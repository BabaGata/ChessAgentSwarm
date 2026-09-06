"""What the swarm knows about each thing it detects.

Design: docs/notes/design.knowledge-base.md

The author's request: one entry per detected claim, holding what the thing is,
why it matters, how to practise it, and where to read more. Drafted by the swarm
(Option C), approved by the author, and never shown to a player before that.

**Four parts with four provenances**, which is why they are separate fields
rather than one blob of prose:

| field | comes from | evidence class |
|---|---|---|
| `definition` + `quote` | a retrieved source, verbatim | whatever the source is |
| `not_this` | **the author** | `measured` -- it is the detector's rule |
| `why` / cost | this project's own corpus, at report time | `measured` |
| `practice`, `links` | sources, or nothing at all | `single-expert` at best |

**`not_this` is the load-bearing field**, and it is the one a model may not
write. The web's definition of a fork is *"one piece attacks two pieces at
once"* -- which is exactly what the broken detector implemented, counting 1,014
double attacks where three were forks. What fixed it was the author's sentence
about definite material loss, which no consulted source states. A retrieved
definition is the vague version by construction, and vagueness is invisible in
prose and fatal in a detector.

**`reviewed` means the author endorsed it.** Same rule as `reviewed` in the
guide library and `approve` in the run store: no drafting path may set it, and
`for_player` refuses everything without it.
"""

from __future__ import annotations

import json
from datetime import date
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "knowledge.json"

# Per capacity.knowledge. `measured` is the strongest and is what the project's
# own corpus supplies; `folklore` is recorded so it can be refused, not used.
EVIDENCE_CLASSES = ("measured", "expert-consensus", "single-expert", "folklore")

# An entry may never be shown to a player on this basis. R-03: LLM-generated
# chess advice is not a source.
UNUSABLE_EVIDENCE = ("folklore",)


class NotEndorsed(Exception):
    """Something tried to publish an entry the author has not reviewed."""


@dataclass(frozen=True)
class Source:
    """Where a statement came from, and how much that is worth."""

    url: str
    publisher: str
    evidence_class: str = "single-expert"

    def __post_init__(self) -> None:
        if self.evidence_class not in EVIDENCE_CLASSES:
            raise ValueError(f"unknown evidence class: {self.evidence_class!r}")

    @property
    def usable(self) -> bool:
        return bool(self.url) and self.evidence_class not in UNUSABLE_EVIDENCE


@dataclass(frozen=True)
class Entry:
    """One detected thing, explained.

    `key` is the claim kind or motif name the detectors use -- `fork`,
    `late_castling`, `hangingPawn` -- so an entry can be found from a finding
    without a translation table that could drift.
    """

    key: str
    # Retrieved and quoted rather than paraphrased: a paraphrase of a definition
    # is where the precision goes, and precision is the whole point.
    definition: str = ""
    quote: str = ""
    sources: tuple[Source, ...] = ()
    # What the thing is NOT. The author's, never the swarm's.
    not_this: tuple[str, ...] = ()
    why: str = ""
    practice: tuple[str, ...] = ()
    # Drafting provenance, so a run can be traced back.
    drafted_by: str = ""
    checked_on: str = ""
    # AUTHOR ONLY. Never set by a drafting path.
    reviewed: bool = False
    note: str = ""

    @property
    def has_source(self) -> bool:
        """Hard rule 7: every chess claim carries a source."""
        return any(source.usable for source in self.sources)

    @property
    def complete(self) -> bool:
        """Enough to be worth showing, if it were also reviewed."""
        return bool(self.definition) and self.has_source

    def shown_to_player(self) -> dict:
        """The player-facing view, or an error.

        Refuses rather than returning a blank: an entry silently rendered empty
        is the L-046 shape, and this one would be empty *in front of a player*.
        """
        if not self.reviewed:
            raise NotEndorsed(f"{self.key}: not reviewed by the author")
        if not self.has_source:
            raise NotEndorsed(f"{self.key}: no usable source (hard rule 7)")
        return {
            "what": self.definition,
            "why": self.why,
            "practice": list(self.practice),
            "links": [{"url": s.url, "publisher": s.publisher} for s in self.sources
                      if s.usable],
        }


@dataclass
class KnowledgeBase:
    """Entries by key, loaded from and saved to one JSON file.

    Same shape as `guides.json`, which works and which the author already
    reviews: a load format, not a query format.
    """

    entries: dict[str, Entry] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.entries)

    def get(self, key: str) -> Entry | None:
        return self.entries.get(key)

    def for_player(self, key: str) -> dict | None:
        """What a report may say about this claim, or `None` if nothing yet.

        `None` here is honest: it means *"we have nothing endorsed to say"*,
        which is a different sentence from a blank explanation and is why the
        caller gets a `None` to check rather than an empty string to print.
        """
        entry = self.entries.get(key)
        if entry is None or not entry.reviewed:
            return None
        return entry.shown_to_player()

    def draft(self, entry: Entry) -> None:
        """Add or replace a drafted entry, **never endorsing it**.

        A draft for a key the author has already reviewed does not overwrite it:
        re-running the swarm must not silently discard a human judgement, which
        is the same protection the skip list has.
        """
        existing = self.entries.get(entry.key)
        if existing is not None and existing.reviewed:
            return
        self.entries[entry.key] = replace(entry, reviewed=False)

    def endorse(self, key: str, note: str = "") -> None:
        """The author's act, and only theirs."""
        entry = self.entries[key]
        if not entry.complete:
            raise NotEndorsed(
                f"{key}: nothing to endorse -- needs a definition and a source"
            )
        self.entries[key] = replace(entry, reviewed=True, note=note or entry.note)

    def pending(self) -> tuple[Entry, ...]:
        """Drafted, complete, and waiting on the author."""
        return tuple(sorted(
            (e for e in self.entries.values() if not e.reviewed and e.complete),
            key=lambda e: e.key,
        ))

    def missing(self, wanted) -> tuple[str, ...]:
        """Keys with no usable entry yet, in a stable order."""
        return tuple(sorted(
            key for key in wanted
            if key not in self.entries or not self.entries[key].complete
        ))

    @classmethod
    def load(cls, path: Path | str = DEFAULT_PATH) -> KnowledgeBase:
        try:
            raw = json.loads(Path(path).read_text(encoding="utf-8"))
        except FileNotFoundError:
            return cls()
        entries = {}
        for row in raw.get("entries", []):
            sources = tuple(Source(**s) for s in row.pop("sources", []))
            entries[row["key"]] = Entry(
                **{**row,
                   "sources": sources,
                   "not_this": tuple(row.get("not_this", ())),
                   "practice": tuple(row.get("practice", ()))}
            )
        return cls(entries)

    def save(self, path: Path | str = DEFAULT_PATH) -> None:
        rows = []
        for entry in sorted(self.entries.values(), key=lambda e: e.key):
            row = asdict(entry)
            row["sources"] = [asdict(s) for s in entry.sources]
            row["not_this"] = list(entry.not_this)
            row["practice"] = list(entry.practice)
            rows.append(row)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {"note": "Drafted by the swarm; nothing with reviewed=false is "
                         "ever shown to a player.",
                 "entries": rows},
                indent=1,
            ),
            encoding="utf-8",
        )


def write_definition(base: KnowledgeBase, key: str, definition: str,
                     source: Source | None, note: str = "") -> None:
    """The author's own definition, for a claim no source defines.

    Four claims are this project's error categories rather than terms the
    literature names -- `hangingPawn`, `allows_pressure`, `moved_into_attack`,
    `opening_pawn_error` -- so the swarm has nothing to offer and the only door was
    `endorse`, which needs something to endorse. This is the other door.

    **Hard rule 7 does not bend for the author.** A definition still carries a
    source, because the reason for the rule -- that a reader can check the claim
    -- is not weakened by who typed it.

    **Writing is not endorsing.** The entry stays `reviewed=False`, so the author
    can write it, read it back against the detector, and decide separately.
    """
    if source is None or not source.usable:
        raise NotEndorsed(f"{key}: an author's definition still needs a source (hard rule 7)")

    existing = base.entries.get(key)
    kept = tuple(s for s in (existing.sources if existing else ()) if s.usable)
    base.entries[key] = replace(
        existing or Entry(key=key),
        definition=definition,
        quote=definition,
        sources=(source,) + tuple(s for s in kept if s.url != source.url),
        drafted_by="author",
        checked_on=date.today().isoformat(),
        reviewed=False,
        note=note or (existing.note if existing else ""),
    )


def write_not_this(base: KnowledgeBase, key: str, not_this: tuple[str, ...]) -> None:
    """What the thing is NOT. The author's field, and no agent may fill it.

    Kept separate from `write_definition` because it is the one field with no
    drafting path at all: the web's definition of a fork is *"one piece attacks
    two pieces at once"*, which is precisely what the broken detector
    implemented, and only a human who has read both can say so.
    """
    existing = base.entries.get(key) or Entry(key=key)
    base.entries[key] = replace(existing, not_this=tuple(not_this))
