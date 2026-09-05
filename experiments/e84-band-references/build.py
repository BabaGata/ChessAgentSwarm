"""Three overlapping band references, so a player is compared against their own level.

Note: docs/notes/experiments.e84-band-references.md

[[experiments.e83-spread-rescreen]]'s D2 changed what `allowed_motif`'s denominator
counts, so every reference on disk is stale for those claims and the rebuild was
blocked: the band guard refuses `corpus-blitz` because **15 of 65 players sit
outside 1400-1800**, from 720 to 2006.

Building one band and discarding those players is correct and wasteful. The
corpus supports three, and the third one matters for a reason already on the
books -- a 1900-rated player compared against a 1400-1800 population comes out
with nothing unusual about their play, which is not a statement about their play.

**The bands overlap on purpose.** `declared_band_is_wrong` reads the player's
median rating against the band plus `BAND_EDGE_TOLERANCE`, so a 1500 player
belongs in both 1200-1600 and 1400-1800. These are overlapping windows on one
population, not a partition of it: the question "what do players at this level
do" should include everyone at that level.

    python build.py [--dry-run]
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from chesscoach.peers import declared_band_is_wrong  # noqa: E402
from chesscoach.pipeline import load_games  # noqa: E402

BANDS = ("1200-1600", "1400-1800", "1600-2000")
SPEEDS = {"blitz": "corpus-blitz", "rapid": "corpus-rapid"}

STAGING = REPO / "data/raw/corpus-bands"
OUT = REPO / "data/raw/out/peers-e84.json"
DEPTH = 15
CACHE = REPO / "data/cache/peers.db"


def stage(band: str, speed: str) -> tuple[Path, int]:
    """Copy the players who belong in this band into their own directory.

    The guard's own advice is to "pass the --band they are actually in", and it
    reads a directory. Staging by the very predicate the build will re-check is
    what makes the build pass for a reason rather than by luck.
    """
    source = REPO / "data/raw" / SPEEDS[speed]
    target = STAGING / f"{band}-{speed}"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    kept = 0
    for pgn in sorted(source.glob("*.pgn")):
        if declared_band_is_wrong(load_games(pgn), pgn.stem, band) is None:
            shutil.copy2(pgn, target / pgn.name)
            kept += 1
    return target, kept


def build(directory: Path, band: str, speed: str, merge_with: Path | None) -> None:
    command = [
        sys.executable, "-m", "chesscoach.cli", "build-peer-reference",
        "--pgn-dir", str(directory),
        "--engine", "stockfish",
        "--out", str(OUT),
        "--band", band,
        "--time-control", speed,
        "--depth", str(DEPTH),
        "--cache", str(CACHE),
    ]
    if merge_with is not None:
        command += ["--merge-with", str(merge_with)]

    print(f"  building {band} {speed} ...", flush=True)
    done = subprocess.run(command, cwd=REPO, capture_output=True, text=True)
    if done.returncode != 0:
        # Refusing loudly beats a half-built reference that reads like a whole
        # one -- the failure mode the band guard itself exists to prevent.
        print(done.stdout[-4000:])
        print(done.stderr[-2000:], file=sys.stderr)
        raise SystemExit(f"build failed for {band} {speed}")
    print(f"    {done.stdout.strip().splitlines()[-1] if done.stdout.strip() else 'ok'}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="stage and count, build nothing")
    args = parser.parse_args()

    staged: list[tuple[Path, str, str, int]] = []
    print("STAGING\n" + "=" * 60)
    for band in BANDS:
        for speed in SPEEDS:
            directory, kept = stage(band, speed)
            staged.append((directory, band, speed, kept))
            print(f"  {band:<12} {speed:<6} {kept:>3} players")

    if args.dry_run:
        return 0

    print("\nBUILDING\n" + "=" * 60)
    if OUT.exists():
        OUT.unlink()
    merge_with: Path | None = None
    for directory, band, speed, kept in staged:
        if kept == 0:
            print(f"  skipping {band} {speed}: no players")
            continue
        build(directory, band, speed, merge_with)
        merge_with = OUT

    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
