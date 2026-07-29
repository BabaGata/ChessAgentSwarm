"""Scoring an agent's findings against a planted weakness.

Two questions carry equal weight:

  * **sensitivity** -- did it find the weakness that was actually planted?
  * **specificity** -- did it refrain from asserting anything else?

The second is the one usually skipped, and the one that matters most for a
coach. A detector that reports everything finds every planted weakness and is
worthless, and E02 showed how easy it is to produce claims that are true and
useless (R-14).

Only findings the player would actually be shown count as spurious: `watch` is
internal, so it cannot mislead anyone.
"""

from __future__ import annotations

from dataclasses import dataclass

from chesscoach.evaluation.planted import WeaknessSpec
from chesscoach.profile.models import ConfidenceTier, Finding

# Which claim kinds count as having found each planted weakness.
_MATCHING_KINDS: dict[str, frozenset[str]] = {
    "time_pressure": frozenset({"time_pressure_error", "clock_management"}),
    "phase": frozenset({"phase_error_excess"}),
    "uniform": frozenset({"error_rate_excess", "blunder_rate_excess"}),
}

# Tiers that reach the player, per architecture.confidence.
_ASSERTED = frozenset({ConfidenceTier.FOCUS, ConfidenceTier.PRIORITY})


def matches_spec(finding: Finding, spec: WeaknessSpec) -> bool:
    """Does this finding name the weakness that was planted?"""
    kinds = _MATCHING_KINDS.get(spec.kind, frozenset())
    if finding.claim.kind not in kinds:
        return False
    if spec.kind == "phase":
        return finding.claim.subject == spec.phase
    return True


@dataclass(frozen=True)
class ScoreCard:
    """The result of putting one agent in front of one planted weakness."""

    planted_kind: str
    matched: tuple[str, ...]
    spurious: tuple[str, ...]
    asserted_count: int
    insufficient_data: bool = False

    @property
    def detected(self) -> bool:
        return bool(self.matched)

    @property
    def spurious_count(self) -> int:
        return len(self.spurious)

    @property
    def precision(self) -> float | None:
        """Share of asserted findings that were the planted weakness."""
        if self.asserted_count == 0:
            return None
        return len(self.matched) / self.asserted_count

    def summary(self) -> str:
        if self.detected:
            verdict = "found"
        elif self.insufficient_data:
            # Declining for lack of evidence is correct behaviour, not a failure.
            # Reporting it as a miss would penalise the agent for being honest.
            verdict = "DECLINED (insufficient data)"
        else:
            verdict = "MISSED"
        return (
            f"planted {self.planted_kind}: {verdict}; "
            f"{self.spurious_count} spurious of {self.asserted_count} asserted"
        )


def score_findings(
    findings: tuple[Finding, ...], spec: WeaknessSpec, insufficient_data: bool = False
) -> ScoreCard:
    """Score a set of findings against the weakness that was planted."""
    asserted = tuple(f for f in findings if f.confidence.tier in _ASSERTED)
    matched = tuple(f.id for f in asserted if matches_spec(f, spec))
    spurious = tuple(f.id for f in asserted if not matches_spec(f, spec))

    return ScoreCard(
        planted_kind=spec.kind,
        matched=matched,
        spurious=spurious,
        asserted_count=len(asserted),
        insufficient_data=insufficient_data,
    )
