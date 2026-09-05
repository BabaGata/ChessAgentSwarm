"""Scout → Assessor → Compiler, pointed at a detected claim instead of an opening.

Design: docs/notes/design.knowledge-base.md (Option C)

The author chose the swarm to draft the knowledge base and asked that LLM agents
be used as far as they go. This reuses the three agents rather than growing a
fourth: **the `Assessor` is used unchanged** — its prompt takes a topic string,
and a claim name is as good a topic as an opening name — and only the queries
and the final assembly are new.

**The strongest guarantee here is that the definition is not written by a
model.** It is a sentence from the retrieved page, chosen **by index**, exactly
the trick that keeps the Assessor's kept notes verbatim. The model chooses
*which* sentence defines the thing; it never composes the sentence. So the one
field the detector review will be compared against is the source's own words.

What the model does write — `why` and `practice` — is grounded against the kept
notes and dropped when it is not, and `practice` is dropped entirely when
nothing supports it. [[capacity.knowledge]] records that the expertise research
found training-method evidence thin and coaching's value contested, so inventing
practice advice would contradict the project's own knowledge base and produce
exactly the unfalsifiable coaching CLAUDE.md forbids.

**`not_this` is never written here.** The web's definition of a fork is *"one
piece attacks two pieces at once"*, which is precisely what the broken detector
implemented. That field is the author's.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import re

from chesscoach import ollama
from chesscoach.books import BookLibrary, is_book
from chesscoach.grounding import check
from chesscoach.knowledge import Entry, Source
from chesscoach.opening_agent import Gap, SearchUnavailable
from chesscoach.opening_swarm import (
    MODEL,
    Assessor,
    Candidate,
    _detailed,
    _restates,
    _today,
)
from chesscoach.skiplist import domain_of, SkipList

# The words chess writers actually use for the things we detect.
#
# **Discovered, not asserted** (experiments.e65-real-phrases). E64 found that
# nine of fourteen claim keys are this project's own jargon -- Capablanca has a
# chapter on castling and nobody has written a definition of "late castling",
# because it is not a term. So each claim carries several real phrases, and every
# one was checked against two independent sources.
#
# 1.4 MB of Capablanca, Edward Lasker and Staunton corrected four guesses that
# would have searched for nothing:
#
#     "outpost"            0 uses  ->  "hole"             50 uses
#     "trapped"            0       ->  "hemmed in"         5
#     "discovered attack"  0       ->  "discovered check"  8
#     "undefended piece"   0       ->  "en prise"          8
#
# And the web supplied the modern vocabulary those books cannot have, scored by
# how many returned titles actually name chess:
#
#     "fork chess tactic"       51 results, 43 naming chess
#     "skewer chess tactic"     44/37        "x-ray attack"   30/28
#     "deflection chess tactic" 41/32   <- capturingDefender, for which the
#                                          classical literature has NO word
#     "outpost chess"           21/21   <- modern, absent from the books
#
# Two candidates were refused on the evidence rather than on taste:
# "undermining chess tactic" (12 results, 2 naming chess) and "hole chess
# position" (20/6) -- "hole" is the books' word and the web's word for something
# else, so it stays a book term and never becomes a query.
#
# First phrase is what a search asks; the rest widen the net and feed the terms
# used to search the shelf.
TERMS: dict[str, tuple[str, ...]] = {
    # --- tactics: the web knows these, the classical books mostly do not -----
    "fork": ("fork chess tactic", "double attack", "forking piece"),
    "pin": ("pin chess tactic", "pinned piece", "absolute pin"),
    "skewer": ("skewer chess tactic", "x-ray attack"),
    "discoveredAttack": ("discovered attack chess", "discovered check"),
    "capturingDefender": ("deflection chess tactic", "removing the defender",
                          "removing the guard"),
    "hangingPiece": ("hanging piece chess", "en prise", "undefended piece"),
    # **Singular, and never "hanging pawns".** Two senses of the word exist and
    # only one is this claim. The *plural* is Steinitz's structural term -- two
    # adjacent pawns on central half-open files -- and searching it returns
    # structure material, which is why this entry once held a passage about a
    # bishop's advantage. The sense meant here is the tactical one Lichess uses
    # for `hangingPiece`: *"undefended or insufficiently defended and free to
    # capture"*. `isolated pawn` and `backward pawn` were also listed and are
    # `concedes_weakness` subjects, so all three phrases named something else.
    "hangingPawn": ("undefended pawn chess", "hanging pawn chess", "en prise pawn",
                    "unprotected pawn"),
    "trappedPiece": ("trapped piece chess", "hemmed in", "shut in"),
    "backRankMate": ("back rank mate chess", "back rank weakness"),

    # --- the opening: the books are strong here ------------------------------
    "late_castling": ("castling in chess", "castle early opening", "king safety",
                      "safety of the king"),
    "slow_development": ("development of the pieces chess", "develop the pieces",
                         "loss of time", "gain of time"),
    "repeat_move": ("moving the same piece twice chess", "same piece twice",
                    "loss of time", "waste of time"),
    "pawn_error": ("pawn moves in the opening chess", "premature advance",
                   "pawn advance"),

    # --- position and phase --------------------------------------------------
    "allows_square": ("outpost chess", "weak square chess", "hole"),
    "allows_pressure": ("attack on the king chess", "king side attack",
                        "assault on the king"),
    "concedes_weakness": ("weak pawn chess", "isolated pawn", "doubled pawns"),
    "endgame_error": ("endgame technique chess", "opposition", "king activity"),
    "moved_into_attack": ("en prise chess", "unprotected piece", "attacked piece"),
    "long_think_error": ("time management chess", "time trouble", "time limit"),
}

# The single phrase a search asks, so nothing downstream changed shape.
TOPICS = {key: phrases[0] for key, phrases in TERMS.items()}


def terms_for(key: str) -> tuple[str, ...]:
    """Every phrase worth searching for this claim, best first."""
    return TERMS.get(key) or (key.replace("_", " ") + " in chess",)

# The Assessor picks sentences by the hundred and `qwen2.5:3b` does it well
# enough. The Compiler makes ONE judgement that decides the entry -- is this
# sentence a definition, or an example of the thing? -- and measured on the same
# eight notes, the 3b model picked the example while both larger models picked
# the definition:
#
#     qwen2.5:3b       "The Knight forks the King and Rook, forcing..."   example
#     qwen3:8b         "An absolute fork is when a piece attacks two..."  definition
#     phi4-mini:3.8b   "An absolute fork is when a piece attacks two..."  definition
#
# Two attempts at fixing this in the prompt failed first: told to pick the best
# sentence it returned a plausible wrong one, and told that refusing was usually
# right it refused a page that did contain a definition. The distinction is a
# capability, not a wording.
# phi4-mini rather than qwen3:8b, after both got the discriminating test right:
# qwen3 is a THINKING model, so its reasoning eats the token budget before any
# JSON appears -- asked to reply "ok" in 10 tokens it returned an empty string --
# and it was the model loaded when Ollama answered HTTP 500 twice on longer
# prompts. phi4-mini is smaller, not a reasoning model, and its answers are
# roughly half the length for the same verdict.
JUDGE_MODEL = "phi4-mini:3.8b"

# --- choosing the notes a definition is picked from -------------------------
#
# The opening Assessor is the wrong instrument here, and measurably so. Its veto
# `is_usable_note` ends with `return bool(BOARD.search(sentence))` -- a sentence
# must name something locatable on the board -- and `BOARD` matches specific
# pieces, squares, files and ranks but **not the generic word "piece"**. Every
# definition tested was rejected before any model saw it:
#
#     "A fork is a move that attacks two or more enemy pieces..."   rejected
#     "A hanging piece is one that is undefended..."                rejected
#     "Practice recognising forks by studying tactics puzzles."     rejected (META)
#
# The judge was choosing from the survivors -- plan-shaped sentences naming
# squares -- which is why it kept returning examples. Those were not bad
# choices; they were the only ones left. Reusing the Assessor unchanged, which
# this module presented as a virtue, was the bug.

# Algebraic squares and move notation. A sentence carrying these is about ONE
# position, and a definition is about all of them.
_SPECIFIC = re.compile(
    # Standard algebraic notation: an optional piece letter, optional
    # disambiguation by file and/or rank, an optional capture marker, then the
    # destination square. Written three times before it was tested:
    #
    #   v1  `[a-h]x?`   put the capture after the FILE, missing `Nxf3+`
    #   v2  no trailing guard, so `b12` and `e40` matched `b1` and `e4`
    #
    # Case matters and is not a mistake: SAN squares are lower case and piece
    # letters upper, so `H1` is a heading and `h1` is a square.
    r"\b[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](?![0-9])(?:=[QRBN])?[+#]?"
    # Castling, spelled with letters or with zeros -- both are common in print.
    r"|\b[O0]-[O0](?:-[O0])?\b"
    # A result belongs to one game, so it is specific by the same rule.
    r"|\b[01\u00bd]-[01\u00bd]\b"
    # Numbered moves: "12. Nf3", "5...c5", "1.e4".
    r"|\b\d+\.{1,3}\s*[KQRBNa-h]"
    # DESCRIPTIVE notation, which is what the public-domain books use: "P-K4",
    # "Kt-KB3", "QR-Q1", "B x Kt", and the spaced forms Capablanca's typesetter
    # preferred, "Kt - K B 3". Added when the books came in: the algebraic
    # pattern caught none of it, so "Kt - Q B 3 This developing move at the same
    # time defends the King's Pawn" read as a general statement about
    # development when it is a note on one move of one game.
    r"|\b(?:Kt|[KQRBNP])\s*[-x]\s*(?:Kt|[KQRBNP1-8])"
    # A bare descriptive square: "K 4", "Q B 3", "KB3", "K R 1".
    r"|\b[KQ]\s?[KQRBN]?\s?[RBNP]?\s?[1-8]\b"
)



# --- what a definition is not ------------------------------------------------
#
# `_SPECIFIC` removes sentences about one position. These remove sentences about
# one MOMENT: running commentary, which names no square and so passes the first
# filter untouched. The sentence that forced this was drafted as the definition
# of a hanging pawn:
#
#     "Indeed, there is an avalanche of pawns hanging over Black's head!"
#
# Verbatim from a real chess page, about pawns, naming no square -- and useless,
# because it describes a moment in one game rather than saying what the thing
# is. **A definition stands on its own.** Each filter below is a way a sentence
# announces that it does not.

# A sentence that opens by connecting to the previous one is not self-contained:
# whatever it says depends on what came before. "Because" and "When" are absent
# on purpose -- they subordinate within the sentence rather than reaching back.
_CONNECTIVE = re.compile(
    # `there` only in its connective sense. "There, White plays..." points at a
    # previous sentence; "There are two kinds of pin" is an existential and one
    # of the commonest ways a definition opens. Refusing both cost the pin
    # entry a real definition (E89).
    r"^\s*(indeed|however|but|so|then|now|here|"
    r"there(?!\s+(is|are|was|were|exists?|remains?|follows?)\b)|instead|thus|therefore|"
    r"also|moreover|yet|still|meanwhile|finally|next|again|furthermore|"
    r"nevertheless|nonetheless|besides|otherwise|conversely|likewise|"
    r"in fact|of course|for example|for instance|as such|at right|at left|"
    r"in this case|in the diagram|as we|as you)\b",
    re.I,
)

# A sentence opening with a demonstrative points at something outside itself.
_ANAPHORA = re.compile(r"^\s*(this|that|these|those|it|they|he|she|his|her)\b", re.I)

# A demonstrative can be the main clause's subject without opening the sentence:
# "As any general knows, this is a recipe for disaster." The opening clause is
# decoration and "this" still points outside.
_ANAPHORA_MID = re.compile(
    r",\s*(this|that|these|those|it)\s+(?:is|are|was|were)\b", re.I
)

# Chess writing says "White" and "Black". A sentence narrating what "he" did is
# telling the story of one game.
_NARRATOR = re.compile(r"\b(he|she|him|her|his|hers)\b")

# Deixis: the writer pointing at a board the reader is looking at.
_DEIXIS = re.compile(
    r"\b(the position|the diagram|the game|this position|this game|shown above|"
    r"shown below|see above|see below|at right|at left|in the picture)\b",
    re.I,
)


def reads_as_commentary(sentence: str) -> str:
    """Why this sentence is about a moment rather than about the thing, or "".

    Returned as a reason rather than a boolean so a run can report what it threw
    away -- the author asked what the Assessor discards, and "some sentences"
    is not an answer.
    """
    if sentence.rstrip().endswith("!"):
        return "exclamation: commentary, not definition"
    if _CONNECTIVE.match(sentence):
        return f"opens by connecting to the previous sentence: {_CONNECTIVE.match(sentence).group(1)!r}"
    if _ANAPHORA.match(sentence):
        return f"opens with a reference to something outside it: {_ANAPHORA.match(sentence).group(1)!r}"
    if _ANAPHORA_MID.search(sentence):
        return (f"its main clause points outside itself: "
                f"{_ANAPHORA_MID.search(sentence).group(1)!r}")
    if _NARRATOR.search(sentence):
        return "narrates a player as 'he' or 'she' rather than White or Black"
    if _DEIXIS.search(sentence):
        return f"points at a particular board: {_DEIXIS.search(sentence).group(1)!r}"
    return ""


SELECTORS = ("assessor", "definition", "none")


# Page scripts that survived text extraction. Re-drafting `late_castling`
# produced *"Castling is permitted provided all of the following conditions are
# met: "}},"i":0}}]}'>"* -- embedded JSON with a prose prefix, which passed every
# other filter and would have been offered to the author as a definition.
#
# Braces and angle brackets do not occur in chess prose, so this is a cheap test
# for a failure that is otherwise invisible until someone reads the output.
_MARKUP = re.compile(r"[{}<>\\]|\]\}|\}\]")


def is_broad(sentence: str) -> bool:
    """Is this a general statement rather than a comment on one position?

    **The inverse of the opening veto**, which is the author's own framing:
    *"remove specifics and keep the broad definitions"*. Where `is_usable_note`
    REQUIRES something locatable on the board, this REFUSES it -- a sentence
    naming b5 or Nxf3+ is about one game, and a definition is about all of them.

    Everything else the opening veto refuses is still refused, except two:
    `META` (study advice), because the `practice` field is made of exactly that,
    and `FIRST_PERSON`, because *"we call this a fork"* is a normal way to write
    a definition.
    """
    from chesscoach.opening_plans import (
        MAX_WORDS,
        MIN_WORDS,
        NAVIGATION,
        SELL,
        STATISTIC,
        is_analysis_line,
    )

    words = len(sentence.split())
    if words < MIN_WORDS or words > MAX_WORDS:
        return False
    if sentence.endswith("?"):
        return False
    if SELL.search(sentence) or STATISTIC.search(sentence):
        return False
    if NAVIGATION.search(sentence) or is_analysis_line(sentence):
        return False
    if _MARKUP.search(sentence):
        return False
    if reads_as_commentary(sentence):
        return False
    return not _SPECIFIC.search(sentence)


DEFINITION_ASSESSOR = """You are the ASSESSOR in a chess coaching system.

You read one web page and pick the sentences that say WHAT {topic} IS.

A sentence that defines it would still make sense to someone who had never
heard the term. Prefer:
- a sentence of the form "X is ..." or "X refers to ..." or "X happens when ..."
- a sentence saying what makes it good or bad, in general
- a sentence saying how a player practises or recognises it

Do NOT pick:
- a comment on one particular position or game
- a sentence that only makes sense if you already know the term

Sentences from a page about {topic}:
{sentences}

Pick the {limit} that best say what {topic} is, best first.
Answer with the numbers in the "keep" field. If none of them says what {topic}
is, keep nothing."""

COMPILER_SCHEMA = ollama.schema_of(
    definition={"type": "integer"},
    why={"type": "string"},
    practice=ollama.array_of("string"),
)

COMPILER = """You are the COMPILER in a chess coaching system.

You are writing one encyclopedia entry about: {topic}

These numbered sentences were taken from real chess pages. They are the ONLY
material you may use. You may not add chess knowledge of your own.

{notes}

Answer as JSON with three fields:

"definition": the NUMBER of the sentence that says what {topic} IS -- a sentence
that would still make sense to someone who had never heard the term. An example
of it happening ("the knight forks the king and rook") is NOT a definition, and
neither is a sentence about a different subject.
Choose a number from the list. Do not write a sentence.
If no sentence defines {topic}, answer -1.

"why": one sentence on what it costs a player who gets this wrong, using only
what the sentences above say. If the sentences do not say, answer "".

"practice": up to {practice} short suggestions for how to practise this, each
supported by the sentences above. If the sentences suggest none, answer with an
empty list. Do not invent training advice."""


# Words that carry no topic. "in chess" is in every query, so a page mentioning
# "chess" is not thereby about forks.
_EMPTY = frozenset({
    # Grammar. `against` is here because "allowing pressure against the king"
    # matched a libertarian-communism essay on both `against` and `king`.
    "in", "the", "a", "an", "of", "on", "to", "and", "for", "with", "against",
    "when", "that", "this", "from", "into", "your", "их",
    # Chess words so common they identify nothing: every query says "in chess",
    # and almost every chess page says "move" and "piece".
    "chess", "move", "moves", "piece", "pieces", "player", "opening", "game",
    "games", "position", "positions",
})


def key_terms(topic: str) -> frozenset[str]:
    """The words a page must actually contain to be about this topic."""
    return frozenset(
        word.strip(".,()").lower() for word in topic.split()
        if word.strip(".,()").lower() not in _EMPTY and len(word) > 2
    )


# A page has to be about chess, not merely share vocabulary with it. Measured on
# the fetched pages: Sensei's Library -- the **Go** wiki, which supplied a
# "definition" of endgame technique -- says "chess" **zero** times, while real
# chess pages say it 35 to 3,310 times.
#
# A flat threshold is not enough. A constructed-language grammar said "chess" 4
# times in 400 KB, and a libertarian-communism essay said it 3 times in 55 KB
# and supplied the sentence *"They cater for the moment, and the moment is
# capitalism."* as a definition of king-side pressure. Both cleared a floor of
# three; neither clears one mention per 5 KB.
CHESS_MENTIONS = 3
CHARS_PER_MENTION = 5_000


def about_chess(candidate: Candidate, body: str) -> bool:
    """Is this page about chess at all?

    Separate from the topic check because the two failures are different. A page
    can be about chess and not about forks (the Assessor's problem), or about
    forks-in-another-sense and not chess at all -- "endgame" and "technique" are
    Go words too, and that is how a Go wiki came to define a chess claim.

    **An address naming chess settles it** -- `chessprogramming.org` and
    `/chess-royal-fork/` are chess pages however short their text, because a
    domain and a path are structural claims about the whole page.

    **A title does not**, and letting it was the fourth leak in this gate: a
    search result titled for chess pointed at a libertarian-communism essay,
    which then supplied *"They cater for the moment, and the moment is
    capitalism"* as a definition of king-side pressure. A title is a line of
    text like any other and is written to attract a click.

    **The URL fragment is stripped first.** The page that made this necessary is
    a grammar of a constructed language whose address ends `#Chess_Piece_` -- a
    fragment names one section, not the page, and taking it as the page's
    subject is how 400 KB about grammar became a source about chess.

    Otherwise it falls back to a rate in the body, not a count: that same page
    said "chess" four times in 400 KB.
    """
    address = candidate.url.split("#", 1)[0].lower()
    if "chess" in address:
        return True
    mentions = body.lower().count("chess")
    needed = max(CHESS_MENTIONS, len(body) // CHARS_PER_MENTION)
    return mentions >= needed


def all_terms(key: str) -> frozenset[str]:
    """Key words from every phrase for a claim, for searching the books.

    The books and the web use different words for the same thing, and a shelf
    search should try both: `allows_square` finds nothing under "outpost" and
    fifty passages under "hole".
    """
    found: set[str] = set()
    for phrase in terms_for(key):
        found |= key_terms(phrase)
    return frozenset(found)


def is_about(topic: str, candidate: Candidate, body: str) -> bool:
    """Is this page about the topic, on a page that is about chess?

    **A mechanical veto, not a model judgement**, in the same idiom as
    `is_usable_note`: it refuses a page rather than ranking it, and it is cheap
    enough to run before any model call is spent.

    It exists because the Assessor picks the most informative sentences *within*
    a page and never asks whether the page is about the thing. Live runs drafted
    a "definition" of *hanging piece* whose sources included the Wikipedia
    article for **Black Is King**, a Beyonce film, one of *hanging pawn* from
    **TCEC Season 18**, and one of *endgame technique* from a **Go** wiki. All
    three mention chess words; none is about the motif.

    Two conditions, because there are two ways to fail:

    - the page must **mention the topic** -- generous, one key term anywhere in
      title, URL or body, since ranking chess pages against each other is the
      Assessor's job and it is better at it than a word count;
    - the page must **be about chess**, which is what the Go wiki fails.
    """
    if not about_chess(candidate, body):
        return False
    terms = key_terms(topic)
    if not terms:
        return True
    haystack = f"{candidate.title} {candidate.url} {body[:20000]}".lower()
    return any(term in haystack for term in terms)


# Chess words general enough to appear in a definition of anything. They are
# useful for FINDING a page and useless for VERIFYING what a sentence is about:
# "attack", from `fork`'s phrase "double attack", matched "a skewer happens when
# a piece ATTACKS a man" and let a skewer through as a fork.
_GENERIC = frozenset({
    "attack", "attacks", "attacked", "attacking", "tactic", "tactics",
    "defend", "defender", "defence", "defense", "square", "squares",
    "capture", "captured", "material", "advantage", "weakness", "weak",
    # Added 2026-09-01: words that appear on nearly every page of a chess book
    # and therefore separate nothing. `key_terms("skewer chess tactic")` kept
    # "chess", which passed all six candidate passages for a term E64 measured
    # as appearing **zero times** on the shelf -- a filter keyed on a word the
    # whole corpus shares is not a filter.
    "chess", "chessboard", "board", "game", "games", "player", "players",
    "piece", "pieces", "move", "moves", "moved", "position", "positions",
    "play", "playing", "played", "white", "black",
    # Board furniture, as generic as "square" beside it. `backRankMate` was
    # corroborated by two passages that share only the word "rank" -- one about
    # piece values, one about the opening setup -- and every chess book talks
    # about ranks and files on almost every page.
    "rank", "ranks", "file", "files",
})


# What each concept is CALLED, as opposed to what finds a page about it.
#
# `TERMS` mixes the two and that mixture is what let five wrong entries through.
# "castle" and "king safety" sit in the same tuple for `late_castling`: the first
# names the concept, the second names a neighbourhood, and a gate keyed on the
# union accepts the rule about moving into check because it says "king".
#
# These are synonyms and spellings, not chess claims, so nothing here needs a
# source (R-03). Matched as substrings, so "castl" would be a stemmer and
# "castle"/"castling" listed separately is not one.
NAMES: dict[str, tuple[str, ...]] = {
    "fork": ("fork", "forking", "double attack"),
    "pin": ("pin", "pinned", "pinning"),
    "skewer": ("skewer", "skewered", "skewering"),
    "discoveredAttack": ("discovered attack", "discovered check", "discovery"),
    "capturingDefender": ("deflection", "removing the defender", "removing the guard",
                          "capturing the defender", "capturing defender"),
    # "hanging piece" rather than bare "hanging", so that a hanging *pawn* does
    # not read as a hanging piece -- they are separate claims here.
    "hangingPiece": ("hanging piece", "en prise", "undefended piece", "unprotected piece"),
    "hangingPawn": ("hanging pawn", "undefended pawn", "unprotected pawn"),
    "trappedPiece": ("trapped", "hemmed in", "shut in"),
    "backRankMate": ("back rank", "back-rank"),
    "late_castling": ("castling", "castle", "castled"),
    "slow_development": ("development", "develop", "developed", "developing"),
    "repeat_move": ("same piece twice", "lose a move", "lost move", "tempo"),
    "pawn_error": ("pawn advance", "premature advance", "pawn move"),
    "allows_square": ("outpost", "hole", "weak square"),
    "allows_pressure": ("attack on the king", "king-side attack", "assault on the king"),
    "concedes_weakness": ("isolated", "doubled", "backward", "weak pawn"),
    "endgame_error": ("endgame", "end-game", "ending", "opposition"),
    "moved_into_attack": ("en prise", "unprotected", "attacked piece"),
    "long_think_error": ("time trouble", "time management", "long think"),
}


def _own_terms(key: str) -> frozenset[str]:
    """The words that name this concept, as opposed to merely finding it.

    `NAMES` where there is one, since a concept's synonyms are not recoverable
    from its search phrases -- `hangingPiece` is named by "en prise" and
    `late_castling` by "castle", neither of which any splitting of the topic
    phrase produces. Otherwise the topic phrase, minus the generic half.
    """
    named = NAMES.get(key)
    if named:
        return frozenset(named)
    return key_terms(topic_for(key)) - _GENERIC


def _names(sentence: str, key: str) -> bool:
    """Does this sentence define **this** concept, rather than share a word with it?

    Checked against the claim's own vocabulary rather than its key, since the
    key is this project's jargon: `late_castling` is named by "castling" and
    `hangingPiece` by "en prise" as readily as by "hanging".

    **Broad for finding, narrow for verifying** -- and the narrow half is two
    tests, because presence alone was not enough. Of fourteen stored entries,
    five passed on a single ordinary word: a pawn ending stood as the definition
    of an attack on the king because it says "king".

    1. **It must name the concept**, using the topic phrase rather than the
       widened net (`_own_terms`).
    2. **Nothing else may name it better.** A sentence matching some other
       claim's vocabulary *more* than this one's is about that other thing. The
       comparison is on strength rather than presence, because a definition by
       contrast -- "a skewer is the inverse of a pin" -- names its neighbour on
       purpose and is still a definition of the skewer.

    Words the two concepts share are dropped from the rival's count: they
    separate nothing, which is the same reason `_GENERIC` exists.
    """
    low = sentence.lower()
    mine = _own_terms(key) or (all_terms(key) - _GENERIC) or all_terms(key)
    strength = _claim_on(low, mine)
    if strength[0] == 0:
        return False

    for other in TERMS:
        if other == key:
            continue
        if _claim_on(low, _own_terms(other) - mine) > strength:
            return False
    return True


def _claim_on(low: str, terms: frozenset[str]) -> tuple[int, int]:
    """How strongly a sentence is about a vocabulary: how often, then how early.

    **How often**, because a passage saying "pawn" twice and "king" once is about
    pawns -- that is the pawn ending that stood as the definition of an attack on
    the king.

    **Then how early**, because in an English definition the thing being defined
    is the subject: *"A skewer is the inverse of a pin"* defines the skewer, and
    both concepts appear exactly once. Earlier is stored negated so that plain
    tuple comparison prefers it.
    """
    hits = [(low.count(term), low.find(term)) for term in terms if term in low]
    if not hits:
        return (0, 0)
    return (sum(count for count, _ in hits), -min(at for _, at in hits))


def topic_for(key: str) -> str:
    """The single best phrase for a claim key."""
    return terms_for(key)[0]


@dataclass
class KnowledgeScout:
    """Finds pages that explain a claim. Judges nothing, fetches nothing.

    Three fixed queries rather than model-written ones. The opening Scout asks a
    model for queries because opening names are many and their phrasings vary;
    a claim has one name and three obvious questions about it, and a generated
    query here could only be worse than the obvious one.
    """

    searcher: object
    skiplist: SkipList = field(default_factory=SkipList.seeded)
    name: str = "knowledge-scout"

    def __post_init__(self) -> None:
        self.skipped: list[str] = []

    def queries(self, key: str) -> list[str]:
        """The plain phrase first, then the alternatives.

        Several phrasings rather than one, because a claim key is this project's
        jargon and the literature's word is often different: `allows_square` is
        an **outpost** to the web and a **hole** to Staunton, and a single query
        for either misses half the writing about it.

        **The plain phrase is asked, and asked first.** It used to appear only
        wrapped -- "what is a {phrase}" and "why {phrase} matters" -- and never
        on its own, which is what returned nothing usable for three concepts in
        a row. Measured against the local search instance:

            'outpost chess'                  -> wikipedia Outpost_(chess)
            'what is a outpost chess'        -> chessmetrics.com, missiveapp.com
            'undefended pawn chess'          -> wikipedia Chess_tactic
            'what is a undefended pawn chess'-> wikipedia **Turochamp**

        A search engine's own ranking of the exact term is the best signal
        available, and the wrapping threw it away. It also produced
        ungrammatical queries -- *"what is a castling in chess"* -- by prefixing
        an article to a phrase that does not take one.
        """
        phrases = terms_for(key)
        asked = [phrases[0], *phrases[1:3], f"{phrases[0]} explained"]
        return list(dict.fromkeys(asked))

    def find(self, key: str) -> list[Candidate]:
        found: dict[str, Candidate] = {}
        self.skipped = []
        failures = 0
        queries = self.queries(key)
        for query in queries:
            asked = Gap(opening=key, games=0, share=0.0, query_override=query)
            try:
                results = _detailed(self.searcher, asked)
            except SearchUnavailable:
                failures += 1
                continue
            for title, url, publisher, snippet in results:
                if self.skiplist.skips(url):
                    self.skipped.append(publisher)
                    continue
                found.setdefault(url, Candidate(title, url, publisher, snippet))
        # Every query failing is "we could not ask", which must not be returned
        # as "nothing was found" -- L-046, six instances in this project.
        if failures == len(queries) and not found:
            raise SearchUnavailable(f"every query for {key!r} failed")

        # A domain that has produced usable text before is read first. The
        # search instance returns a different ordering on each call -- asked
        # twice for `late_castling` within a minute it offered the Castling
        # article once and a list of 1904 tournaments the next time -- and only
        # `read_web` pages are read, so a bad draw loses the concept.
        #
        # `mark_useful` is already called on every page that helps, so this
        # spends evidence the run collects anyway. Stable, and it invents no
        # preference where there is no history: without a match the engine's own
        # ranking is the only signal left, and it is kept.
        # `is not None`, not truthiness: `SkipList.__len__` counts entries, so a
        # list that skips nothing is falsy while still knowing which domains
        # have helped. Asking the object whether it exists by asking whether it
        # is empty is how the useful set went missing here.
        useful = self.skiplist.useful if self.skiplist is not None else frozenset()
        return sorted(found.values(), key=lambda c: domain_of(c.url) not in useful)


@dataclass
class KnowledgeCompiler:
    """Assembles one entry. Chooses a definition, writes at most two fields."""

    model: str = JUDGE_MODEL
    host: str = ollama.OLLAMA_URL
    practice: int = 2
    # Notes offered to the judge. Four pages at six sentences each is 24, and a
    # first batch met an HTTP 500 from Ollama on a long prompt. A definition, if
    # the pages contain one, is not in the twentieth sentence -- and a cap keeps
    # the one call that decides each entry inside a size that is known to work.
    limit: int = 16
    transport: object | None = None
    name: str = "knowledge-compiler"

    def compile(self, key: str, notes: tuple[str, ...],
                sources: tuple[Source, ...]) -> Entry:
        if not notes:
            # Nothing kept means nothing to say. Asking anyway is asking the
            # model what it believes about forks, which is the whole thing R-03
            # forbids.
            return Entry(key=key, drafted_by=self.model, checked_on=_today())

        topic = topic_for(key)
        notes = notes[: self.limit]
        numbered = "\n".join(f"{i}. {n}" for i, n in enumerate(notes))
        answer = ollama.generate(
            self.model,
            COMPILER.format(topic=topic, notes=numbered, practice=self.practice),
            host=self.host, num_predict=260, schema=COMPILER_SCHEMA,
            transport=self.transport,
        )
        data = ollama.as_json(answer)

        quote = self._quote(data, notes)
        # **A definition of the wrong thing is not a definition.** A page about
        # chess tactics defines several of them, and asked for `fork` the judge
        # returned "a skewer happens when a chess piece attacks an opponent's
        # chessman, which hides a less important piece behind it" -- a correct
        # definition, verbatim, of a different tactic. The page was relevant and
        # the sentence was a definition; only the subject was wrong, which no
        # filter upstream of here can see.
        if quote and not _names(quote, key):
            quote = ""
        source_text = " ".join(notes)
        why = self._grounded(str((data or {}).get("why", "")).strip(), source_text)
        practice = tuple(
            p for p in ollama.strings(data, "practice")[: self.practice]
            if self._grounded(p, source_text) and not _restates(p, [why] if why else [])
        )

        return Entry(
            key=key,
            # The retrieved sentence IS the definition. A model-written
            # paraphrase is where the precision goes, and precision is the one
            # thing the detector review needs from this field.
            definition=quote,
            quote=quote,
            sources=sources,
            why=why,
            practice=practice,
            drafted_by=self.model,
            checked_on=_today(),
        )

    @staticmethod
    def _quote(data: dict | None, notes: tuple[str, ...]) -> str:
        """The chosen sentence, verbatim, or nothing.

By index, so the definition is the page's own words by construction and
        cannot be something the model composed. Two answers are refused rather
        than repaired, on `ollama.ints`'s contract: an index **outside the list**
        is a hallucination rather than a near miss, and **prose in an integer
        field** is the model ignoring the one instruction that matters here.
        Clamping either would silently pick a sentence nobody chose.

        **-1 means no sentence defines the topic**, and getting the instruction
        for it right took two attempts. Told merely to pick the best sentence,
        the model returned a plausible wrong one; told that refusing was *usually*
        right, it refused a page containing *"an absolute fork is when a piece
        attacks two or more enemy pieces simultaneously, one of them being the
        King"*. **A refusal option needs a criterion, not a bias** -- the prompt
        now says what a definition is (a sentence that would make sense to
        someone who had never heard the term) rather than how often to expect
        one.

        The first live run drafted a "definition" of castling that read
        *"There are two possible moves that place a pawn in the centre of the
        board"* -- a real sentence, verbatim from a real page, about something
        else entirely. Choosing by index guarantees provenance; it cannot
        guarantee relevance, and without a way to say "none of these" the model
        must return the least-bad sentence. A plausible wrong answer where
        "nothing found" was the truth is L-046 with the failure moved from the
        pipeline into the content.
        """
        if not data:
            return ""
        chosen = data.get("definition")
        if isinstance(chosen, bool) or not isinstance(chosen, int):
            return ""
        return notes[chosen] if 0 <= chosen < len(notes) else ""

    @staticmethod
    def _grounded(text: str, source: str) -> str:
        """Model prose, or nothing if the notes do not support it."""
        if not text:
            return ""
        return text if check(text, source).grounded else ""


@dataclass
class KnowledgeSwarm:
    """Scout → Assessor (per page) → Compiler, for one detected claim."""

    searcher: object
    fetch: object
    skiplist: SkipList = field(default_factory=SkipList.seeded)
    # Public-domain chess books, read before the web. A book by a world
    # champion is about chess by construction, so it needs none of the
    # machinery built to keep out a Beyonce film -- and it is strong in
    # exactly the places the web returned nothing: castling, development,
    # pins.
    library: BookLibrary = field(default_factory=BookLibrary.load)
    model: str = MODEL
    judge: str = JUDGE_MODEL
    # Read budget, SPLIT rather than shared. Prepending books to one list of
    # four meant the web was never reached: across fourteen redrafted entries
    # the sources were 34 books and **zero** pages, and `fork` lost a real
    # definition from chessmood to a Lasker game annotation.
    #
    # The two sources fail in opposite places -- books have no word for a skewer
    # and the web has no Capablanca -- so neither may starve the other.
    read_books: int = 2
    read_web: int = 3
    # How the sentences offered to the judge are chosen:
    #   "assessor"   the opening Assessor, unchanged -- the arm that fails
    #   "definition" a model pick with the veto INVERTED to keep broad sentences
    #   "none"       no model selection at all; the mechanical filter only
    select: str = "definition"
    # Sentences taken per page when no model selects them.
    per_page: int = 6
    transport: object | None = None

    def __post_init__(self) -> None:
        # What the filters threw away on the last draft, by reason. Kept because
        # "the Assessor discards some sentences" is not an answer to "what does
        # the Assessor discard" -- and because every defect in this pipeline so
        # far was found by reading what it produced, not by counting it.
        self.discarded: dict[str, int] = {}
        # Book text by locator, so `_body` serves a passage without a fetch.
        self._passages: dict[str, str] = {}
        self.scout = KnowledgeScout(self.searcher, self.skiplist)
        self.assessor = Assessor(model=self.model, transport=self.transport)
        # The judgement step gets the stronger model; the Assessor keeps the
        # cheap one, where it is measured to be adequate.
        self.compiler = KnowledgeCompiler(model=self.judge,
                                          transport=self.transport)

    def draft(self, key: str) -> Entry:  # noqa: D401
        """One unreviewed entry for one claim.

        Never returns a reviewed entry, and cannot: `Entry` defaults to
        `reviewed=False` and nothing here sets it. Endorsement is the author's
        act alone.
        """
        self.discarded = {}
        topic = topic_for(key)
        # Books first. They are fewer, better, and free of the failure modes
        # the web keeps producing, so they take the first `read` slots.
        from_books = self._from_books(key)[: self.read_books]
        from_web = self.scout.find(key)[: self.read_web]
        candidates = from_books + from_web

        notes: list[str] = []
        sources: list[Source] = []
        for candidate in candidates:
            body = self._body(candidate)
            if not body:
                continue
            # A curated shelf needs no relevance gate: the author chose the
            # books, and a passage of Capablanca can say "chess" zero times
            # and still be Capablanca.
            if not is_book(candidate.url) and not is_about(topic, candidate, body):
                # Refused before any model call: a page that is not about the
                # topic cannot contain a definition of it, and its sentences
                # would only give the judge something plausible to pick.
                continue
            reading = self._read(topic, candidate, body)
            if reading.skip_reason:
                # A page that is not an article puts its DOMAIN on the skip
                # list, so no model call is ever spent on that site again.
                self.skiplist = self.skiplist.add(
                    candidate.url, reading.skip_reason, "assessor", _today()
                )
            if not reading.useful:
                continue
            notes += list(reading.sentences)
            # A site that has helped can never be skipped later -- the guard
            # that stops the list eating its own sources.
            self.skiplist = self.skiplist.mark_useful(candidate.url)
            sources.append(Source(url=candidate.url, publisher=candidate.publisher,
                                  evidence_class="single-expert"))

        return self.compiler.compile(key, tuple(notes), tuple(sources))

    def _read(self, topic: str, candidate: Candidate, body: str):
        """Sentences from one page, by whichever selector is configured."""
        from chesscoach.opening_swarm import Reading

        if self.select == "assessor":
            return self.assessor.read(topic, candidate, body)

        offered = self.assessor.candidates(body)
        broad = []
        for sentence in offered:
            reason = self._why_dropped(sentence)
            if reason:
                self.discarded[reason] = self.discarded.get(reason, 0) + 1
            else:
                broad.append(sentence)
        if not broad:
            return Reading(candidate, ())
        if self.select == "none":
            # No model judgement at all. Page order is kept, because a
            # definition is near the top of an article far more often than not,
            # and any other order would be a selection wearing a disguise.
            return Reading(candidate, tuple(broad[: self.per_page]))
        return Reading(candidate, self._pick_definitions(topic, broad, candidate))

    @staticmethod
    def _why_dropped(sentence: str) -> str:
        """The filter that refused this sentence, or "" if it survived."""
        if is_broad(sentence):
            return ""
        commentary = reads_as_commentary(sentence)
        if commentary:
            return commentary.split(":")[0]
        if _SPECIFIC.search(sentence):
            return "names a square or a move: about one position"
        return "junk: length, advertising, navigation or an analysis line"

    def _pick_definitions(self, topic: str, sentences, candidate) -> tuple[str, ...]:
        """The Assessor's index trick, asked for definitions instead of plans."""
        from chesscoach.opening_swarm import ASSESSOR_SCHEMA, CHUNK

        kept: list[str] = []
        for start in range(0, len(sentences), CHUNK):
            chunk = sentences[start:start + CHUNK]
            numbered = "\n".join(f"{i}. {s}" for i, s in enumerate(chunk))
            try:
                answer = ollama.generate(
                    self.model,
                    DEFINITION_ASSESSOR.format(topic=topic, sentences=numbered,
                                               limit=self.per_page),
                    host=ollama.OLLAMA_URL, num_predict=60,
                    schema=ASSESSOR_SCHEMA, transport=self.transport,
                )
            except ollama.OllamaUnavailable:
                break
            chosen = ollama.ints(ollama.as_json(answer), "keep", len(chunk))
            kept += [chunk[i] for i in chosen[: self.per_page]]
            if len(kept) >= self.per_page:
                break
        return tuple(kept[: self.per_page])

    def _from_books(self, key: str) -> list[Candidate]:
        """Book passages about this claim, as candidates the pipeline reads."""
        if not len(self.library):
            return []
        found = []
        for book, locator, passage in self.library.passages(all_terms(key)):
            self._passages[locator] = passage
            found.append(Candidate(book.title, locator, book.publisher, ""))
        return found

    def _body(self, candidate: Candidate) -> str:
        if is_book(candidate.url):
            return self._passages.get(candidate.url, "")
        try:
            return self.fetch(candidate.url) or ""
        except Exception:
            # A page that will not load is one page, not a failed run.
            return ""
