"""S6 — squares and files: what the player's play lets the opponent keep.

Design: docs/notes/capacity.agents.s6-squares-and-files.md
Screen: docs/notes/experiments.e09-square-candidates.md

Built on two claims out of five candidates, because E09 screened them against 38
real players **before** the section was written -- the first time this project
has done that in the right order (L-023, learned on S5).

The claims here are judged across the **opponent's reply**, not the player's own
move: a knight settles and a rook arrives on their turn. The same framing S1 uses
for `allowed_motif`, and E09 showed it is not a detail -- measuring across the
player's move alone reported both rates as zero.
"""

from __future__ import annotations

import hashlib
import random
from collections import defaultdict
from dataclasses import dataclass, field

import chess

from chesscoach.analysis.observations import Observation
from chesscoach.confidence import MIN_GAMES_WITH_DATA, ClaimStats, assign_tier
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
    POOLED_SUBJECT,
    SectionContext,
    SectionReport,
    diagnosable,
    drop_redundant_aggregates,
    split_by_tier,
)
from chesscoach.squares import FEATURES, allowed

SECTION = "S6"

ALLOWS = "allows_square"

EVIDENCE_SAMPLE_SIZE = 4


@dataclass
class _Tally:
    instances: int = 0
    opportunities: int = 0
    games_hit: set[str] = field(default_factory=set)
    examples: list[Observation] = field(default_factory=list)


@dataclass
class _Counts:
    tallies: dict[str, _Tally]
    games_with_data: int


class S6SquaresAndFiles:
    """Diagnoses what a player's moves let the opponent establish permanently."""

    section = SECTION

    def findings(self, context: SectionContext) -> tuple[Finding, ...]:
        return self.report(context).findings

    def measure(self, context: SectionContext) -> tuple[ConditionMeasurement, ...]:
        counts = _count(context)
        return tuple(
            ConditionMeasurement(
                claim_key=key,
                instances=tally.instances,
                opportunities=tally.opportunities,
                distinct_games=len(tally.games_hit),
                games_with_data=counts.games_with_data,
            )
            for key, tally in sorted(counts.tallies.items())
        )

    def report(self, context: SectionContext) -> SectionReport:
        counts = _count(context)

        if counts.games_with_data < MIN_GAMES_WITH_DATA:
            return SectionReport(
                section=SECTION,
                insufficient_data=True,
                notes=(f"only {counts.games_with_data} games with diagnosable moves",),
            )

        candidates = [_assess(key, counts, context) for key in sorted(counts.tallies)]
        asserted, watched = split_by_tier(candidates)
        findings = drop_redundant_aggregates(asserted)
        return SectionReport(
            section=SECTION,
            findings=tuple(sorted(findings, key=lambda f: f.id)),
            sub_threshold=tuple(sorted(drop_redundant_aggregates(watched), key=lambda f: f.id)),
        )


# --- counting ---------------------------------------------------------------


def _count(context: SectionContext) -> _Counts:
    """One pass over the player's moves, looking through the opponent's answer."""
    by_ply = {(o.game_id, o.ply): o for o in context.observations}
    moves = diagnosable(context.player_observations())
    tallies: dict[str, _Tally] = defaultdict(_Tally)

    for observation in moves:
        # Two plies on is the player's next turn, so its `fen_before` is the
        # position after the opponent has answered.
        answered = by_ply.get((observation.game_id, observation.ply + 2))
        if answered is None:
            continue

        colour = chess.WHITE if observation.mover_is_white else chess.BLACK
        established = allowed(
            chess.Board(observation.fen_before), chess.Board(answered.fen_before), colour
        )

        _tally(tallies, _key(POOLED_SUBJECT), observation, bool(established))
        for feature in FEATURES:
            _tally(tallies, _key(feature), observation, feature in established)

    return _Counts(
        tallies=dict(tallies),
        games_with_data=len({o.game_id for o in moves}),
    )


def _tally(
    tallies: dict[str, _Tally], key: str, observation: Observation, occurred: bool
) -> None:
    tally = tallies[key]
    tally.opportunities += 1
    if not occurred:
        return
    tally.instances += 1
    tally.games_hit.add(observation.game_id)
    tally.examples.append(observation)


def _key(subject: str) -> str:
    return Claim.of(kind=ALLOWS, subject=subject).key()


# --- assertion --------------------------------------------------------------


def _assess(key: str, counts: _Counts, context: SectionContext) -> Finding | None:
    tally = counts.tallies[key]
    subject = key.split(".")[1]

    if tally.opportunities == 0 or not tally.examples:
        return None

    peer_rate = context.peer_rate(key)
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
        claim=Claim.of(kind=ALLOWS, subject=subject),
        measurement=Measurement(
            instances=tally.instances,
            distinct_games=stats.distinct_games,
            games_with_data=counts.games_with_data,
            rate=round(rate, 4),
            baseline_rate=round(peer_rate, 4),
            peer_rate=round(peer_rate, 4),
            ci95=stats.ci95,
            opportunities=tally.opportunities,
            peer_opportunities_per_game=context.peer_opportunities_per_game(key),
        ),
        provenance=context.provenance,
        # Giving up a square for something concrete is respectable; not noticing
        # it is not. The position cannot tell them apart, which makes this good
        # probe material (V9).
        gap_type=GapType(
            hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED
        ),
        confidence=Confidence(
            tier=decision.tier, replicated=stats.replicated, reasons=decision.reasons
        ),
        evidence=_sample_evidence(tally, f"{SECTION}.{key}:{context.corpus.corpus_id}"),
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
            # As in S5: no `better_move`. Showing the engine's preference would
            # imply the concession was the error, and nothing here establishes
            # that it cost anything.
            loss_wp=round(observation.loss_wp, 4),
        )
        for observation in chosen
    )
