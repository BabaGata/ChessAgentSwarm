"""Move stored citations to the passages that now hold their text.

Note: docs/notes/experiments.e78-rechunk.md

A `book://slug#7` locator is **positional**, so changing how a book is divided
moves what every stored citation points at -- silently, and an endorsed entry
whose quote is no longer in its own source is worse than an unendorsed one
because it still looks checked.

`BookLibrary.citation_holds` is the invariant that makes the change visible:
does the passage a locator names still contain the text that was quoted from it?

**Each source is re-anchored by its own old text**, resolved through the chunker
that was in force when it was written. A first version matched every source
against the *entry's definition* instead, and would have rewritten all four of
`long_think_error`'s sources to the single passage holding that one sentence --
collapsing four distinct citations into four copies of one, which is a worse
corruption than the stale locators it was fixing.

Anything that cannot be re-anchored is **reported, never guessed at**: a citation
pointing somewhere plausible is the failure this exercise exists to avoid.

    python reanchor.py            report only
    python reanchor.py --write    rewrite data/knowledge.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.books import SCHEME, BookLibrary  # noqa: E402

STORE = Path(__file__).resolve().parents[2] / "data" / "knowledge.json"



# The chunker that was in force when these locators were written: a fixed stride
# through the raw text. Kept here and nowhere else -- it exists only to read old
# citations, and `chesscoach.books` should have exactly one way to divide a book.
def _legacy_passages(library) -> dict[str, str]:
    """Old locator -> the text it used to name, normalised."""
    from chesscoach.books import PASSAGE_CHARS
    found = {}
    for book in library.shelf:
        text = library.texts.get(book.slug)
        if not text:
            continue
        for index, start in enumerate(range(0, len(text), PASSAGE_CHARS)):
            found[f"{SCHEME}{book.slug}#{index}"] = " ".join(
                text[start:start + PASSAGE_CHARS].split())
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--store", type=Path, default=STORE)
    args = parser.parse_args()

    if not args.store.exists():
        print(f"no store at {args.store}")
        return 0

    library = BookLibrary.load()
    # One pass over the shelf; the quotes are short and the shelf is small.
    passages = [(locator, " ".join(text.split()))
                for _, locator, text in library.all_passages()]
    legacy = _legacy_passages(library)

    raw = json.loads(args.store.read_text(encoding="utf-8"))
    entries = raw if isinstance(raw, list) else raw.get("entries", [])

    moved = held = lost = 0
    print(f"{'entry':<22}{'locator':<44}outcome")
    print("-" * 92)

    for entry in entries:
        quoted = " ".join((entry.get("definition") or "").split())
        for source in entry.get("sources", []):
            locator = source.get("url", "")
            if not locator.startswith(SCHEME):
                continue
            if quoted and library.citation_holds(quoted, locator):
                held += 1
                continue
            # **This source's own old text**, not the entry's definition. A
            # middle slice, because the boundaries are exactly what moved: the
            # start and end of an old passage may now fall in two new ones,
            # while the middle is inside a single paragraph.
            was = legacy.get(locator, "")
            probe = was[len(was) // 3: len(was) // 3 + 200].strip()
            found = [loc for loc, body in passages if probe and probe in body]
            if len(found) == 1:
                print(f"{entry.get('key','')[:21]:<22}{locator:<44}-> {found[0]}")
                if args.write:
                    source["url"] = found[0]
                moved += 1
            elif not found:
                note = ("old locator does not resolve" if not was
                        else "old text not found under the new chunking")
                print(f"{entry.get('key','')[:21]:<22}{locator:<44}{note}")
                lost += 1
            else:
                print(f"{entry.get('key','')[:21]:<22}{locator:<44}"
                      f"ambiguous, {len(found)} passages -- left alone")
                lost += 1

    print()
    print(f"  already correct   {held}")
    print(f"  re-anchored       {moved}")
    print(f"  not re-anchored   {lost}")
    if args.write and moved:
        args.store.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n",
                              encoding="utf-8")
        print(f"\n  written to {args.store}")
    elif moved:
        print("\n  dry run -- pass --write to apply")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
