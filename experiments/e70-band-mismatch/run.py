"""Who is being compared against a population they are not in, and what it costs.

Note: docs/notes/experiments.e70-band-mismatch.md

The author's question was about one player: *"my guess is that he is one of the
better players with higher rating and that he just doesn't make mistakes as often
as others... this also removes recommendation options for those with higher
ranks."*

The guess is right and the mechanism is worse than the guess. A peer lookup is
keyed on `(band, time_control, claim)`. The **speed** arm has been checked
against the games since the stratum guard; the **band** arm never was. `--band`
defaults to `1400-1800` and nothing compares it to who the player actually is.

**No engine pass.** Ratings are in the PGN headers and the finding counts are in
the sheet-build log, so this reads artefacts that already exist. That is the
point: nothing here needed measuring that was not already written down, which is
why it went unnoticed for so long.

    python run.py [--band 1400-1800]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.peers import declared_band_is_wrong  # noqa: E402
from chesscoach.pipeline import load_games  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review" / "games"

# From experiments/e55-detector-precision/results/sheet-build.log, generated at
# commit 20b1cef: how many claims reached the confidence gate for each player,
# and how many were measured at all.
FINDINGS = {
    "bernes": (1, 5), "bjagus": (1, 7), "cademan": (5, 10),
    "Crossfire1983": (2, 7), "goydorak": (1, 8), "Hirsican": (1, 11),
    "maikel5": (0, 2), "maxhayastan": (0, 2),
    "Maximilian_Honigtopf": (6, 6), "Odin5306": (0, 2),
    "Sheriwoyama": (0, 6), "simonvj": (0, 9),
}


def own_rating(games, player: str) -> float | None:
    """The player's own median rating, never the opponent's."""
    ratings = []
    for game in games:
        if (game.white or "").lower() == player.lower():
            rating = game.white_elo
        elif (game.black or "").lower() == player.lower():
            rating = game.black_elo
        else:
            continue
        if rating is not None:
            ratings.append(rating)
    return statistics.median(ratings) if ratings else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--band", default="1400-1800")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    low, high = (int(part) for part in args.band.split("-"))
    rows = []
    for path in sorted(ROOT.glob("*.pgn")):
        player = path.stem
        games = load_games(path)
        rating = own_rating(games, player)
        if rating is None:
            continue
        asserted, measured = FINDINGS.get(player, (None, None))
        where = "inside" if low <= rating <= high else ("above" if rating > high else "below")
        rows.append((player, rating, where, asserted, measured,
                     declared_band_is_wrong(games, player, args.band)))

    rows.sort(key=lambda r: -r[1])

    lines = [
        f"WHO IS BEING COMPARED AGAINST THE {args.band} BAND, AND WHO IS IN IT",
        "=" * 78, "",
        "Every one of these players was diagnosed against the 1400-1800 peer",
        "reference. The reference has exactly one stratum, so there was never",
        "another population any of them could have been compared against.",
        "",
        f"  {'player':<24}{'Elo':>6}{'where':>9}{'asserted':>10}{'measured':>10}",
        "  " + "-" * 59,
    ]
    for player, rating, where, asserted, measured, _ in rows:
        a = "-" if asserted is None else str(asserted)
        m = "-" if measured is None else str(measured)
        lines.append(f"  {player[:23]:<24}{rating:>6.0f}{where:>9}{a:>10}{m:>10}")

    grouped: dict[str, list[int]] = {}
    for _, _, where, asserted, _, _ in rows:
        if asserted is not None:
            grouped.setdefault(where, []).append(asserted)

    lines += ["", "=" * 78, "ASSERTED FINDINGS BY WHERE THE PLAYER SITS", "=" * 78, ""]
    for where in ("above", "inside", "below"):
        got = grouped.get(where, [])
        if got:
            lines.append(f"  {where:<8} n={len(got)}  findings {sorted(got)}  "
                         f"mean {statistics.mean(got):.1f}")

    rated = [(r[1], r[3]) for r in rows if r[3] is not None]
    if len(rated) >= 3:
        r = statistics.correlation([x for x, _ in rated], [y for _, y in rated])
        lines += ["", f"  r(rating, asserted findings) = {r:+.2f}"]

    refused = [r for r in rows if r[5]]
    lines += [
        "", "=" * 78,
        f"  in the band       {len(rows) - len(refused):>3} of {len(rows)}",
        f"  outside it        {len(refused):>3} of {len(rows)}",
        "",
        "The players above the band are compared against people rated below",
        "them, so nothing they do is unusual and they are told nothing. The",
        "players below it are compared against people rated above them, so",
        "everything is unusual and they are told the most. Neither figure is",
        "a statement about how they play.",
        "",
    ]
    for row in refused:
        lines.append(f"  {row[5]}")

    text = "\n".join(lines) + "\n"
    (args.out / "band-mismatch.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
