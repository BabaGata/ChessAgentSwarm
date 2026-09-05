"""Read what the swarm drafted, and endorse the entries that are right.

Design: docs/notes/design.knowledge-base.md

Endorsement is the author's act and nothing else can perform it — the same rule
as `reviewed` on a guide link and `approve` in the run store. This is the door,
and it is deliberately the only one.

    python review.py                      # everything waiting, with sources
    python review.py --key fork           # one entry in full
    python review.py --endorse fork       # "yes, this is right"
    python review.py --endorse fork --note "narrower than the detector"

Where the swarm found nothing, write it yourself. A definition still needs a
source -- hard rule 7 does not bend for the author -- and writing is not
endorsing, so you can read it back before deciding:

    python review.py --write moved_into_attack         --definition "Moving a piece to a square where it can be taken for free."         --source https://en.wikipedia.org/wiki/Glossary_of_chess --publisher Wikipedia         --evidence expert-consensus

    python review.py --write fork --not-this "a double attack by two pieces"

**Read the definition against the detector before endorsing it.** The whole
reason this field is retrieved rather than written is that it becomes the
independent check on the code — and the first live entry showed why that check
matters: the swarm found *"an absolute fork is when a piece attacks two or more
enemy pieces simultaneously, one of them being the King"*, which is a real
definition of a **subtype**. Adopting it as the rule would narrow the detector
wrongly. A retrieved definition that disagrees with the detector is a question,
not an answer.

`not_this` stays empty until you write it. No agent may fill it.
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.knowledge import (
    KnowledgeBase,
    NotEndorsed,
    Source,
    write_definition,
    write_not_this,
)  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "data" / "knowledge.json"


def wrap(text: str, indent: str = "      ") -> str:
    return textwrap.fill(text, width=88, initial_indent=indent,
                         subsequent_indent=indent)


def show(entry, full: bool = False) -> None:
    mark = "reviewed" if entry.reviewed else "draft"
    print(f"  [{mark}] {entry.key}")
    if not entry.definition:
        print("      (no definition found -- the swarm refused rather than guessing)")
    else:
        print(wrap(entry.definition))
    if entry.why:
        print(f"      WHY  {entry.why[:200]}")
    for suggestion in entry.practice:
        print(f"      PRACTICE  {suggestion[:180]}")
    if entry.not_this:
        for line in entry.not_this:
            print(f"      NOT      {line}")
    elif entry.definition:
        print("      NOT      -- empty. Yours to write; no agent may fill it.")
    if full or entry.definition:
        for source in entry.sources:
            print(f"      SRC  {source.publisher:22} {source.url}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=OUT)
    parser.add_argument("--key", default="")
    parser.add_argument("--endorse", default="")
    parser.add_argument("--note", default="")
    # The author's own words, for the claims no source defines.
    parser.add_argument("--write", default="", metavar="KEY",
                        help="write your own definition for KEY")
    parser.add_argument("--definition", default="", help="the sentence, with --write")
    parser.add_argument("--source", default="",
                        help="URL backing your definition; required with --write")
    parser.add_argument("--publisher", default="", help="who said it, with --source")
    parser.add_argument("--evidence", default="single-expert",
                        choices=("measured", "expert-consensus", "single-expert", "folklore"))
    parser.add_argument("--not-this", default="", dest="not_this",
                        help="what this is NOT; semicolon-separated. Yours alone.")
    parser.add_argument("--all", action="store_true",
                        help="include entries that found nothing")
    args = parser.parse_args()

    base = KnowledgeBase.load(args.path)
    if not len(base):
        print(f"nothing at {args.path}")
        return 1

    if args.write:
        if args.not_this:
            write_not_this(base, args.write,
                           tuple(p.strip() for p in args.not_this.split(";") if p.strip()))
        if args.definition:
            if not args.source:
                print("--definition needs --source: a chess claim carries one (hard rule 7)")
                return 1
            try:
                write_definition(
                    base, args.write, args.definition,
                    source=Source(url=args.source,
                                  publisher=args.publisher or args.source,
                                  evidence_class=args.evidence),
                    note=args.note,
                )
            except NotEndorsed as exc:
                print(f"cannot write: {exc}")
                return 1
        base.save(args.path)
        entry = base.get(args.write)
        print(f"{args.write} written, still unreviewed.")
        show(entry, full=True)
        print("Endorse it separately when you have read it against the detector:")
        print(f"    python review.py --endorse {args.write}")
        return 0

    if args.endorse:
        try:
            base.endorse(args.endorse, note=args.note)
        except KeyError:
            print(f"no entry for {args.endorse!r}")
            return 1
        except NotEndorsed as exc:
            # Refused rather than recorded: an endorsement of an entry with no
            # definition or no source would put the author's name on nothing.
            print(f"cannot endorse: {exc}")
            return 1
        base.save(args.path)
        print(f"{args.endorse} endorsed. It may now appear in a report.")
        return 0

    if args.key:
        entry = base.get(args.key)
        if entry is None:
            print(f"no entry for {args.key!r}")
            return 1
        show(entry, full=True)
        return 0

    pending = base.pending()
    empty = [e for e in base.entries.values() if not e.complete]
    reviewed = [e for e in base.entries.values() if e.reviewed]

    print(f"{len(base)} entries: {len(reviewed)} reviewed, {len(pending)} waiting, "
          f"{len(empty)} found nothing")
    print()
    if pending:
        print("WAITING FOR YOU")
        print("=" * 88)
        for entry in pending:
            show(entry)

    if empty:
        print("FOUND NOTHING -- the swarm refused rather than guessing")
        print("=" * 88)
        if args.all:
            for entry in sorted(empty, key=lambda e: e.key):
                show(entry)
        else:
            print("  " + ", ".join(sorted(e.key for e in empty)))
            print("  (--all to see their sources)")
        print()

    print("endorse with:  python review.py --endorse <key> [--note '...']")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
