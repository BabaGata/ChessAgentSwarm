"""S8 — attack and defence: how readily an attack builds against the player's king.

Design: docs/notes/capacity.agents.s8-attack-and-defence.md
Screen: docs/notes/experiments.e11-attack-candidates.md

**One claim.** E11 screened four candidates: the error-rate contrast under
pressure barely varies (1.46), the under-pressure rate is too thin (97
opportunities), and a broken pawn shield spreads well but cannot distinguish
advancing your own pawns from having them traded off. What is left is the
crossing itself -- the opponent bringing a third piece to bear on the king zone
when they had fewer before.

At 1.59 this is the **weakest spread the project has shipped**, just under
`long_think_error`'s 1.60. That is stated rather than hidden: S8 is a marginal
section by construction.
"""

from __future__ import annotations

import hashlib
import random
from collections import defaultdict
from dataclasses import dataclass, field

import chess

from chesscoach.analysis.observations import Observation
from chesscoach.confidence import MIN_GAMES_WITH_DATA, ClaimStats, assign_tier
from chesscoach.kingsafety import allowed_pressure
from chesscoach.peers import ConditionMeasurement
from chesscoach.profile.models import (
    Claim,
    Confidence,
    ConfidenceTier,
    DeterminedBy,
    Evidence,
    Finding,
    GapType,
    GapTypeHypothesis,
    Measurement,
    wilson_interval,
)
from chesscoach.sections.base import (
    SectionContext,
    SectionReport,
    diagnosable,
    split_by_tier,
)

SECTION = "S8"

ALLOWS_PRESSURE = "allows_pressure"
KING = "king"

EVIDENCE_SAMPLE_SIZE = 4


@dataclass
class _Tally:
    instances: int = 0
    opportunities: int = 0
    games_hit: set[str] = field(default_factory=set)
    examples: list[Observation] = field(default_factory=list)


@dataclass
class _Counts:
    tally: _Tally
    games_with_data: int


class S8AttackAndDefence:
    """Diagnoses how readily a player lets an attack assemble against their king."""

    section = SECTION

    def findings(self, context: SectionContext) -> tuple[Finding, ...]:
        return self.report(context).findings

    def measure(self, context: SectionContext) -> tuple[ConditionMeasurement, ...]:
        counts = _count(context)
        if counts.tally.opportunities == 0:
            return ()
        return (
            ConditionMeasurement(
                claim_key=_key(),
                instances=counts.tally.instances,
                opportunities=counts.tally.opportunities,
                distinct_games=len(counts.tally.games_hit),
                games_with_data=counts.games_with_data,
            ),
        )

    def report(self, context: SectionContext) -> SectionReport:
        counts = _count(context)

        if counts.games_with_data < MIN_GAMES_WITH_DATA:
            return SectionReport(
                section=SECTION,
                insufficient_data=True,
                notes=(f"only {counts.games_with_data} games with diagnosable moves",),
            )

        asserted, watched = split_by_tier([_assess(counts, context)])
        return SectionReport(section=SECTION, findings=asserted, sub_threshold=watched)


# --- counting ---------------------------------------------------------------


def _count(context: SectionContext) -> _Counts:
    by_ply = {(o.game_id, o.ply): o for o in context.observations}
    moves = diagnosable(context.player_observations())
    tally = _Tally()

    for observation in moves:
        # Two plies on is the player's next turn, so its position is the one
        # after the opponent has answered.
        answered = by_ply.get((observation.game_id, observation.ply + 2))
        if answered is None:
            continue

        colour = chess.WHITE if observation.mover_is_white else chess.BLACK
        tally.opportunities += 1
        if not allowed_pressure(
            chess.Board(observation.fen_before), chess.Board(answered.fen_before), colour
        ):
            continue
        tally.instances += 1
        tally.games_hit.add(observation.game_id)
        tally.examples.append(observation)

    return _Counts(tally=tally, games_with_data=len({o.game_id for o in moves}))


def _key() -> str:
    return Claim.of(kind=ALLOWS_PRESSURE, subject=KING).key()


# --- assertion --------------------------------------------------------------


def _assess(counts: _Counts, context: SectionContext) -> Finding | None:
    tally = counts.tally
    if tally.opportunities == 0 or not tally.examples:
        return None

    peer_rate = context.peer_rate(_key())
    if peer_rate is None:
        return None

    rate = tally.instances / tally.opportunities
    stats = ClaimStats(
        distinct_games=len(tally.games_hit),
        games_with_data=counts.games_with_data,
        rate=rate,
        baseline_rate=peer_rate,
        ci95=wilson_interval(tally.instances, tally.opportunities),
        replicated=len({o.game_id for o in tally.examples}) >= 2 and rate > peer_rate,
    )
    decision = assign_tier(stats)
    if decision.tier is ConfidenceTier.NONE:
        return None

    return Finding(
        section=SECTION,
        claim=Claim.of(kind=ALLOWS_PRESSURE, subject=KING),
        measurement=Measurement(
            instances=tally.instances,
            distinct_games=stats.distinct_games,
            games_with_data=counts.games_with_data,
            rate=round(rate, 4),
            baseline_rate=round(peer_rate, 4),
            peer_rate=round(peer_rate, 4),
            ci95=stats.ci95,
            opportunities=tally.opportunities,
            peer_opportunities_per_game=context.peer_opportunities_per_game(_key()),
        ),
        provenance=context.provenance,
        # Inviting an attack can be a deliberate provocation or an oversight, and
        # the position does not say which. A probe would.
        gap_type=GapType(
            hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED
        ),
        confidence=Confidence(
            tier=decision.tier, replicated=stats.replicated, reasons=decision.reasons
        ),
        evidence=_sample_evidence(tally, f"{SECTION}:{context.corpus.corpus_id}"),
    )


def _sample_evidence(tally: _Tally, seed: str) -> tuple[Evidence, ...]:
    """One example per game first, then fill. Seeded, so a profile reproduces."""
    rng = random.Random(hashlib.sha256(seed.encode()).hexdigest())

    by_game: dict[str, list[Observation]] = defaultdict(list)
    for observation in tally.examples:
        by_game[observation.game_id].append(observation)

    one_each = [rng.choice(sorted(v, key=lambda o: o.ply)) for _, v in sorted(by_game.items())]
    rng.shuffle(one_each)
    remaining = [o for o in tally.examples if o not in one_each]
    rng.shuffle(remaining)

    chosen = sorted(
        (one_each + remaining)[:EVIDENCE_SAMPLE_SIZE], key=lambda o: (o.game_id, o.ply)
    )
    return tuple(
        Evidence(
            game_id=observation.game_id,
            ply=observation.ply,
            fen=observation.fen_before,
            move_played=observation.move_played,
            # As in S5 and S6: no `better_move`. Nothing here establishes that
            # allowing the attack was the error.
            loss_wp=round(observation.loss_wp, 4),
        )
        for observation in chosen
    )
