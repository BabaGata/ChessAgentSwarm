"""Public-domain chess books, as a source the swarm can read.

Design: docs/notes/design.knowledge-base.md

The author asked for books. They are a better source than the open web for the
reason the web kept demonstrating: a book by a world champion is *about chess*
by construction, so none of the machinery built to exclude a Beyonce film, a Go
wiki and a libertarian-communism essay is needed against it.

**Free, and free in the way C7 means it.** These are Project Gutenberg texts,
out of copyright, downloaded once and read from disk forever. No key, no rate
limit, no signup an examiner cannot reproduce.

**What they cover, measured rather than assumed** -- the counts that decided
which claims to point them at:

| | fork | skewer | outpost | pin | castl | develop |
|---|--:|--:|--:|--:|--:|--:|
| Capablanca, *Chess Fundamentals* (1921) | 0 | 0 | 0 | 35 | 15 | 68 |
| Ed. Lasker, *Chess Strategy* (1915) | 1 | 0 | 0 | 68 | 235 | 214 |
| Staunton, *Blue Book of Chess* (1848) | 0 | 0 | 0 | 18 | 281 | 6 |

**The modern tactical vocabulary postdates them.** "Skewer" and "outpost" appear
zero times in all three; "fork" once in three books. So these are not a
replacement for the web -- they are its complement, and they are strong in
exactly the places the web returned nothing: castling, development, pins.

They also write in **descriptive notation**, which is why `_SPECIFIC` had to
learn "P-K4" and "Kt - K B 3": without that, a note on one move read as a
general statement about development.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SHELF = Path(__file__).resolve().parent.parent / "data" / "books"

# A locator, so a citation can name the book and the passage rather than a URL
# nobody can open. `book://` also marks a source as **curated**: the relevance
# gate exists for the open web and a shelf the author chose needs no such check.
SCHEME = "book://"

# Roughly a page of prose. Long enough to hold a definition and its sentence of
# context, short enough that one passage is about one thing.
PASSAGE_CHARS = 2400

# Gutenberg wraps every text in a licence header and footer. Neither is chess.
_START = re.compile(r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG.*?\*\*\*", re.I)
_END = re.compile(r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG.*?\*\*\*", re.I)



# Runs of newlines, so the wrap can be told from the paragraph break.
_NEWLINES = re.compile(r"\n+")

# Where a sentence ends, for the rare paragraph too long to be a passage on its
# own. Kept greedy about the closing punctuation so an abbreviation does not
# split a sentence in half.
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")



def _paragraphs(text: str) -> list[str]:
    """A text split at its paragraph breaks, with the wrap detected not assumed.

    **These books are double-spaced.** A wrapped line ends with two newlines and
    a paragraph ends with four, measured across all three: run lengths are
    `2 x 2783, 4 x 1637` in Capablanca and the same shape in the others, with no
    odd lengths at all. Splitting on a blank line -- correct for ordinary text --
    therefore cut every *line*, which turned 4,434 paragraphs into 4,434
    fragments of at most 75 characters and made paragraph-aware chunking a
    no-op that looked like it worked.

    So the wrap is the **most common** run length and a paragraph is anything
    longer. The exception is a text with only one run length: nothing longer
    exists to contrast with, so there is no wrap to detect and every break is a
    paragraph break. That is the ordinary single-spaced case.

    Wrap newlines inside a paragraph collapse to spaces, which is what makes a
    quoted passage readable rather than typeset to somebody else's column width.
    """
    runs = {}
    for match in _NEWLINES.finditer(text):
        length = len(match.group(0))
        runs[length] = runs.get(length, 0) + 1
    if not runs:
        stripped = " ".join(text.split())
        return [stripped] if stripped else []

    if len(runs) == 1:
        wrap = 0
    else:
        wrap = max(runs, key=lambda length: runs[length])

    parts = re.split(rf"\n{{{wrap + 1},}}", text)
    return [" ".join(part.split()) for part in parts if part.strip()]


def _chunks(text: str) -> list[str]:
    """A book divided at its own paragraph breaks, packed up to the cap.

    **Paragraphs, not a fixed stride.** Stepping every `PASSAGE_CHARS`
    characters was chosen when a passage only had to *contain* a search term. It
    is wrong for the two things the shelf is now asked to do: a passage that
    spans the end of one topic and the start of another has an embedding that
    means neither, and a passage beginning *"ack would be lost, as calculation
    easily shows"* cannot be shown to a player -- and showing the text is the
    point of quoting a book.

    Paragraphs are the author's own division of their argument, so they are the
    boundary to keep. Short ones are packed together, because one paragraph per
    passage would make retrieval return fragments. A paragraph longer than the
    cap on its own is split at sentence ends, and only then.
    """
    passages: list[str] = []
    current: list[str] = []
    size = 0

    def flush() -> None:
        nonlocal current, size
        if current:
            passages.append("\n\n".join(current).strip())
            current, size = [], 0

    for paragraph in _paragraphs(text):
        if not paragraph:
            continue
        if len(paragraph) > PASSAGE_CHARS:
            flush()
            passages.extend(_split_long(paragraph))
            continue
        if size + len(paragraph) > PASSAGE_CHARS:
            flush()
        current.append(paragraph)
        size += len(paragraph) + 2
    flush()
    return [p for p in passages if p]


def _split_long(paragraph: str) -> list[str]:
    """One over-long paragraph, cut at sentence ends rather than mid-word."""
    parts: list[str] = []
    current: list[str] = []
    size = 0
    for sentence in _SENTENCE_END.split(paragraph):
        if size + len(sentence) > PASSAGE_CHARS and current:
            parts.append(" ".join(current).strip())
            current, size = [], 0
        current.append(sentence)
        size += len(sentence) + 1
    if current:
        parts.append(" ".join(current).strip())
    return parts


@dataclass(frozen=True)
class Book:
    """One book on the shelf, with what a citation needs."""

    slug: str
    title: str
    author: str
    year: str
    # Every entry drawn from a book carries this. A master's textbook is one
    # expert writing, however eminent -- `expert-consensus` would be a claim
    # about the field that a single book cannot support.
    evidence_class: str = "single-expert"

    @property
    def publisher(self) -> str:
        return f"{self.author}, {self.title} ({self.year})"


# The shelf. Titles and years are from the Gutenberg records, not from memory.
SHELF = (
    Book("capablanca-chess-fundamentals", "Chess Fundamentals",
         "José Raúl Capablanca", "1921"),
    Book("edward-lasker-chess-strategy", "Chess Strategy", "Edward Lasker", "1915"),
    Book("staunton-blue-book-of-chess", "The Blue Book of Chess",
         "Howard Staunton", "1848"),
    # Added 2026-09-01, when corroboration needed more than three voices. Titles
    # and authors are read from the Gutenberg search result **with the id taken
    # from the same HTML element**: a first parse collected ids and titles into
    # two lists and zipped them, which paired 33870 with "The Big Four" when
    # this project's own records have it as Capablanca. An attribution error is
    # the worst kind of error here, so the parse was corrected and then checked
    # against the three ids already known.
    Book("bird-chess-history-and-reminiscences", "Chess History and Reminiscences",
         "H. E. Bird", "1893"),
    Book("philidor-studies-of-chess", "Studies of Chess",
         "François-André Danican Philidor", "1817"),
    Book("young-chess-generalship", "Chess Generalship, Vol. I",
         "Franklin K. Young", "1910"),
    # **The same lineage as `edward-lasker-chess-strategy`**, deliberately kept
    # apart from the others: two books by one author are one voice, and counting
    # them twice is exactly the ancestry-for-agreement mistake corroboration is
    # built to avoid ([[design.graph-knowledge-base]]).
    Book("edward-lasker-chess-and-checkers", "Chess and Checkers: the Way to Mastership",
         "Edward Lasker", "1918"),
)


def strip_licence(text: str) -> str:
    """The book without Gutenberg's wrapper.

    The header alone is ~800 words of licence terms, and it mentions neither
    chess nor anything else worth quoting -- but it is long enough to dominate a
    passage and it would be cited as a source if it were left in.
    """
    start = _START.search(text)
    if start:
        text = text[start.end():]
    end = _END.search(text)
    if end:
        text = text[: end.start()]
    return text.strip()


@dataclass
class BookLibrary:
    """The shelf, loaded from disk."""

    texts: dict[str, str]
    shelf: tuple[Book, ...] = SHELF

    @classmethod
    def load(cls, path: Path | str = DEFAULT_SHELF) -> BookLibrary:
        """Whatever is on disk. A missing shelf is an empty library, not an error.

        The books are downloaded by `experiments/e64-books/fetch.py` and are not
        in the repository: three Gutenberg texts are 1.4 MB and reproducible
        from their ids.
        """
        path = Path(path)
        texts = {}
        for book in SHELF:
            file = path / f"{book.slug}.txt"
            if file.exists():
                texts[book.slug] = strip_licence(
                    file.read_text(encoding="utf-8", errors="replace")
                )
        return cls(texts)

    def __len__(self) -> int:
        return len(self.texts)

    def book(self, slug: str) -> Book | None:
        return next((b for b in self.shelf if b.slug == slug), None)

    def all_passages(self):
        """Every passage on the shelf, as (book, locator, text).

        **The one place a passage boundary is decided.** `passages()` used to
        chunk inline, and the graph loader needed the same chunking; two loops
        stepping by `PASSAGE_CHARS` are two definitions of "passage 7", and a
        citation that means different text in the store than in a search result
        is worse than no citation. So both read this.
        """
        for book in self.shelf:
            text = self.texts.get(book.slug)
            if not text:
                continue
            for index, passage in enumerate(_chunks(text)):
                yield book, f"{SCHEME}{book.slug}#{index}", passage

    def passage_at(self, locator: str) -> str | None:
        """The text a `book://slug#index` locator names, or None.

        None for a locator this shelf cannot resolve -- a book that is not
        downloaded, or an index past the end -- rather than an empty string,
        which would read as "the passage is blank".
        """
        if not locator.startswith(SCHEME):
            return None
        slug, _, index = locator[len(SCHEME):].partition("#")
        text = self.texts.get(slug)
        if not text or not index.isdigit():
            return None
        for at, (_, found, passage) in enumerate(self.all_passages()):
            if found == locator:
                return passage
        return None

    def citation_holds(self, quoted: str, locator: str) -> bool:
        """Does the passage this locator names still contain the quoted text?

        **The invariant that makes re-chunking safe.** A locator is positional --
        `#7` is the seventh passage -- so any change to how a book is divided
        moves what every stored citation points at, silently. An endorsed entry
        whose quote no longer appears in its own source is worse than an
        unendorsed one, because it still looks checked.

        Whitespace is normalised on both sides: passages are wrapped at the
        column the book was typeset to, and a quote copied out of one carries
        those line breaks.
        """
        passage = self.passage_at(locator)
        if passage is None or not quoted.strip():
            return False
        return " ".join(quoted.split()) in " ".join(passage.split())

    def passages(self, terms, limit: int = 4) -> list[tuple[Book, str, str]]:
        """Passages mentioning the terms, as (book, locator, text).

        **Ranked by usable prose, not by term count.** Counting terms put a
        table of contents and an e-text header at the top of the first run --
        a contents page names every subject in the book exactly once, so on a
        term count it beats the chapter that explains one of them.

        So a passage scores by how many of its SENTENCES both mention a term and
        read as prose: a real sentence, ending in a full stop, long enough to
        say something. A contents page scores zero because it has no sentences.
        """
        wanted = [t.lower() for t in terms if t]
        if not wanted:
            return []

        scored: list[tuple[int, int, Book, str, str]] = []
        for book, locator, passage in self.all_passages():
            score = _prose_hits(passage, wanted)
            if score:
                # The tie-break is the passage's index **within its book**, read
                # back from the locator rather than counted again. Enumerating
                # the whole shelf instead would order ties by shelf position,
                # which is a different result from a refactor that was meant to
                # change nothing.
                index = int(locator.rsplit("#", 1)[1])
                scored.append((-score, index, book, locator, passage))
        scored.sort(key=lambda row: (row[0], row[1]))
        return [(b, loc, text) for _, _, b, loc, text in scored[:limit]]


# A sentence worth counting: ends properly and is long enough to make a claim.
_SENTENCE = re.compile(r"[^.!?]{40,400}[.!?]")

# Front matter, contents pages and the e-text header. All three mention many
# subjects and explain none, and all three were returned by a first version.
_FRONT_MATTER = re.compile(
    r"\b(e-text|etext|project gutenberg|table of contents|CONTENTS|"
    r"transcriber|produced by|INFORMATION ABOUT THIS)\b",
    re.I,
)


def _prose_hits(passage: str, terms) -> int:
    """How many real sentences in this passage mention one of the terms."""
    if _FRONT_MATTER.search(passage):
        return 0
    hits = 0
    for sentence in _SENTENCE.findall(passage):
        low = sentence.lower()
        # A line of moves is not a sentence however it is punctuated.
        if sum(ch.isdigit() for ch in sentence) > len(sentence) // 8:
            continue
        if any(term in low for term in terms):
            hits += 1
    return hits


def is_book(url: str) -> bool:
    """Is this locator a curated book rather than a page off the web?"""
    return url.startswith(SCHEME)
