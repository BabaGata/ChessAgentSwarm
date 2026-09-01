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
            for index, start in enumerate(range(0, len(text), PASSAGE_CHARS)):
                yield book, f"{SCHEME}{book.slug}#{index}", text[start:start + PASSAGE_CHARS]

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
