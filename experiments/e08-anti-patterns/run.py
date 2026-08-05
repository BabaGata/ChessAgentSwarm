"""E08 — is the swarm actually saying something different to each player?

Implements the anti-pattern family from docs/notes/evaluation.md, which has been
blocked since it was designed on there being a language layer to point at. There
now is one.

    D1  inter-player divergence  — a generic coach writes near-identical text for
                                   everyone. This is the direct test for R-12.
    D2  base-rate specificity    — is the claim true of most of the population?
                                   Then it is a description, not a diagnosis.
    D3  priority count           — more than two priorities is the "list nine
                                   weaknesses" anti-pattern.
    D4  groundedness             — fraction of claims citing a specific game.

D1 has been P1 in state.md for several cycles with the note that it "would have
caught M5's base-rate finding automatically instead of by eye". This is that.

Usage:
    python run.py --profiles DIR
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach.explainer import render  # noqa: E402
from chesscoach.profile.io import load_profile  # noqa: E402
from chesscoach.profile.models import PlayerProfile  # noqa: E402

# evaluation.md D3: the arbiter's own limit. More than this and the report is
# the anti-pattern it was built to avoid.
MAX_PRIORITIES = 2


def load_all(directory: Path) -> list[PlayerProfile]:
    profiles = []
    for path in sorted(directory.glob("*.json")):
        try:
            profiles.append(load_profile(path))
        except (ValueError, KeyError) as error:
            print(f"  skipped {path.name}: {error}")
    return profiles


def claim_keys(profile: PlayerProfile) -> set[str]:
    """What the report would actually tell this player about."""
    if profile.plan is None:
        return set()
    planned = {step.finding_id for step in profile.plan.steps}
    return {f.claim.key() for f in profile.findings if f.id in planned}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b) if (a | b) else 1.0


def divergence(profiles: list[PlayerProfile]) -> dict:
    """D1. Pairwise overlap between what different players are told.

    Reported as overlap rather than distance so that the failure direction is
    unambiguous: **high is bad**. A coach telling everyone the same thing scores
    1.0 here.
    """
    advised = [(p.player.username, claim_keys(p)) for p in profiles]
    advised = [(name, keys) for name, keys in advised if keys]

    overlaps = [
        jaccard(a, b)
        for i, (_, a) in enumerate(advised)
        for _, b in advised[i + 1 :]
    ]
    counts = Counter(key for _, keys in advised for key in keys)
    return {
        "players_advised": len(advised),
        "pairs": len(overlaps),
        "mean_overlap": statistics.mean(overlaps) if overlaps else None,
        "identical_pairs": sum(1 for o in overlaps if o == 1.0),
        "distinct_claims": len(counts),
        "most_common": counts.most_common(5),
    }


def base_rate_specificity(profiles: list[PlayerProfile]) -> dict:
    """D2. A claim made to almost everyone is a description of the band."""
    advised = [claim_keys(p) for p in profiles]
    advised = [keys for keys in advised if keys]
    counts = Counter(key for keys in advised for key in keys)
    return {
        "shares": sorted(
            ((key, n / len(advised)) for key, n in counts.items()),
            key=lambda pair: pair[1],
            reverse=True,
        )
    }


def priority_counts(profiles: list[PlayerProfile]) -> Counter:
    """D3."""
    return Counter(len(p.plan.steps) if p.plan else 0 for p in profiles)


def detected_vs_advised(profiles: list[PlayerProfile]) -> list[tuple[str, int, int]]:
    """Separates "commonly true" from "commonly *detectable*".

    D2 flags a claim made to most players as a description rather than a
    diagnosis. But a claim can dominate the advice for a duller reason: its
    denominator is bigger, so it clears the confidence gate more often. S2
    measures against every long think; S1 measures against motif opportunities,
    of which there are few (step-07 counted ~3 skewer chances per player).

    If a kind is *detected* about as often as it is *advised*, it is common. If
    it is detected rarely but advised often, the gate is doing the selecting.
    """
    detected = Counter(f.claim.key() for p in profiles for f in p.findings)
    advised = Counter(key for p in profiles for key in claim_keys(p))
    return sorted(
        ((key, detected[key], advised[key]) for key in detected),
        key=lambda row: row[1],
        reverse=True,
    )


def groundedness(profiles: list[PlayerProfile]) -> dict:
    """D4. Every reported finding must cite a game, checked in the rendered text.

    Checked against what the player is actually shown rather than against the
    profile: a finding can hold evidence that the report fails to print, and it
    is the report that has to be grounded.
    """
    reported, cited = 0, 0
    for profile in profiles:
        if profile.plan is None:
            continue
        blocks = render(profile).split("How often")[1:]
        for block in blocks:
            reported += 1
            cited += "For example game" in block
    return {"reported": reported, "cited": cited}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles", required=True, type=Path)
    args = parser.parse_args()

    profiles = load_all(args.profiles)
    print(f"{len(profiles)} profiles\n")

    d1 = divergence(profiles)
    print("D1  inter-player divergence   (high overlap is the failure)")
    print(f"      players given advice      {d1['players_advised']}")
    print(f"      distinct claim kinds      {d1['distinct_claims']}")
    if d1["mean_overlap"] is not None:
        print(f"      mean pairwise overlap     {d1['mean_overlap']:.2f}")
        print(f"      identical pairs           {d1['identical_pairs']}/{d1['pairs']}")
    for key, n in d1["most_common"]:
        print(f"        {key:<44} {n}")

    print("\nD2  base-rate specificity     (a claim made to most players is a description)")
    for key, share in base_rate_specificity(profiles)["shares"][:5]:
        flag = "  <-- said to most players" if share > 0.5 else ""
        print(f"      {key:<44} {share:.0%}{flag}")

    print("\n    detected vs advised          (is it common, or just easier to detect?)")
    print(f"      {'claim':<44} {'found':>6} {'advised':>8}")
    for key, found, advised in detected_vs_advised(profiles)[:8]:
        print(f"      {key:<44} {found:>6} {advised:>8}")

    print("\nD3  priority count")
    for count, n in sorted(priority_counts(profiles).items()):
        flag = "  <-- over the limit" if count > MAX_PRIORITIES else ""
        print(f"      {count} priorities: {n} players{flag}")

    d4 = groundedness(profiles)
    print("\nD4  groundedness")
    if d4["reported"]:
        print(f"      reported findings citing a game   {d4['cited']}/{d4['reported']} "
              f"({d4['cited'] / d4['reported']:.0%})")
    else:
        print("      no reported findings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
