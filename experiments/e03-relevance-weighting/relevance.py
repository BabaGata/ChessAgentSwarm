"""Measure whether a detected feature carries information about errors (E03).

Open question C6: how is a detected feature weighted for relevance?

The measure used here is **conditional error lift**. For a feature F and a set of
moves, compare the probability that the mover errs when F is present against the
probability when it is absent:

    lift(F) = P(error | F present) / P(error | F absent)

A feature that carries no information about this player's mistakes has lift near
1, however often it is detected. That is precisely the isolated-pawn problem from
E02: present in 96% of games, and -- if lift is 1 -- telling us nothing.

Two levels are reported:

  * **population** -- pooled over every player in the sample, answering "is this
    feature associated with errors at all, in this band?";
  * **per player** -- answering "is this feature unusually costly *for this
    player*?", which is what personalised coaching actually requires.

Confidence intervals are Wilson score intervals, and every figure is reported
with its sample size, because a lift computed from nine moves is not a finding.

Usage:
    python relevance.py --records records.jsonl --out DIR
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

# Below this many observations a rate is reported but flagged as unreliable.
MIN_OBSERVATIONS = 50

Z = 1.96  # 95%


def wilson(successes: int, total: int) -> tuple[float, float]:
    """Wilson score interval -- behaves sensibly at small n, unlike the normal approximation."""
    if total == 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1 + Z**2 / total
    centre = (p + Z**2 / (2 * total)) / denom
    margin = Z * math.sqrt(p * (1 - p) / total + Z**2 / (4 * total**2)) / denom
    return (round(100 * max(0.0, centre - margin), 1), round(100 * min(1.0, centre + margin), 1))


class Tally:
    """Error counts with and without a feature."""

    def __init__(self) -> None:
        self.present_n = 0
        self.present_err = 0
        self.present_blunder = 0
        self.absent_n = 0
        self.absent_err = 0
        self.games: set[str] = set()

    def add(self, present: bool, is_error: bool, is_blunder: bool, game_id: str) -> None:
        if present:
            self.present_n += 1
            self.present_err += is_error
            self.present_blunder += is_blunder
            self.games.add(game_id)
        else:
            self.absent_n += 1
            self.absent_err += is_error

    def summary(self) -> dict[str, object]:
        rate_present = self.present_err / self.present_n if self.present_n else 0.0
        rate_absent = self.absent_err / self.absent_n if self.absent_n else 0.0
        lift = (rate_present / rate_absent) if rate_absent else None
        return {
            "n_present": self.present_n,
            "n_absent": self.absent_n,
            "games_with_feature": len(self.games),
            "err_rate_present_pct": round(100 * rate_present, 1),
            "err_rate_absent_pct": round(100 * rate_absent, 1),
            "ci95_present_pct": wilson(self.present_err, self.present_n),
            "blunder_rate_present_pct": round(
                100 * self.present_blunder / self.present_n if self.present_n else 0.0, 1
            ),
            "lift": round(lift, 2) if lift else None,
            "reliable": self.present_n >= MIN_OBSERVATIONS and self.absent_n >= MIN_OBSERVATIONS,
        }


# How many of the mover's own subsequent moves to accumulate loss over. A
# positional weakness is not expected to cause an immediate blunder; it is
# expected to make the next several moves quietly worse.
DRIFT_MOVES = 3


def load(records_path: Path) -> list[dict]:
    with records_path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def add_drift(records: list[dict]) -> None:
    """Attach cumulative loss over the mover's next DRIFT_MOVES own moves.

    Move-level error labels capture blunders, which are overwhelmingly tactical.
    A positional feature is more plausibly associated with *slow decay* -- a
    sequence of slightly worse moves -- so this measures that instead.
    """
    sequences: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for record in records:
        sequences[(record["game_id"], record["mover"])].append(record)

    for sequence in sequences.values():
        sequence.sort(key=lambda r: r["ply"])
        for index, record in enumerate(sequence):
            window = sequence[index : index + DRIFT_MOVES]
            record["drift_wp"] = round(sum(w["loss_wp"] for w in window), 2)
            record["drift_complete"] = len(window) == DRIFT_MOVES


def drift_by_feature(records: list[dict], feature_names: list[str]) -> dict[str, object]:
    """Mean cumulative loss with and without each feature, and the ratio."""
    usable = [r for r in records if r.get("drift_complete")]
    out: dict[str, object] = {}
    for name in feature_names:
        present = [r["drift_wp"] for r in usable if name in r["features"]]
        absent = [r["drift_wp"] for r in usable if name not in r["features"]]
        mean_present = sum(present) / len(present) if present else 0.0
        mean_absent = sum(absent) / len(absent) if absent else 0.0
        out[name] = {
            "n_present": len(present),
            "mean_drift_present": round(mean_present, 2),
            "mean_drift_absent": round(mean_absent, 2),
            "drift_ratio": round(mean_present / mean_absent, 2) if mean_absent else None,
        }
    return out


def lift_within_phase(records: list[dict], feature_names: list[str]) -> dict[str, object]:
    """Error lift computed inside each phase, to strip out the phase confound."""
    out: dict[str, object] = {}
    for phase in sorted({r["phase"] for r in records}):
        rows = [r for r in records if r["phase"] == phase]
        tallies = tally(rows, set(feature_names))
        out[phase] = {
            name: {
                "n_present": summary["n_present"],
                "err_present_pct": summary["err_rate_present_pct"],
                "err_absent_pct": summary["err_rate_absent_pct"],
                "lift": summary["lift"],
            }
            for name, summary in ((n, t.summary()) for n, t in tallies.items())
        }
    return out


def tally(records: list[dict], feature_names: set[str]) -> dict[str, Tally]:
    tallies: dict[str, Tally] = defaultdict(Tally)
    for record in records:
        present = set(record["features"])
        is_error = record["label"] is not None
        is_blunder = record["label"] == "blunder"
        for name in feature_names:
            tallies[name].add(name in present, is_error, is_blunder, record["game_id"])
    return tallies


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    records = load(args.records)
    feature_names = sorted({name for r in records for name in r["features"]})
    overall_err = sum(1 for r in records if r["label"]) / max(1, len(records))

    print(f"{len(records)} moves, {len(feature_names)} feature keys")
    print(f"baseline error rate: {100 * overall_err:.1f}%\n")

    population = {name: t.summary() for name, t in tally(records, set(feature_names)).items()}

    # Per player: the mover must be the player whose games these are, otherwise
    # we would be measuring their opponents.
    by_player: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        if record["mover"].lower() == str(record["source_player"]).lower():
            by_player[record["mover"]].append(record)

    per_player = {
        player: {
            "moves": len(rows),
            "err_rate_pct": round(100 * sum(1 for r in rows if r["label"]) / max(1, len(rows)), 1),
            "features": {n: t.summary() for n, t in tally(rows, set(feature_names)).items()},
        }
        for player, rows in by_player.items()
    }

    # Confound check: does the feature/error association simply track game phase?
    by_phase = {
        phase: {
            "moves": len([r for r in records if r["phase"] == phase]),
            "err_rate_pct": round(
                100
                * sum(1 for r in records if r["phase"] == phase and r["label"])
                / max(1, len([r for r in records if r["phase"] == phase])),
                1,
            ),
        }
        for phase in sorted({r["phase"] for r in records})
    }

    add_drift(records)
    drift = drift_by_feature(records, feature_names)
    within_phase = lift_within_phase(records, feature_names)

    results = {
        "moves": len(records),
        "baseline_err_rate_pct": round(100 * overall_err, 1),
        "min_observations_for_reliable": MIN_OBSERVATIONS,
        "drift_moves": DRIFT_MOVES,
        "by_phase": by_phase,
        "population": population,
        "drift": drift,
        "lift_within_phase": within_phase,
        "per_player": per_player,
    }
    (args.out / "relevance.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"{'feature':28} {'n':>6} {'err%':>6} {'vs absent':>10} {'lift':>6}  reliable")
    for name in sorted(population, key=lambda n: -(population[n]["lift"] or 0)):
        s = population[name]
        print(
            f"{name:28} {s['n_present']:>6} {s['err_rate_present_pct']:>6} "
            f"{s['err_rate_absent_pct']:>10} {str(s['lift']):>6}  {s['reliable']}"
        )

    print("\nphase:", json.dumps(by_phase))

    print(f"\ncumulative loss over next {DRIFT_MOVES} own moves (win-% points)")
    print(f"{'feature':28} {'n':>6} {'present':>9} {'absent':>8} {'ratio':>6}")
    for name in sorted(drift, key=lambda n: -(drift[n]["drift_ratio"] or 0)):
        d = drift[name]
        print(
            f"{name:28} {d['n_present']:>6} {d['mean_drift_present']:>9} "
            f"{d['mean_drift_absent']:>8} {str(d['drift_ratio']):>6}"
        )

    print("\nerror lift computed within each phase (confound stripped)")
    for phase, features in within_phase.items():
        best = sorted(features.items(), key=lambda kv: -(kv[1]["lift"] or 0))[:3]
        shown = ", ".join(f"{n} {v['lift']} (n={v['n_present']})" for n, v in best)
        print(f"  {phase:20} {shown}")

    print(f"\nWritten -> {args.out / 'relevance.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
