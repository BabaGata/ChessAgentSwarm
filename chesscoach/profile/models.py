"""The player profile: the artefact every agent reads and writes.

Specified in docs/notes/architecture.player-profile.md. Two rules shape all of it:

  * **claims are typed, never prose** -- a finding is a record with fields, so it
    can be compared across sessions, tested, ablated, and fed cheaply to a
    language model;
  * **every field earns its place by preventing a specific failure** that this
    project has already observed. Provenance carries depth because E01 showed
    labels shift with it; measurements carry a peer rate because E02 showed base
    rates are enormous; confidence carries a replication flag because E03
    produced a convincing effect that reversed on held-out players.

Everything here is immutable. Updates return new objects.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from enum import Enum

# v2 adds Measurement.baseline_rate. Building S2 showed that comparing a player
# against their own out-of-condition rate is a different claim from comparing
# them against their rating peers, and reusing `peer_rate` for it would have
# quietly overstated what the system knows.
#
# v3 makes plans checkable. `progress_sign` was written for a person to read and
# a machine cannot test it, so the falsifiability the plan claimed was only half
# real: PlanStep gains `target_rate`, the number the prose describes.
# CorpusRef gains `game_ids`, so a later check knows which games are new. And
# Plan gains `outcomes`, so a plan carries its own verdict -- a system that
# quietly drops its failed predictions is unfalsifiable.
SCHEMA_VERSION = 3

_Z = 1.96  # 95% normal quantile, for Wilson intervals


class ConfidenceTier(str, Enum):
    """How much the swarm is willing to assert. Only FOCUS and above reach the player."""

    NONE = "none"
    WATCH = "watch"
    FOCUS = "focus"
    PRIORITY = "priority"


class GapTypeHypothesis(str, Enum):
    """Why an error happened -- each needs a different remedy."""

    KNOWLEDGE = "knowledge"
    SKILL = "skill"
    PROCESS = "process"
    PSYCHOLOGICAL = "psychological"
    UNKNOWN = "unknown"


class DeterminedBy(str, Enum):
    """How the gap type was established. Never allowed to default silently."""

    INFERRED = "inferred"
    PROBED = "probed"


@dataclass(frozen=True)
class Claim:
    """What is being asserted, as data rather than a sentence.

    Context is part of the claim's identity, not a footnote: E03 found relevance
    is conditional, so "backward pawns" is not a claim while "backward pawns, in
    endgames, in rapid" is.
    """

    kind: str
    subject: str
    direction: str = "own"
    context: tuple[tuple[str, str], ...] = ()

    @classmethod
    def of(
        cls,
        kind: str,
        subject: str,
        direction: str = "own",
        context: dict[str, str] | None = None,
    ) -> Claim:
        """Build a claim, normalising context order so identity is stable."""
        pairs = tuple(sorted((context or {}).items()))
        return cls(kind=kind, subject=subject, direction=direction, context=pairs)

    @property
    def context_dict(self) -> dict[str, str]:
        return dict(self.context)

    def key(self) -> str:
        """Deterministic identity, used to build the finding id."""
        base = f"{self.kind}.{self.subject}.{self.direction}"
        if not self.context:
            return base
        qualifiers = ",".join(f"{name}={value}" for name, value in self.context)
        return f"{base}.{qualifiers}"


def wilson_interval(successes: int, total: int) -> tuple[float, float]:
    """Wilson score interval -- behaves sensibly at the small n we actually have."""
    if total <= 0:
        return (0.0, 0.0)
    p = successes / total
    denominator = 1 + _Z**2 / total
    centre = (p + _Z**2 / (2 * total)) / denominator
    margin = _Z * math.sqrt(p * (1 - p) / total + _Z**2 / (4 * total**2)) / denominator
    return (max(0.0, centre - margin), min(1.0, centre + margin))


@dataclass(frozen=True)
class Measurement:
    """How often, out of how much, and how that compares to the player's peers."""

    instances: int
    distinct_games: int
    games_with_data: int
    rate: float
    peer_rate: float | None = None
    baseline_rate: float | None = None
    ci95: tuple[float, float] | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.rate <= 1.0:
            raise ValueError(f"rate must be a proportion, got {self.rate}")
        if self.distinct_games > self.instances:
            raise ValueError(
                f"distinct_games ({self.distinct_games}) cannot exceed instances ({self.instances})"
            )
        if self.distinct_games > self.games_with_data:
            raise ValueError("distinct_games cannot exceed games_with_data")
        if self.ci95 is None:
            object.__setattr__(
                self, "ci95", wilson_interval(self.distinct_games, self.games_with_data)
            )

    @property
    def lift_vs_peer(self) -> float | None:
        """How unusual this player is among their rating peers.

        A claim true of everyone lifts by 1. Requires a reference population;
        None means we do not have one, not that the player is ordinary.
        """
        if not self.peer_rate:
            return None
        return self.rate / self.peer_rate

    @property
    def lift_vs_baseline(self) -> float | None:
        """How much worse this condition is than the same player's other moves.

        Deliberately distinct from `lift_vs_peer`: "worse than you usually are"
        and "worse than players at your level" are different claims, and only
        the second needs a reference corpus.
        """
        if not self.baseline_rate:
            return None
        return self.rate / self.baseline_rate


@dataclass(frozen=True)
class Provenance:
    """Which engine, at which depth, over which games, and when."""

    engine: str
    depth: int
    corpus_id: str
    analysed_at: str

    def __post_init__(self) -> None:
        if self.depth <= 0:
            raise ValueError(f"depth must be positive, got {self.depth}")


@dataclass(frozen=True)
class Evidence:
    """One position supporting a claim. Sampled uniformly, never cherry-picked."""

    game_id: str
    ply: int
    fen: str
    move_played: str | None = None
    better_move: str | None = None
    loss_wp: float | None = None
    note: str | None = None


@dataclass(frozen=True)
class Confidence:
    """Promotion tier and why it was reached. See architecture.confidence."""

    tier: ConfidenceTier
    replicated: bool = False
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class GapType:
    """The remedy depends entirely on this, so how it was decided is recorded."""

    hypothesis: GapTypeHypothesis
    determined_by: DeterminedBy
    probe_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class HistoryEntry:
    """What this finding looked like at an earlier point. Enables V7."""

    date: str
    tier: ConfidenceTier
    rate: float


@dataclass(frozen=True)
class Finding:
    """One thing the swarm believes about a player, with its evidence."""

    section: str
    claim: Claim
    measurement: Measurement
    provenance: Provenance
    confidence: Confidence
    gap_type: GapType
    evidence: tuple[Evidence, ...]
    status: str = "candidate"
    history: tuple[HistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        if not self.evidence:
            raise ValueError("a finding requires evidence: at least one position must be cited")

    @property
    def id(self) -> str:
        """Deterministic identity -- the same measurement always yields the same id."""
        return f"{self.section}.{self.claim.key()}"

    def with_status(self, status: str) -> Finding:
        return replace(self, status=status)

    def with_confidence(self, confidence: Confidence) -> Finding:
        return replace(self, confidence=confidence)


@dataclass(frozen=True)
class ProbeRecord:
    """A question put to the player, and what their answer implies."""

    id: str
    finding_id: str
    fen: str
    asks: str
    conditions: str = "untimed"
    player_move: str | None = None
    player_reason: str | None = None
    engine_best: str | None = None
    verdict: str | None = None
    inference: str | None = None
    asked_at: str | None = None


@dataclass(frozen=True)
class PlanStep:
    """One step of a coaching path.

    `progress_sign` and `check_after_games` are mandatory: a step nobody can
    check is unfalsifiable, and unfalsifiable coaching is what this project
    exists to avoid.
    """

    finding_id: str
    action: str
    why: str
    progress_sign: str
    check_after_games: int
    target_rate: float | None = None
    time_estimate_days: int | None = None

    def __post_init__(self) -> None:
        if not self.progress_sign.strip():
            raise ValueError("a plan step requires a progress_sign")
        if self.check_after_games <= 0:
            raise ValueError("a plan step requires a positive check_after_games")
        if self.target_rate is not None and not 0.0 <= self.target_rate <= 1.0:
            raise ValueError(f"target_rate must be a proportion, got {self.target_rate}")

    @property
    def claim_key(self) -> str:
        """The measurement this step is a prediction about."""
        return self.finding_id.split(".", 1)[1]


@dataclass(frozen=True)
class StepOutcome:
    """What actually happened to a prediction. Kept whether or not it flattered us."""

    finding_id: str
    status: str  # met | not_met | too_early | not_measurable
    target_rate: float
    previous_rate: float
    observed_rate: float | None
    games_since: int
    checked_at: str


@dataclass(frozen=True)
class Plan:
    created: str
    steps: tuple[PlanStep, ...] = ()
    outcomes: tuple[StepOutcome, ...] = ()


@dataclass(frozen=True)
class PlayerRef:
    source: str
    username: str
    ratings: dict[str, int] = field(default_factory=dict)
    band: str | None = None


@dataclass(frozen=True)
class CorpusRef:
    """Exactly which games produced the findings."""

    corpus_id: str
    n_games: int
    time_controls: tuple[str, ...] = ()
    date_range: tuple[str, str] | None = None
    # Recorded so a later progress check can tell which games are new.
    game_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlayerContext:
    """What only the player can tell us. See architecture.interaction step 2."""

    goals: str | None = None
    weekly_study_hours: float | None = None
    self_reported_weaknesses: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProfileHistoryEntry:
    date: str
    corpus_id: str
    finding_count: int


@dataclass(frozen=True)
class PlayerProfile:
    """The blackboard: everything the swarm knows about one player."""

    player: PlayerRef
    corpus: CorpusRef
    findings: tuple[Finding, ...] = ()
    probes: tuple[ProbeRecord, ...] = ()
    context: PlayerContext | None = None
    plan: Plan | None = None
    history: tuple[ProfileHistoryEntry, ...] = ()
    schema_version: int = SCHEMA_VERSION

    def with_findings(self, findings: tuple[Finding, ...]) -> PlayerProfile:
        return replace(self, findings=tuple(findings))

    def without_section(self, section: str) -> PlayerProfile:
        """Ablation is a filter, not a code branch -- see evaluation B3."""
        return replace(self, findings=tuple(f for f in self.findings if f.section != section))

    def section_findings(self, section: str) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.section == section)
