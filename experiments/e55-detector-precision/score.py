"""Read a marked detection sheet and report precision per detector.

Screen: docs/notes/experiments.e55-detector-precision.md

`state.md` has carried this P0 for a week: *"the deliverable is precision per
detector on hand-verified samples — not a pass/fail."* The sheet exists
(`e46-motif-precision/results/detection-sheet.txt`, 165 boxes across every claim
kind). This reads it back after it has been marked.

**Marking happens in the sheet itself.** Change `[ ]` to `[y]`, `[n]` or `[?]`
and save. No second file to keep in step, and the position, the link and the mark
stay on one line — which matters because the marking is the expensive part and
anything that adds friction to it costs more than it saves.

**A detector nobody has marked is reported as unmarked, never as perfect.** An
empty box is an absence of evidence and the commonest way a screen like this
quietly lies.

Usage:
    python score.py [--sheet PATH] [--only-decided]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.precision import (  # noqa: E402
    MEASURE_SAMPLE,
    PRECISION_FLOOR,
    SCREEN_SAMPLE,
    Dated,
    Marks,
    condemned,
    confirmed,
    module_for,
    unsettled,
)

SHEET = (Path(__file__).resolve().parents[1] / "e46-motif-precision" / "results"
         / "detection-sheet.txt")

# A claim heading sits at the left margin and carries no box; an example line is
# indented and starts with one. Two shapes, so neither can be mistaken for the
# other however the sheet is edited.
# A claim heading: unindented `kind.subject.direction`. **The subject can hold
# spaces, hyphens and apostrophes** -- `out_of_book.Queen's Pawn Game.own`. The
# first version allowed only `[\w.]`, never matched those headings, and credited
# their marks to whichever claim preceded them: `missed_motif.fork` was reported
# at 25 % on the 2026-09-07 sheet when its own marks gave 20 %. The kind must be
# a lowercase word immediately followed by a dot, which no prose line in the
# sheet's header is.
_HEADING = re.compile(r"^(?![ \t])([a-z][a-z_]*\.[^\n]+\.[a-z]+)\s*$")
_BOX = re.compile(r"^\s*\[([ ynYN?])\]")
_COUNT = re.compile(r"([\d,]+)\s+instances")
_RECOVERED = re.compile(r"^([\w.]+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$")

RECOVERED = Path(__file__).parent / "results" / "marks-recovered.txt"


class StaleSheet(Exception):
    """The marks judge code that is no longer there."""


_STAMP = re.compile(r"GENERATED\s+\S+\s+from commit\s+([0-9a-f]+)", re.I)


def stamp_of(path: Path) -> str:
    """The commit a sheet was generated from, or "" if it does not say."""
    # The stamp sits under the sheet's instructions, not at the very top, and a
    # first version read twenty lines and reported a stamped sheet as unstamped
    # -- refusing for the wrong reason, which is only better than not refusing.
    for line in path.read_text(encoding="utf-8-sig").splitlines()[:60]:
        found = _STAMP.search(line)
        if found:
            return found.group(1)
    return ""


def detectors_changed_since(commit: str) -> list[str]:
    """Detector commits landed since `commit`, newest first."""
    if not commit:
        return []
    try:
        done = subprocess.run(
            ["git", "log", "--oneline", f"{commit}..HEAD", "--",
             "chesscoach/tactics.py", "chesscoach/squares.py",
             "chesscoach/structure.py", "chesscoach/sections/"],
            capture_output=True, text=True,
            cwd=Path(__file__).resolve().parents[2], timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    return [line for line in done.stdout.splitlines() if line.strip()]


def refuse_if_stale(path: Path) -> None:
    """Stop rather than score marks against code that has since changed.

    **A stamp nothing reads is a comment.** E55 added the commit stamp to the
    detection sheet precisely so marks could be dated against the code they
    judged -- and E57 then compared a fresh count against a sheet generated two
    commits earlier and recorded the difference as an unexplained side effect of
    the wrong change. The stamp was at the top of the file being read.

    So the check refuses rather than warns. Scoring a stale sheet produces a
    precision figure that looks exactly like a real one, which is worse than no
    figure at all -- the same reasoning that made these marks undateable in the
    first place.
    """
    stamp = stamp_of(path)
    if not stamp:
        raise StaleSheet(
            f"{path.name} carries no commit stamp, so its marks cannot be dated. "
            f"Regenerate it with detection_sheet.py."
        )
    changed = detectors_changed_since(stamp)
    if changed:
        listed = "\n  ".join(changed[:8])
        raise StaleSheet(
            f"{path.name} was generated from {stamp}, and {len(changed)} detector "
            f"commit(s) have landed since:\n  {listed}\n"
            f"These marks judge code that is no longer there. Regenerate the "
            f"sheet before scoring it."
        )


def read(path: Path) -> tuple[list[Marks], dict[str, int]]:
    """Marks per detector, and how often each fired, from one marked sheet."""
    tally: dict[str, list[int]] = {}
    fired: dict[str, int] = {}
    current: str | None = None

    for line in path.read_text(encoding="utf-8-sig").splitlines():
        heading = _HEADING.match(line)
        if heading:
            current = heading.group(1)
            tally.setdefault(current, [0, 0, 0])
            continue
        if current is None:
            continue
        count = _COUNT.search(line)
        if count:
            fired[current] = int(count.group(1).replace(",", ""))
            continue
        box = _BOX.match(line)
        if box:
            mark = box.group(1).lower()
            if mark == "y":
                tally[current][0] += 1
            elif mark == "n":
                tally[current][1] += 1
            elif mark == "?":
                tally[current][2] += 1

    marks = [
        Marks(detector=name, right=right, wrong=wrong, unsure=unsure)
        for name, (right, wrong, unsure) in sorted(tally.items())
    ]
    return marks, fired


def recovered(path: Path) -> dict[str, tuple[int, int, int]]:
    """Marks made before this scorer existed, kept so they are not re-done."""
    if not path.exists():
        return {}
    found: dict[str, tuple[int, int, int]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            continue
        match = _RECOVERED.match(line.strip())
        if match:
            found[match.group(1)] = tuple(int(match.group(i)) for i in (2, 3, 4))
    return found


@lru_cache(maxsize=None)
def last_changed(module: str) -> str:
    """The date this module was last committed, or "" if git cannot say.

    Asked of version control rather than recorded by hand, because a hand-kept
    date is exactly the thing that goes stale silently. An empty answer means
    "cannot tell", and `Dated.stale` then leaves the mark alone -- the check
    must not invalidate marks because git was unavailable (L-046).
    """
    root = Path(__file__).resolve().parents[2]
    try:
        done = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", module],
            cwd=root, capture_output=True, text=True, timeout=20, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return done.stdout.strip() if done.returncode == 0 else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet", type=Path, default=SHEET)
    parser.add_argument("--recovered", type=Path, default=RECOVERED)
    parser.add_argument("--marked-on", default="2026-08-23",
                        help="when the recovered marks were made")
    parser.add_argument("--only-decided", action="store_true",
                        help="hide detectors nobody has marked yet")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    parser.add_argument("--allow-stale", action="store_true",
                        help="score a sheet whose detectors have changed since "
                             "it was generated; the figures will be about code "
                             "that is no longer there")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    if not args.sheet.exists():
        print(f"no sheet at {args.sheet}")
        return 1

    # Refuse rather than warn. A precision figure from a stale sheet looks
    # exactly like a real one, which is the condition E55 was built to end.
    if not args.allow_stale:
        try:
            refuse_if_stale(args.sheet)
        except StaleSheet as exc:
            print(f"REFUSING: {exc}")
            return 1

    marks, fired = read(args.sheet)

    # Earlier marks are ADDED to whatever the sheet now carries, so re-marking a
    # claim the author already judged accumulates rather than replaces.
    earlier = recovered(args.recovered)
    if earlier:
        by_name = {m.detector: m for m in marks}
        for name, (right, wrong, unsure) in earlier.items():
            was = by_name.get(name, Marks(name))
            # Dated, so a detector rebuilt after the marking reads as unmarked
            # rather than as measured. Three of these four were.
            by_name[name] = Dated(
                name, was.right + right, was.wrong + wrong, was.unsure + unsure,
                marked_on=args.marked_on, changed_on=last_changed(module_for(name)),
            )
        marks = sorted(by_name.values(), key=lambda m: m.detector)

    marked = [m for m in marks if m.judged or m.unsure]

    lines = [
        "PRECISION PER DETECTOR",
        "=" * 86,
        "",
        f"Floor {PRECISION_FLOOR:.0%}, from the author's own two verdicts: 4/5 accepted "
        f'("works, leave alone"),',
        '0/5 rejected ("broken"). Provisional, and labelled so.',
        "",
        f"Intervals are Wilson 95 %. At n={SCREEN_SAMPLE} a perfect score still spans "
        f"roughly 57-100 %,",
        f"so the screen can CONDEMN and cannot CONFIRM; that needs about "
        f"n={MEASURE_SAMPLE}.",
        "",
        f"Includes {sum(sum(v) for v in recovered(args.recovered).values())} marks "
        f"recovered from design.informative-claims.md ({args.marked_on}), each",
        "checked against the date its module last changed -- a detector rebuilt "
        "since",
        "carries no measured precision, however many marks it has.",
        "",
        f"  {'detector':<34}{'fired':>8}{'marks':>7}{'prec':>7}"
        f"{'95% interval':>16}  verdict",
        "",
    ]

    for mark in sorted(marks, key=lambda m: -fired.get(m.detector, 0)):
        if args.only_decided and not (mark.judged or mark.unsure):
            continue
        shots = fired.get(mark.detector, 0)
        if mark.judged:
            low, high = mark.interval
            band = f"{low:.0%} - {high:.0%}"
            precision = f"{mark.precision:.0%}"
        else:
            band, precision = "-", "-"
        unsure = f"  ({mark.unsure} unsure)" if mark.unsure else ""
        lines.append(
            f"  {mark.detector[:33]:<34}{shots:>8}{mark.judged:>7}{precision:>7}"
            f"{band:>16}  {mark.verdict.value}{unsure}"
        )

    stale = [m for m in marks if getattr(m, "stale", False)]

    lines += ["", "=" * 86, "WHAT TO DO WITH THIS", ""]
    if stale:
        lines.append(f"  stale        {len(stale):>3}   marked, then the detector "
                     f"changed -- re-mark before trusting either way")
        for mark in stale:
            lines.append(f"      {mark.detector:<34}{mark.reason}")
        lines.append("")
    if not marked:
        lines += [
            "  Nothing is marked yet, so nothing is measured. The table above is the",
            "  work list, not a result: every detector reads 'unmarked', which is an",
            "  absence of evidence and not a pass.",
            "",
            f"  Open {SHEET.name}, change [ ] to [y], [n] or [?], and run this again.",
        ]
    else:
        broken, good, open_ = condemned(marks), confirmed(marks), unsettled(marks)
        lines.append(f"  condemned    {len(broken):>3}   fix or retire before anything "
                     f"downstream is trusted")
        for mark in sorted(broken, key=lambda m: -fired.get(m.detector, 0)):
            lines.append(f"      {mark.detector:<34}{mark.reason}")
        lines.append(f"  confirmed    {len(good):>3}")
        for mark in good:
            lines.append(f"      {mark.detector:<34}{mark.reason}")
        lines.append(f"  unsettled    {len(open_):>3}   where the next marks are worth "
                     f"most")
        for mark in sorted(open_, key=lambda m: -fired.get(m.detector, 0))[:10]:
            lines.append(f"      {mark.detector:<34}{mark.reason}")

    lines += [
        "",
        "A precision figure says how often a detector is right when it fires. It",
        "says nothing about what it MISSES, which needs a different screen and is",
        "the reason D15 defect (a) -- five claims that never become candidates --",
        "is a separate item and not answered here.",
    ]

    text = "\n".join(lines)
    print(text)
    (args.out / "precision.txt").write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
