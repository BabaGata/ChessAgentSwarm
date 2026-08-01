"""S2 — decision process and clock behaviour. The swarm's first agent.

Design: docs/notes/capacity.agents.s2-decision-process.md

It answers a question no amount of chess knowledge answers: **under what
conditions do this player's decisions get worse?** Not why a move was wrong —
that belongs to S1 — but whether the clock, or the absence of thought, or an
unusually long think, is what the errors have in common.

Entirely deterministic. The signal is arithmetic over timestamps the analysis
core already extracted, so the agent costs nothing to run and its output is
reproducible to the last sampled position.
"""

from __future__ import annotations

import hashlib
import random
import statistics
from dataclasses import dataclass
from typing import Callable

from chesscoach.analysis.observations import Observation
from chesscoach.confidence import MIN_GAMES_WITH_DATA, ClaimStats, assign_tier
from chesscoach.evaluation.splithalf import split_half_check
from chesscoach.peers import ConditionMeasurement
from chesscoach.profile.models import (
    Claim,
    Confidence,
    DeterminedBy,
    Evidence,
    Finding,
    GapType,
    GapTypeHypothesis,
    Measurement,
    wilson_interval,
)
from chesscoach.sections.base import SectionContext, SectionReport, diagnosable

SECTION = "S2"

# Provisional thresholds -- see the design note. The time-pressure threshold is
# absolute, which is a known limitation: 60 seconds means something different in
# a 3+0 game than in a 15+10 one.
TIME_PRESSURE_SECONDS = 60.0
INSTANT_MOVE_SECONDS = 2.0
LONG_THINK_MULTIPLE = 3.0

# Evidence is sampled, not selected: showing the worst examples produces a coach
# who exaggerates and evidence unrepresentative of its own claim.
EVIDENCE_SAMPLE_SIZE = 4


@dataclass(frozen=True)
class Condition:
    """One diagnosable circumstance: a name and a test for it."""

    kind: str
    subject: str
    applies: Callable[[Observation], bool]
    describe: Callable[[Observation], str]
    selection_confounded: bool = False
    """True when the condition is *selected by* the same thing that causes the error.

    A long think happens because the position is hard, and hard positions produce
    errors — so an elevated error rate after long thinks says little about the
    player and much about chess. Comparing against the player's own baseline
    cannot separate the two; only a rating-peer population can.

    Confirmed empirically in M5: four of six real players showed this at a
    similar magnitude, which is the signature of a base rate, not a weakness.
    Such conditions are measured but withheld until a peer baseline exists.
    """


class S2DecisionProcess:
    """Diagnoses when a player's decisions get worse, rather than why."""

    section = SECTION

    def findings(self, context: SectionContext) -> tuple[Finding, ...]:
        return self.report(context).findings

    def measure(self, context: SectionContext) -> tuple[ConditionMeasurement, ...]:
        """Raw per-condition rates, with no judgement applied.

        This is what building a peer reference needs: every player's numbers,
        including the unremarkable ones, and without the confidence policy
        deciding anything.
        """
        observations = self._eligible(context)
        games_with_data = len({o.game_id for o in observations})

        measurements = []
        for condition in _conditions(observations):
            inside = tuple(o for o in observations if condition.applies(o))
            errors = tuple(o for o in inside if o.is_error)
            measurements.append(
                ConditionMeasurement(
                    claim_key=Claim.of(kind=condition.kind, subject=condition.subject).key(),
                    instances=len(errors),
                    opportunities=len(inside),
                    distinct_games=len({o.game_id for o in errors}),
                    games_with_data=games_with_data,
                )
            )
        return tuple(measurements)

    @staticmethod
    def _eligible(context: SectionContext) -> tuple[Observation, ...]:
        """Diagnosable moves that also carry a clock reading, which S2 needs."""
        return tuple(
            o for o in diagnosable(context.player_observations()) if o.seconds_spent is not None
        )

    def report(self, context: SectionContext) -> SectionReport:
        observations = self._eligible(context)
        # Games with data **for the section** -- games in which this player made
        # any timed, competitive move after the opening. Deliberately not "games
        # in which the condition occurred": gating each condition on its own
        # frequency would make a rare-but-severe condition permanently
        # unassertable, however badly the player handled it. How often the
        # condition arises is already carried by `distinct_games` and the rate.
        games_with_data = len({o.game_id for o in observations})

        if games_with_data < MIN_GAMES_WITH_DATA:
            return SectionReport(
                section=SECTION,
                insufficient_data=True,
                notes=(f"only {games_with_data} games with timed moves after the opening",),
            )

        findings: list[Finding] = []
        notes: list[str] = []
        for condition in _conditions(observations):
            finding, note = self._assess(condition, observations, context, games_with_data)
            if finding is not None:
                findings.append(finding)
            if note is not None:
                notes.append(note)

        return SectionReport(
            section=SECTION,
            findings=tuple(sorted(findings, key=lambda f: f.id)),
            notes=tuple(notes),
        )

    def _assess(
        self,
        condition: Condition,
        observations: tuple[Observation, ...],
        context: SectionContext,
        games_with_data: int,
    ) -> tuple[Finding | None, str | None]:
        """Measure one condition and decide whether it may be asserted.

        Returns the finding, if any, and a note explaining anything withheld.
        """
        inside = tuple(o for o in observations if condition.applies(o))
        outside = tuple(o for o in observations if not condition.applies(o))
        if not inside:
            return None, None

        errors = tuple(o for o in inside if o.is_error)
        rate = len(errors) / len(inside)
        baseline = (sum(1 for o in outside if o.is_error) / len(outside)) if outside else 0.0

        claim = Claim.of(kind=condition.kind, subject=condition.subject)
        peer_rate = context.peer_rate(claim.key())

        if condition.selection_confounded and peer_rate is None:
            # Measured, and deliberately not said. Without a rating-peer
            # baseline this cannot be distinguished from something every player
            # does, and asserting it would be true-but-useless output (R-14).
            return None, (
                f"{condition.kind} measured at {rate:.1%} vs {baseline:.1%} own baseline, "
                "withheld: needs a rating-peer baseline to separate this player from the base rate"
            )

        # For a condition selected by the same thing that causes the error, the
        # player's own baseline answers the wrong question; only the population
        # rate is meaningful. Elsewhere the self-baseline is the comparison and
        # the peer rate is recorded alongside it.
        comparison = peer_rate if condition.selection_confounded else baseline

        stats = ClaimStats(
            distinct_games=len({o.game_id for o in errors}),
            games_with_data=games_with_data,
            rate=rate,
            baseline_rate=comparison,
            ci95=wilson_interval(len(errors), len(inside)),
            replicated=self._replicates(condition, inside, comparison),
        )
        decision = assign_tier(stats)

        if not decision.is_assertable:
            return None, None

        return Finding(
            section=SECTION,
            claim=claim,
            measurement=Measurement(
                instances=len(errors),
                distinct_games=stats.distinct_games,
                games_with_data=stats.games_with_data,
                rate=round(rate, 4),
                baseline_rate=round(baseline, 4),
                peer_rate=round(peer_rate, 4) if peer_rate is not None else None,
                ci95=stats.ci95,
            ),
            provenance=context.provenance,
            confidence=Confidence(
                tier=decision.tier, replicated=stats.replicated, reasons=decision.reasons
            ),
            gap_type=GapType(
                hypothesis=GapTypeHypothesis.PROCESS, determined_by=DeterminedBy.INFERRED
            ),
            evidence=_sample_evidence(
                errors, condition, seed_key=f"{SECTION}.{claim.key()}:{context.corpus.corpus_id}"
            ),
        ), None

    @staticmethod
    def _replicates(
        condition: Condition, inside: tuple[Observation, ...], baseline: float
    ) -> bool:
        """Does the condition hold up across a split of the player's own games?"""
        by_game: dict[str, list[Observation]] = {}
        for observation in inside:
            by_game.setdefault(observation.game_id, []).append(observation)

        def measure(game_ids):
            selected = [o for game_id in game_ids for o in by_game.get(game_id, ())]
            return sum(1 for o in selected if o.is_error), len(selected)

        return split_half_check(by_game.keys(), measure, reference_rate=baseline).replicated


def _conditions(observations: tuple[Observation, ...]) -> tuple[Condition, ...]:
    """The circumstances S2 knows how to look for.

    The long-think threshold is relative to this player's own median, so it means
    the same thing for a fast player and a slow one.
    """
    think_times = [o.seconds_spent for o in observations if o.seconds_spent is not None]
    median_think = statistics.median(think_times) if think_times else 0.0
    long_think_seconds = max(median_think * LONG_THINK_MULTIPLE, 1.0)

    return (
        Condition(
            kind="time_pressure_error",
            subject="clock",
            applies=lambda o: (o.clock_after or 0.0) <= TIME_PRESSURE_SECONDS,
            describe=lambda o: f"{o.clock_after:.0f}s left on the clock",
        ),
        Condition(
            kind="instant_move_error",
            subject="instant_moves",
            applies=lambda o: (o.seconds_spent or 0.0) <= INSTANT_MOVE_SECONDS,
            describe=lambda o: f"played in {o.seconds_spent:.1f}s",
        ),
        Condition(
            kind="long_think_error",
            subject="long_think",
            applies=lambda o: (o.seconds_spent or 0.0) >= long_think_seconds,
            describe=lambda o: f"{o.seconds_spent:.0f}s spent, then a mistake",
            selection_confounded=True,
        ),
    )


def _sample_evidence(
    errors: tuple[Observation, ...], condition: Condition, seed_key: str
) -> tuple[Evidence, ...]:
    """A uniform sample of the supporting positions, reproducibly chosen.

    Seeded from a stable hash rather than Python's `hash`, which is randomised
    per process and would make the evidence differ between runs.
    """
    digest = hashlib.sha256(seed_key.encode("utf-8")).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))

    ordered = sorted(errors, key=lambda o: (o.game_id, o.ply))
    chosen = sorted(
        rng.sample(ordered, min(EVIDENCE_SAMPLE_SIZE, len(ordered))),
        key=lambda o: (o.game_id, o.ply),
    )

    return tuple(
        Evidence(
            game_id=o.game_id,
            ply=o.ply,
            fen=o.fen_before,
            move_played=o.move_played,
            better_move=o.best_move,
            loss_wp=round(o.loss_wp, 1),
            note=condition.describe(o),
        )
        for o in chosen
    )
