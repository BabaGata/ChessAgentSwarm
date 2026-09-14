"""Carry marks from an old detection sheet onto a new one, and say what moved.

Screen: docs/notes/experiments.e55-detector-precision.md

The marking is the expensive part. Every regeneration of the sheet has so far
thrown it away -- the author re-marks from scratch, or the marks are scored
against code that has changed under them and `score.py` refuses them (which is
correct, and also the end of the evidence).

**A mark is about a position, not about a line in a file.** It says *"this
detector is right/wrong about `player` at `game_id` ply `N`"*, and that
judgement survives a regeneration whenever the same detector still fires on the
same position. So the marks can be carried, and the only honest way to do it is
to be explicit about the three cases:

  **kept**      the same (detector, player, game, ply) row is on both sheets.
                The mark carries. This is the evidence that survives.
  **gone**      it was marked and the detector no longer fires there, or the
                claim no longer samples it. A `[n]` here is a **fix landing**;
                a `[y]` here is recall lost and worth knowing about.
  **new**       a row on the new sheet nobody has judged. It stays `[ ]`.

**A carried mark is not as good as a fresh one and this does not pretend
otherwise.** The detector changed, which is why the sheet was regenerated; a
`[y]` carried onto a row the detector reaches by a different route is a mark
about the old reasoning. The `--report` output names every carried row so the
author can re-check any of them, and `score.py`'s staleness rule still applies
to the sheet as a whole.

Usage:
    python carry_marks.py --old OLD.txt --new NEW.txt [--out MERGED.txt]
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# `  [y] Hirsican              move  13  Black Be6      lost  15.8 wp`
ROW = re.compile(
    r"^  \[([yn?]?)\s*\]\s+(\S+)\s+move\s+(\d+)\s+(White|Black)\s+(\S+)\s+lost\s+([\d.]+) wp"
)
# `      lichess.org/NF4Pv6NH#26`
LINK = re.compile(r"^\s+lichess\.org/(\S+)#(\d+)\s*$")


def parse(path: Path) -> tuple[dict[tuple, dict], list[str]]:
    """Every marked-or-markable row, keyed by what it is *about*.

    The key is (claim, game_id, ply) -- the position and the claim made about
    it. Not the player name, which is implied by the game, and not the move in
    SAN, which is implied by the position: including either would make a key
    that changes when the display changes rather than when the finding does.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    rows: dict[tuple, dict] = {}
    claim = None
    pending: tuple | None = None

    for index, line in enumerate(lines):
        if line and not line.startswith(" ") and not line.startswith("-") and "." in line.split()[0]:
            claim = line.strip()
            pending = None
            continue

        match = ROW.match(line)
        if match and claim:
            pending = (claim, match.group(1) or " ", index, match.group(2))
            continue

        link = LINK.match(line)
        if link and pending is not None:
            claim_key, mark, row_index, player = pending
            key = (claim_key, link.group(1), int(link.group(2)))
            rows[key] = {
                "mark": mark.strip(),
                "line": row_index,
                "player": player,
                "text": lines[row_index],
            }
            pending = None

    return rows, lines


def notes_under(lines: list[str], index: int) -> list[str]:
    """The author's free-text comment on a row, if they left one.

    Everything indented under the row that is not the link and not the
    machine-written evidence line. Carried with the mark -- a comment is the
    reason for the mark and is worth more than the letter (L-057).
    """
    found = []
    for line in lines[index + 1:]:
        if ROW.match(line) or not line.startswith("      "):
            break
        stripped = line.strip()
        if stripped.startswith("lichess.org/"):
            continue
        # Machine-written lines are regenerated on the new sheet, and the
        # provenance line is re-stamped there, so carrying any of them would
        # duplicate it.
        if stripped.startswith(("punished by", "was available", "engine:", "(carried from")):
            continue
        found.append(line)
    return found


GENERATED = re.compile(r"^GENERATED \S+ from commit (\S+?)\.?$")


def generated_at(lines: list[str]) -> str:
    """The commit a sheet was built from, as it stamped itself."""
    for line in lines[:60]:
        match = GENERATED.match(line.strip())
        if match:
            return match.group(1)
    return "unknown commit"


def main() -> int:
    parser = argparse.ArgumentParser()
    # **Several earlier sheets, oldest first.** Where two of them marked the same
    # claim at the same position, the later mark wins: it is the author's more
    # recent judgement, and usually of code closer to what is running now.
    parser.add_argument("--old", required=True, type=Path, nargs="+")
    parser.add_argument("--new", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    new, new_lines = parse(args.new)

    marked: dict[tuple, dict] = {}
    history: dict[tuple, list[tuple[str, str]]] = defaultdict(list)
    for path in args.old:
        rows, lines = parse(path)
        commit = generated_at(lines)
        count = 0
        for key, row in rows.items():
            if not row["mark"]:
                continue
            count += 1
            history[key].append((path.name, row["mark"]))
            marked[key] = {**row, "source": path.name, "commit": commit,
                           "comment": notes_under(lines, row["line"])}
        print(f"OLD  {path.name}: {len(rows)} rows, {count} marked (built from {commit})")

    kept = {key: row for key, row in marked.items() if key in new}
    gone = {key: row for key, row in marked.items() if key not in new}
    conflicts = {key: marks for key, marks in history.items()
                 if len({mark for _, mark in marks}) > 1}

    print(f"NEW  {args.new.name}: {len(new)} rows")
    print()
    print(f"  distinct marked positions across the old sheets: {len(marked)}")
    if conflicts:
        print(f"  marked differently on different sheets: {len(conflicts)} "
              "(the latest mark is the one carried)")
    print()
    print(f"  kept   {len(kept):3d}  same claim, same position -- the mark carries")
    print(f"  gone   {len(gone):3d}  marked, and the new sheet does not cite it")
    print(f"  new    {len(new) - len(kept):3d}  unjudged")
    print()

    # **What the fixes did, in the author's own verdicts.** A `[n]` that is gone
    # is a rejection that no longer has a row; a `[y]` that is gone is a correct
    # detection this sheet stopped showing, which is the cost side and must be
    # reported next to it rather than under it.
    by_claim: dict[str, Counter] = defaultdict(Counter)
    for key, row in marked.items():
        where = "kept" if key in new else "gone"
        by_claim[key[0]][f"{row['mark']}-{where}"] += 1

    print(f"{'detector':40s}  n:gone y:gone  n:kept y:kept ?:kept")
    print("-" * 82)
    for claim in sorted(by_claim, key=lambda c: -by_claim[c]["n-gone"]):
        counts = by_claim[claim]
        print(f"{claim:40s} {counts['n-gone']:6d} {counts['y-gone']:6d} "
              f"{counts['n-kept']:7d} {counts['y-kept']:6d} {counts['?-kept']:5d}")

    if kept:
        print()
        print("CARRIED MARKS -- each is a judgement of code that has since changed;")
        print("re-check any that matter before leaning on them.")
        for key in sorted(kept):
            row = kept[key]
            clash = "   (sheets disagreed: " + ", ".join(
                f"{mark} on {name}" for name, mark in history[key]) + ")" if key in conflicts else ""
            print(f"  [{row['mark']}] {key[0]}  lichess.org/{key[1]}#{key[2]}  "
                  f"from {row['source']}{clash}")

    if args.out:
        merged = list(new_lines)
        for key, row in kept.items():
            index = new[key]["line"]
            merged[index] = re.sub(r"^  \[.\s*\]", f"  [{row['mark']}]", merged[index], count=1)
        # Comments go back too, after the row's own lines, so the reason
        # survives with the verdict -- followed by where the mark came from and
        # which code it judged, so a carried mark can never be mistaken for a
        # fresh one on the sheet the author marks next.
        for key in sorted(kept, key=lambda k: -new[k]["line"]):
            row = kept[key]
            stamp = f"      (carried from {row['source']}, which judged commit {row['commit']})"
            at = new[key]["line"] + 1
            while at < len(merged) and merged[at].startswith("      ") \
                    and not ROW.match(merged[at]):
                at += 1
            merged[at:at] = row["comment"] + [stamp]
        args.out.write_text("\n".join(merged) + "\n", encoding="utf-8")
        print()
        print(f"merged sheet written to {args.out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
