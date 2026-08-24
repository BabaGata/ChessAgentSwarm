"""S5 — pawn-structure weaknesses. What the player's moves leave behind.

Design: docs/notes/capacity.agents.s5-pawn-structure.md

The first Tier 2 section, and two negative results shape it more than the
catalogue entry does.

**E02 / L-007:** the detectors work and detection is not a signal — isolated
pawns appear in 96 % of games. So this section counts **creation**, not presence.
Having an isolated pawn is mostly inherited from the opening and the opponent;
making one is a choice, and only choices are coachable.

**E03:** weighting a feature by its association with the player's own errors does
not work — pooled lifts 0.87-1.26, and the one striking effect reversed sign on
held-out players. So the justification here is **peer deviation** and nothing
else, per domain.sections' own re-scope note.

Which leaves a limitation worth stating in the code as well as the note: **this
section can say a player is unusual, not that it costs them anything.** It is the
only section whose subject is not itself a mistake — S1's missed tactics are
missed points, S2/S3/S4 all measure errors in a condition, but creating an
isolated pawn is a choice the literature dislikes and this project's own data has
never linked to lost points. The phrasing must not imply cost.
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
    instance_moves,
    split_by_tier,
)
from chesscoach.structure import conceded

SECTION = "S5"

CONCEDES = "concedes_weakness"

# How far above the peer rate a claim must sit before **this section** will
# assert it, on top of everything the confidence policy already requires.
#
# The general problem this originally patched -- FOCUS testing significance with
# no floor on magnitude -- is now fixed in the policy itself
# (`confidence.FOCUS_MARGIN`, question D12). This stays, and is stricter, for a
# reason that belongs to S5 alone: **E03 found no link between structural
# features and this band's errors**, so unlike every other section a finding here
# cannot claim to be costing the player anything. A claim that cannot say what it
# costs should have to be larger before it takes up one of a player's two slots.
#
# Measured across the 38-player reference, p90/median spread:
#
#     concedes_weakness.doubled   1.20      early_error.any       1.70
#     concedes_weakness.any       1.24      long_think_error      1.60
#     concedes_weakness.isolated  1.40      early_error.black     1.92
#     concedes_weakness.backward  1.85      endgame_error.any     1.70
#
# Players concede structure at very nearly the same rate. `backward` varies like
# the claims that are known to discriminate and fires regularly; `isolated`
# reaches this bar only for outliers; `doubled` and the pooled `any` reach it for
# nobody, and are measured, kept in the peer reference, and never asserted.
MIN_PEER_RATIO = 1.5

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


class S5PawnStructure:
    """Diagnoses which structural weaknesses a player's own moves create."""

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
    """One pass over the player's moves, comparing structure before and after.

    The position after the player's move is the `fen_before` of the next
    observation, so this costs no engine calls -- the same property that makes
    S1 free.
    """
    following = {(o.game_id, o.ply): o for o in context.observations}
    moves = diagnosable(context.player_observations())
    tallies: dict[str, _Tally] = defaultdict(_Tally)

    for observation in moves:
        after = following.get((observation.game_id, observation.ply + 1))
        if after is None:
            continue  # last move of the game: nothing to compare against

        colour = chess.WHITE if observation.mover_is_white else chess.BLACK
        created = conceded(
            chess.Board(observation.fen_before), chess.Board(after.fen_before), colour
        )

        _tally(tallies, _key(POOLED_SUBJECT), observation, bool(created))
        for feature in sorted(created):
            _tally(tallies, _key(feature), observation, True)
        for feature in _absent(created):
            _tally(tallies, _key(feature), observation, False)

    return _Counts(
        tallies=dict(tallies),
        games_with_data=len({o.game_id for o in moves}),
    )


def _absent(created: frozenset[str]) -> tuple[str, ...]:
    """Every feature not created here still had the chance to be.

    The denominator for each feature is all the player's moves, not only the
    ones that went wrong -- otherwise the rate would be 100 % by construction.
    """
    from chesscoach.structure import FEATURES

    return tuple(f for f in FEATURES if f not in created)


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
    return Claim.of(kind=CONCEDES, subject=subject).key()


# --- assertion --------------------------------------------------------------


def _assess(key: str, counts: _Counts, context: SectionContext) -> Finding | None:
    tally = counts.tallies[key]
    subject = key.split(".")[1]

    if tally.opportunities == 0 or not tally.examples:
        return None

    # Peers or silence. Everyone has these structures (E02: 96 % of games), so
    # only being unusual is a diagnosis -- and unlike S1 there is no useful
    # within-player baseline, since the features are not comparable to each
    # other.
    peer_rate = context.peer_rate(key)
    if peer_rate is None:
        return None

    rate = tally.instances / tally.opportunities
    if rate < peer_rate * MIN_PEER_RATIO:
        return None

    stats = ClaimStats(
        distinct_games=len(tally.games_hit),
        games_with_data=counts.games_with_data,
        corpus_games=context.corpus.n_games,
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
        claim=Claim.of(kind=CONCEDES, subject=subject),
        measurement=Measurement(
            instances=tally.instances,
            instances_at=instance_moves(tally.examples),
            distinct_games=stats.distinct_games,
            games_with_data=counts.games_with_data,
            rate=round(rate, 4),
            baseline_rate=round(peer_rate, 4),
            peer_rate=round(peer_rate, 4),
            ci95=stats.ci95,
            # Recorded even though this section can never price itself, so the
            # field means "not measured" nowhere and "no cost to compare"
            # everywhere it is absent.
            opportunities=tally.opportunities,
            peer_opportunities_per_game=context.peer_opportunities_per_game(key),
        ),
        provenance=context.provenance,
        # Conceding a structure deliberately -- for the bishop pair, for open
        # lines -- is respectable, and conceding it without noticing is not.
        # Nothing in the position distinguishes them, which is why this is the
        # section where a probe would earn the most.
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
        # Deliberately no `better_move`: the engine's preferred move is not
        # evidence about a structural choice, and showing it would imply the
        # concession was the error -- which E03 says we cannot claim.
        Evidence.from_observation(observation, better_move=None, loss_dp=4)
        for observation in chosen
    )
