"""The two or three sentences on a page that say what to aim for.

Design: [[decisions.0012-quote-the-plans-rather-than-write-them]]

The author approved one guide — FreeChessTrainer's Pirc page — and quoted two
sentences from it as the register the rest should match:

> *"Black allows White to occupy the center with pawns on e4 and d4, aiming to
> undermine it later with well timed pawn breaks and piece pressure."*

**Those are the page's own words, verbatim.** That was checked before this module
was designed, and it decides what this module is: a **selector**, never a writer.
The system has no business paraphrasing a chess page and presenting the result as
knowledge (R-03) — but choosing which of a page's sentences answer *"what should
I aim for?"* is a text-processing question, and this project may answer those.

So every sentence here is quoted, attributed and bounded. The selection rules are
the author's own three objections to the Wikibooks prose, inverted:

  it must be **forward-looking** — objection 1 was that the prose explained what
    had happened rather than what to aim for;
  it must **assume no vocabulary** — objection 3, and the reason a sentence
    containing "Carlsbad" or "prophylaxis" is dropped however good it is;
  it must be **a plain sentence of ordinary length** — objection 2.

And two rules that are not the author's, from reading what the screen actually
returned: marketing uses the same forward-looking grammar as instruction (a page
scoring 8.7 on plan language was partly saying *"I recommend you to check The
Chueca Method"*), and a heading glued to the sentence after it is an artefact of
stripping tags rather than something the page said.

**The caps are a licence boundary, not a style choice.** Three sentences beside a
prominent link is quotation; a page's worth of extracted prose is a copy, which
is what `opening_guides` exists to avoid.
"""

from __future__ import annotations

import html
import re

# At most this many sentences from any one page, and at most this many words in
# total. Quotation stays quotation by being small next to the link it credits.
MAX_QUOTES = 3
MAX_TOTAL_WORDS = 90

# A sentence shorter than this is a fragment or a heading; longer than this is a
# paragraph the tag-stripper failed to break, and unreadable at 1500 either way.
MIN_WORDS = 8
MAX_WORDS = 40

# Objection 1 inverted: language about what to do next, not what happened.
PLAN = re.compile(
    r"\b(you should|you can|your plan|the plan is|the idea is|aims? to|"
    r"aiming (?:for|to)|looks? to|tr(?:y|ies) to|break with|pawn break|"
    r"typical plan|main plan|middlegame plan|put your|develop your|castle)\b",
    re.I,
)

# Objection 3: named concepts used as if the reader already has them. From the
# author's complaint about the Caro-Kann entry, plus the vocabulary that recurs
# in the same register. A sentence containing one of these is dropped whatever
# else it does, because it is exactly the failure that was rejected.
#
# `maroczy` and `hedgehog` were added after a real run: the Exeter Chess Club
# essay produced *"allowing White the Maroczy bind while retaining a flexible
# position"*, which is objection 3 word for word.
JARGON = re.compile(
    r"\b(carlsbad|isolani|IQP|isolated queen'?s pawn|prophyla\w+|zugzwang|"
    r"zwischenzug|luft|minority attack|hypermodern|tabiya|transpos\w+|"
    r"compensation|initiative|tempo|outpost|fianchett\w+|maroczy|hedgehog|"
    r"overprotect\w*|opposite[- ]colou?red)\b",
    re.I,
)

# Marketing wears instruction's grammar. Found by reading, not by predicting.
# `courses?` is plural because `course` alone let through *"you can already
# choose from a number of good courses and books on this system."*
SELL = re.compile(
    r"\b(free trial|sign up|subscribe|enroll|buy now|add to cart|\$\d|courses?|"
    r"premium|membership|recommend you|we offer|click|newsletter|"
    r"lesson plan|coach|discover|your chess to)\b",
    re.I,
)

# A page speaking as itself is selling or editorialising, not teaching a plan.
# Case-insensitive, or a forum comment written in lower case walks past it:
# "Oh me i also play it against d4 and c4" reached the Compiler as a note.
FIRST_PERSON = re.compile(r"\b(i|we|us|our|my)\b", re.I)

# Sentences about *studying* the opening rather than *playing* it. Real output:
# "If you feel comfortable with the positions in the game then you can continue
# with the further study of the French Defense" -- true, and not a plan.
META = re.compile(
    r"\b(further study|studying|study of|learn more|this article|this guide|"
    r"in this post|read on|you will learn|we will look)\b",
    re.I,
)

# A plan names something on the board. This is the rule that removes the
# generic encouragement marketing and instruction share -- "You can one day play
# a long positional game and the next surprise your opponent" passes every other
# test here and tells a player nothing.
BOARD = re.compile(
    r"\b(white|black|pawns?|knights?|bishops?|rooks?|queens?|king|"
    r"cent(?:er|re)|kingside|queenside|flank|file|rank|diagonal|square|"
    r"[a-h][1-8])\b",
    re.I,
)

# Numbers about how OFTEN something happens, rather than about what to do. A
# database page is full of true sentences a player cannot act on -- "At 1200 Elo,
# the top reply is d4, played 33.4% of the time", "Across 50.8 million Lichess
# games, White wins 50.2%" -- and they survived every content rule because they
# name squares and sides.
STATISTIC = re.compile(
    r"\d+(?:\.\d+)?\s*%"
    r"|\(\s*\d[\d\s.,]*\w*\s*\)"
    r"|\b(?:elo|ratings?|win rate|winrate|million|database|statistics)\b",
    re.I,
)

# Navigation the tag stripper flattens into prose: a breadcrumb trail
# ("Home / Articles / Openings / Czech Pirc") and menu items, which on chess
# sites carry an emoji and no full stop.
NAVIGATION = re.compile(
    r"\s[/|>\u203a\u00bb]\s"
    r"|[\U0001F300-\U0001FAFF\u2600-\u27BF\u2190-\u21FF]"
)

# A tag list or a byline, which the tag stripper turns into one long "sentence":
# "Tags: Complete Guide , flexible hypermodern opening , FM Zaur Tekeyev".
_TAG_LIST = re.compile(r"(\s,\s.*){2,}")

# An annotated variation is not a sentence. "(this is the key) exf6 5.Nc3 Bg7
# 6.g3 O-O 7.Bg2" survived every content rule because it is grammatical.
# The ellipsis marking a Black move is written three ways -- "...", "…", and the
# bare full stop. Matching only the ASCII form let "If Black plays 4…Nf6" through.
_MOVE_NUMBER = re.compile(r"\b\d{1,3}(?:\.{1,3}|…|\.…)\s?[KQRBNa-hO]")
_SAN = re.compile(r"^(?:[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?|O-O(?:-O)?)[+#!?]*$")
# Raised from 3 after a real disagreement: "White develops the dark-squared
# bishop to f4 before blocking it with e3, then builds a solid pawn chain with c3
# and e3" names four squares and is plain prose. The numbered-move check below is
# the strong signal for an annotated variation; this one is the backstop.
MAX_MOVE_TOKENS = 5

# Splitting on ". " cuts "e.g." in half and yields "either side can try an early
# break with the d-Pawn (e.g." -- a real quote from a real run.
#
# Each lookbehind must span the abbreviation's OWN full stop too. Written without
# it, the engine looks back at ".g." rather than "e.g." and the split goes
# through anyway, which is the bug this comment exists to stop coming back.
_ABBREVIATIONS = (r"(?<!e\.g\.)(?<!i\.e\.)(?<!\betc\.)(?<!\bvs\.)"
                  r"(?<!\bcf\.)(?<!\bNo\.)(?<!\bfig\.)")

# A sentence that ENDS in an abbreviation was cut, not finished.
_TRAILING_ABBREVIATION = re.compile(r"\b(e\.g|i\.e|cf|vs|fig|no)\.$", re.I)

_DROP = re.compile(
    r"(?is)<(script|style|nav|footer|header|form|aside|noscript)[^>]*>.*?</\1\s*>"
)
# A block ends a sentence even when it carries no full stop. Without this, a
# heading is glued to the paragraph beneath it and the quote reads
# "Black's goals Black aims to stay flexible" -- which is the page's fault only
# in the sense that HTML is not prose.
_BLOCK_END = re.compile(
    r"(?is)</(p|h[1-6]|li|div|section|article|td|tr|th|blockquote|figcaption)\s*>"
    r"|<br\s*/?>"
)
_TAG = re.compile(r"(?s)<[^>]+>")
_SENTENCE_SPLIT = re.compile(_ABBREVIATIONS + r"(?<=[.!?])\s+")


def text_blocks(body: str) -> list[str]:
    """Readable text from HTML, one entry per block-level element.

    Block boundaries are kept because they are sentence boundaries: this is the
    difference between quoting a sentence and quoting a heading plus a sentence.
    """
    body = _DROP.sub(" ", body)
    # Collapse the source's own line breaks **first**. HTML wraps a paragraph
    # across lines for the editor's benefit, and treating those as boundaries
    # would cut sentences in half -- so the only newlines left are the ones this
    # function puts in deliberately.
    body = re.sub(r"\s+", " ", body)
    body = _BLOCK_END.sub("\n", body)
    body = _TAG.sub(" ", body)
    blocks = []
    for block in body.split("\n"):
        collapsed = re.sub(r"\s+", " ", html.unescape(block)).strip()
        if collapsed:
            blocks.append(collapsed)
    return blocks


def is_analysis_line(sentence: str) -> bool:
    """Is this an annotated variation rather than prose?

    A numbered move anywhere is decisive; loose SAN needs a few, because a good
    plan sentence legitimately names two or three squares.
    """
    if _MOVE_NUMBER.search(sentence):
        return True
    moves = sum(1 for token in sentence.split() if _SAN.match(token.strip("(),.;:")))
    return moves > MAX_MOVE_TOKENS


def is_admissible(sentence: str) -> bool:
    """Could this sentence be shown to a 1500 at all?

    Everything `is_plan_sentence` checks **except** whether it is forward-looking.
    Split out because the two halves behave differently when a model does the
    judging: measured against the regexes, a model finds real plan sentences the
    `PLAN` pattern misses, and also admits marketing, trivia and annotated
    variations that these rules correctly refuse
    ([[experiments.e51-llm-selection-and-search]]).

    So this is the half that stays a veto over a model's choice, and `PLAN` is
    the half a model replaces.
    """
    words = len(sentence.split())
    if words < MIN_WORDS or words > MAX_WORDS:
        return False
    # A sentence that lost its full stop was cut by the splitter or by the page
    # itself, and half a sentence is not quotable.
    if not sentence.endswith((".", "!")):
        return False
    # Two shapes of fragment the length check cannot see: a sentence stopping at
    # an abbreviation, and one carrying an unclosed bracket because the rest of
    # it is on the other side of the cut.
    if _TRAILING_ABBREVIATION.search(sentence):
        return False
    if sentence.count("(") != sentence.count(")"):
        return False
    if JARGON.search(sentence) or SELL.search(sentence) or META.search(sentence):
        return False
    if FIRST_PERSON.search(sentence):
        return False
    if is_analysis_line(sentence):
        return False
    return bool(BOARD.search(sentence))


def is_plan_sentence(sentence: str) -> bool:
    """Does this sentence tell a 1500 what to aim for, in words they have?"""
    return is_admissible(sentence) and bool(PLAN.search(sentence))


def plan_quotes(body: str, limit: int = 2) -> tuple[str, ...]:
    """Up to `limit` sentences from this page saying what to aim for.

    Document order is kept rather than ranking by score. A page introduces the
    opening before it discusses a sideline, so its own order is already the
    order a reader wants — and ranking would make the output unstable under
    small edits to the page for no gain a reader would notice.
    """
    limit = min(limit, MAX_QUOTES)
    chosen: list[str] = []
    used_words = 0
    for block in text_blocks(body):
        for sentence in _SENTENCE_SPLIT.split(block):
            sentence = sentence.strip()
            if not is_plan_sentence(sentence):
                continue
            words = len(sentence.split())
            if used_words + words > MAX_TOTAL_WORDS:
                return tuple(chosen)
            chosen.append(sentence)
            used_words += words
            if len(chosen) >= limit:
                return tuple(chosen)
    return tuple(chosen)


def is_usable_note(sentence: str) -> bool:
    """Is this sentence worth passing to the Compiler as raw material?

    **Relevance and information, never readability.** The author's correction:
    *"It keeps sentences a 1500 can use, this doesn't has to be disregarded,
    compiler will be the one that writes something understandable, more
    information is better than just disregarding it."*

    So a sentence naming the Maroczy bind is kept here and explained later, where
    `is_plan_sentence` would have dropped it. What is still refused is material
    the Compiler cannot use at all: advertising, advice about studying, annotated
    variations, and sentences that name nothing on the board.
    """
    words = len(sentence.split())
    if words < MIN_WORDS or words > MAX_WORDS:
        return False
    if sentence.endswith("?"):
        return False
    if SELL.search(sentence) or META.search(sentence):
        return False
    if FIRST_PERSON.search(sentence):
        return False
    if STATISTIC.search(sentence) or _TAG_LIST.search(sentence):
        return False
    if NAVIGATION.search(sentence):
        return False
    if is_analysis_line(sentence):
        return False
    return bool(BOARD.search(sentence))


# Something a player can locate on the board. Wider than a square, because a
# point can be concrete without naming one: the author's example, *"White should
# take the d file but still keep track of Black's attacks on the king with the
# light squared bishop and a queen"*, names a file and a specific bishop and is
# perfectly actionable.
#
# What it must exclude is the generic noun. "Pieces", "the center" and "pawn
# structure" are what "develop pieces in harmony and prepare for counterplay" is
# made of, and that point tells a player nothing.
CONCRETE = re.compile(
    r"\b[a-h][1-8]\b"                                  # a square
    r"|\b[a-h][1-8]\s?[-\u2013]\s?[a-h][1-8]\b"        # a diagonal, e1-h4
    r"|\b[a-h][\s-]?(?:file|pawn)\b"                   # the d file, the f-pawn
    r"|\b(?:light|dark)[\s-]?squared? \w*bishop\b"     # the light-squared bishop
    r"|\b(?:queen|king)'?s?[\s-](?:knight|bishop|rook|side pawns?)\b"
    r"|\b(?:long|open|half[\s-]open) (?:diagonal|file)\b"
    r"|\b(?:back rank|seventh rank|eighth rank)\b"
    r"|\b[KQRBN][a-h][1-8]\b|\bO-O(?:-O)?\b",          # a move
    re.I,
)


def names_a_target(text: str) -> bool:
    """Does this point name something a player can find on the board?"""
    return bool(CONCRETE.search(text))
