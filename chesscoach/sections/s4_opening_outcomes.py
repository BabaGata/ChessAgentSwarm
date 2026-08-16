"""S4 — opening repertoire outcomes. What the openings cost, not what to play.

Design: docs/notes/capacity.agents.s4-opening-outcomes.md

Three claims, and the shape of them is the design. **Subdivision is by colour,
not by opening name**: a 24-game corpus spread over a dozen ECO codes gives every
per-opening claim two games behind it, and L-022 is the record of what that
produces — five material classes in S3 that fired for nobody. Colour is a real
repertoire boundary, it is directly actionable, and it is a two-way split, which
is the most the evidence supports.

The section deliberately says nothing about *what to play instead*. That is a
recommendation problem rather than a diagnosis, and it is where a language model
produces its most confident nonsense.
"""

from __future__ import annotations

import hashlib
import random
from collections import defaultdict
from dataclasses import dataclass, field

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
    SectionContext,
    SectionReport,
    diagnosable,
    drop_redundant_aggregates,
    split_by_tier,
)

SECTION = "S4"

EARLY_ERROR = "early_error"
OPENING_DISADVANTAGE = "opening_disadvantage"

ANY = "any"

# Move 15, in plies. The catalogue's own figure and conventional rather than
# derived -- the real end of the opening varies by opening and by player. Named
# here so that if it is ever tuned, the tuning is visible rather than buried.
OPENING_END_PLY = 30

# Clearly worse coming out of the opening, short of decided. Matches S3's
# ADVANTAGE_CP so that "clearly better" and "clearly worse" mean the same
# distance in both sections.
OPENING_DISADVANTAGE_CP = 150

EVIDENCE_SAMPLE_SIZE = 4


@dataclass
class _Tally:
    instances: int = 0
    opportunities: int = 0
    games_hit: set[str] = field(default_factory=set)
    examples: list[Observation] = field(default_factory=list)
    cost_wp: float = 0.0


@dataclass
class _Counts:
    tallies: dict[str, _Tally]
    games_with_data: int


class S4OpeningOutcomes:
    """Diagnoses what a player's openings cost them, in their own games."""

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
                # Only `early_error` prices itself. `opening_disadvantage`
                # counts outcomes, not mistakes, and has no cost to pool.
                cost_wp=(
                    round(tally.cost_wp, 2) if key.startswith(f"{EARLY_ERROR}.") else None
                ),
            )
            for key, tally in sorted(counts.tallies.items())
        )

    def report(self, context: SectionContext) -> SectionReport:
        counts = _count(context)

        if counts.games_with_data < MIN_GAMES_WITH_DATA:
            return SectionReport(
                section=SECTION,
                insufficient_data=True,
                notes=(
                    f"only {counts.games_with_data} games reached a diagnosable opening position",
                ),
            )

        candidates = [_assess(key, counts, context) for key in sorted(counts.tallies)]
        asserted, watched = split_by_tier(candidates)
        kept = drop_redundant_aggregates(asserted)
        return SectionReport(
            section=SECTION,
            findings=tuple(sorted(kept, key=lambda f: f.id)),
            sub_threshold=tuple(sorted(drop_redundant_aggregates(watched), key=lambda f: f.id)),
        )


# --- counting ---------------------------------------------------------------


def _count(context: SectionContext) -> _Counts:
    """One pass over the player's diagnosable moves inside the opening window."""
    early = tuple(
        o for o in diagnosable(context.player_observations()) if o.ply <= OPENING_END_PLY
    )
    tallies: dict[str, _Tally] = defaultdict(_Tally)

    for observation in early:
        _tally(tallies, _key(EARLY_ERROR, ANY), observation)
        _tally(tallies, _key(EARLY_ERROR, _colour(observation)), observation)

    _count_disadvantage(tallies, early)

    return _Counts(
        tallies=dict(tallies),
        games_with_data=len({o.game_id for o in early}),
    )


def _count_disadvantage(tallies: dict[str, _Tally], early: tuple[Observation, ...]) -> None:
    """One instance per game, judged at the last position inside the window.

    The denominator is **games**, not moves: "how often do you come out of the
    opening already worse" is a question about games. That makes it the first
    claim here to go quiet on a small corpus, which is stated rather than fixed.

    A game that ended before move 15 was decided in the opening, so the last
    position seen is the right one to judge it by.
    """
    last_in_window: dict[str, Observation] = {}
    for observation in early:
        seen = last_in_window.get(observation.game_id)
        if seen is None or observation.ply > seen.ply:
            last_in_window[observation.game_id] = observation

    tally = tallies[_key(OPENING_DISADVANTAGE, ANY)]
    for observation in last_in_window.values():
        tally.opportunities += 1
        if _score_for_mover(observation) <= -OPENING_DISADVANTAGE_CP:
            tally.instances += 1
            tally.games_hit.add(observation.game_id)
            tally.examples.append(observation)


def _tally(tallies: dict[str, _Tally], key: str, observation: Observation) -> None:
    tally = tallies[key]
    tally.opportunities += 1
    if observation.label is None:
        return
    tally.instances += 1
    tally.games_hit.add(observation.game_id)
    tally.examples.append(observation)
    tally.cost_wp += observation.loss_wp


def _colour(observation: Observation) -> str:
    return "white" if observation.mover_is_white else "black"


def _score_for_mover(observation: Observation) -> int:
    """`score_cp_before` is white-relative; a black player's advantage is negative."""
    score = observation.score_cp_before
    return score if observation.mover_is_white else -score


def _key(kind: str, subject: str) -> str:
    return Claim.of(kind=kind, subject=subject).key()


# --- assertion --------------------------------------------------------------


def _assess(key: str, counts: _Counts, context: SectionContext) -> Finding | None:
    tally = counts.tallies[key]
    kind, subject = key.split(".")[0], key.split(".")[1]

    if tally.opportunities == 0 or not tally.examples:
        return None

    # Everybody errs in the opening (R-14), and there is no meaningful
    # within-player baseline here -- "worse in the opening than in the
    # middlegame" is a different claim belonging to no section yet. So peers or
    # silence.
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
        claim=Claim.of(kind=kind, subject=subject),
        measurement=Measurement(
            instances=tally.instances,
            distinct_games=stats.distinct_games,
            games_with_data=counts.games_with_data,
            rate=round(rate, 4),
            baseline_rate=round(peer_rate, 4),
            peer_rate=round(peer_rate, 4),
            ci95=stats.ci95,
            # Only `early_error` counts mistakes. `opening_disadvantage` counts
            # games the player was already worse in by move 15, which is an
            # outcome rather than a move that lost something — so it has no
            # measurable cost and must not be given one.
            cost_wp=round(tally.cost_wp, 2) if kind == EARLY_ERROR else None,
            peer_cost_per_game=(
                context.peer_cost_per_game(key) if kind == EARLY_ERROR else None
            ),
            opportunities=tally.opportunities,
            peer_opportunities_per_game=context.peer_opportunities_per_game(key),
        ),
        provenance=context.provenance,
        # "Does not know this opening" and "knows it and went wrong" need
        # opposite remedies -- learn a line, versus stop rushing -- so guessing
        # between them would be worse here than usual. Only a probe can say.
        gap_type=GapType(
            hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED
        ),
        confidence=Confidence(
            tier=decision.tier, replicated=stats.replicated, reasons=decision.reasons
        ),
        evidence=_sample_evidence(
            tally, f"{SECTION}.{key}:{context.corpus.corpus_id}", kind == EARLY_ERROR
        ),
    )


def _sample_evidence(tally: _Tally, seed: str, with_better_move: bool) -> tuple[Evidence, ...]:
    """One example per game first, then fill. Seeded, so a profile reproduces.

    Spreading across games matters for how a claim reads: three examples from
    one game invite the reader to dismiss a pattern as one bad day, which is the
    mirror image of cherry-picking and just as misleading.
    """
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
            # Only where the claim is about a *mistake*. `opening_disadvantage`
            # says the player was already worse by move 15, and the position it
            # cites is simply the last one in the window -- often a perfectly
            # good move, which printed as "you played c8e6 (c8e6 was better)".
            better_move=observation.best_move if with_better_move else None,
            loss_wp=round(observation.loss_wp, 4),
        )
        for observation in chosen
    )
