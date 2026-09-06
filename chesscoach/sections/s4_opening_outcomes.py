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
from chesscoach.development_norms import DevelopmentNorms
from chesscoach.confidence import MIN_GAMES_WITH_DATA, ClaimStats, assign_tier
from chesscoach.book_depth import BookDepthNorms
from chesscoach.opening_development import (
    LATE_CASTLING,
    OUT_OF_BOOK,
    PAWN_ERROR,
    REPEAT_MOVE,
    SLOW_DEVELOPMENT,
)
from chesscoach.opening_development import count as count_development
from chesscoach.openings import OpeningBook
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
    instance_moves,
    split_by_tier,
)

SECTION = "S4"

EARLY_ERROR = "early_error"

# Retired 2026-09-06, on the author's instruction: *"early_error retire this,
# this is not valueable measure."*
#
# It counts **any error inside the first 30 plies, split by colour**, and nothing
# else -- no theory, no book depth, no notion of understanding. The sentence it
# produced, *"You go wrong early as Black"*, implies a cause it never
# established, and the author rejected three of its firings on exactly that:
#
# > *"This is just missed tactics, not the result of lack of opening
# > understanding."*
# > *"This is not opening anymore."*
#
# Thirty plies is move 15, which is past the opening in most games, so the claim
# was also naming the wrong phase. The detector was never wrong about what it
# counted -- it was the claim built on top of it that could not be supported
# ([[experiments.e86-detector-audit]]).
#
# **What replaces it is already here.** `slow_development`, `late_castling`,
# `repeat_move` and `out_of_book` make opening claims that name a *behaviour* a
# player can act on, which is what D22 asked for.
#
# The code stays rather than being deleted, on the same reasoning as
# `s3_endgame_technique.ADVANTAGE_ERROR_RETIRED`: the tally is a cheap way to ask
# later whether errors inside the opening window are being explained by some
# other detector, which is a question about the swarm's coverage rather than a
# claim about a player.
EARLY_ERROR_RETIRED = True

# Loaded once. The book is 1.4 MB and the norms a few kB, and rebuilding either
# per player would dominate a section that otherwise costs nothing.
_BOOK: OpeningBook | None = None
_NORMS: DevelopmentNorms | None = None


def _references() -> tuple[OpeningBook, DevelopmentNorms] | tuple[None, None]:
    """The opening book and the strong-player expectation, or nothing.

    **Missing data must silence the claims, never fake them.** A player judged
    against an absent expectation would be judged against zero, and every game
    would read as late -- the L-046 shape, an empty case answering like a real
    one.
    """
    global _BOOK, _NORMS
    if _BOOK is None or _NORMS is None:
        try:
            _BOOK = OpeningBook.load()
            _NORMS = DevelopmentNorms.load()
        except (OSError, ValueError, KeyError):
            return None, None
    return _BOOK, _NORMS
OPENING_DISADVANTAGE = "opening_disadvantage"

ANY = "any"

_DEVELOPMENT_KINDS = (SLOW_DEVELOPMENT, LATE_CASTLING, REPEAT_MOVE, PAWN_ERROR,
                      OUT_OF_BOOK)

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
                    round(tally.cost_wp, 2)
                    if key.startswith(f"{EARLY_ERROR}.") or _is_development(key)
                    else None
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
        if not EARLY_ERROR_RETIRED:
            _tally(tallies, _key(EARLY_ERROR, ANY), observation)
            _tally(tallies, _key(EARLY_ERROR, _colour(observation)), observation)

    _count_disadvantage(tallies, early)
    _count_development(tallies, context)

    return _Counts(
        tallies=dict(tallies),
        games_with_data=len({o.game_id for o in early}),
    )


def _count_development(tallies: dict[str, _Tally], context: SectionContext) -> None:
    """Slow development, late castling and repeated piece moves.

    Design: [[design.opening-development-signals]]. These replace `early_error`,
    which the author marked 0/4 for explaining real errors wrongly. Unlike every
    other claim here they read the **moves** rather than the engine's opinion of
    them, so they cost nothing beyond the walk.

    The expectation is per opening and comes from players who know it
    ([[experiments.e59-strong-player-expectation]]); how often a player misses it
    is what the peer reference answers.
    """
    book, norms = _references()
    if book is None or norms is None:
        return

    counted = count_development(
        context.observations, context.corpus.username, book, norms
    )
    for raw, counts in counted.items():
        # Through `_key`, like every other claim in this section. The tallies
        # arrive as `slow_development.book` and every other claim in the system
        # is `kind.subject.own` -- so the detection sheet, which builds its
        # vocabulary from `measure()` and its fired set from `Claim.key()`,
        # subtracted one format from the other and listed four claims as NEVER
        # FIRED while they were reaching three of twelve plans.
        kind, subject = raw.split(".", 1)
        tally = tallies[_key(kind, subject)]
        tally.instances += counts.instances
        tally.opportunities += counts.opportunities
        tally.games_hit |= counts.games
        # Without these the claim is refused for having no evidence -- the right
        # refusal (V8), and exactly what silenced these claims when they were
        # first wired up: correct numbers, nothing citable, nothing said.
        tally.examples.extend(counts.examples)
        # The habit's own moves DO lose win probability, and summing what they
        # lost is the arbiter's own cost model rather than a second currency.
        # Without it these claims sort below every costed claim and reach no
        # plan at all ([[experiments.e60-peer-reference-rebuild]]).
        tally.cost_wp += counts.cost_wp


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


def _is_development(key: str) -> bool:
    """Claims priced by what their own moves cost, rather than left costless."""
    return any(key.startswith(f"{kind}.") for kind in _DEVELOPMENT_KINDS)


def _key(kind: str, subject: str) -> str:
    return Claim.of(kind=kind, subject=subject).key()


# --- assertion --------------------------------------------------------------


_BOOK_DEPTH: BookDepthNorms | None = None


def _out_of_book_baseline(context: SectionContext) -> float | None:
    """What this player's band and speed play outside theory, or None.

    **None silences the claim rather than defaulting it.** A player judged
    against an invented baseline is judged against a number nobody measured, and
    a blitz player judged against a rapid one is I-03 over again -- so the speed
    must be known and present, not assumed.

    The baseline is **standardised over the player's own speed mix**, the way
    `SectionContext._mixed` does it for peer rates: a blitz-heavy player is
    compared against a blitz-weighted baseline rather than whichever speed the
    corpus was labelled. `_mixed` itself cannot be reused because it refuses
    without a peer reference, and this claim's baseline is not in one -- so the
    weighting is repeated here rather than the coupling being invented.

    Speeds the baseline has never measured are skipped and their weight
    redistributed, so one unfamiliar game does not silence the claim.
    """
    global _BOOK_DEPTH
    if _BOOK_DEPTH is None:
        try:
            _BOOK_DEPTH = BookDepthNorms.load()
        except (OSError, ValueError, KeyError):
            return None
    if context.band is None:
        return None

    mix = context.corpus.speed_mix or (
        ((context.time_control, 1.0),) if context.time_control else ()
    )
    weighted = total = 0.0
    for speed, share in mix:
        value = _BOOK_DEPTH.share_for(context.band, speed)
        if value is None:
            continue
        weighted += share * value
        total += share
    return weighted / total if total else None


def _assess(key: str, counts: _Counts, context: SectionContext) -> Finding | None:
    tally = counts.tallies[key]
    kind, subject = key.split(".")[0], key.split(".")[1]

    if tally.opportunities == 0 or not tally.examples:
        return None

    # Everybody errs in the opening (R-14), and there is no meaningful
    # within-player baseline here -- "worse in the opening than in the
    # middlegame" is a different claim belonging to no section yet. So peers or
    # silence.
    #
    # `out_of_book` is the exception, and not because it is special: its
    # baseline needs **no engine**, so it lives in its own file rather than in a
    # peer reference that costs an hour to rebuild -- the same separation
    # `development-norms.json` already has ([[experiments.e76-leaving-theory]]).
    if kind == OUT_OF_BOOK:
        peer_rate = _out_of_book_baseline(context)
    else:
        peer_rate = context.peer_rate(key)
    if peer_rate is None:
        return None

    rate = tally.instances / tally.opportunities
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
        claim=Claim.of(kind=kind, subject=subject),
        measurement=Measurement(
            instances=tally.instances,
            instances_at=instance_moves(tally.examples),
            distinct_games=stats.distinct_games,
            games_with_data=counts.games_with_data,
            rate=round(rate, 4),
            baseline_rate=round(peer_rate, 4),
            peer_rate=round(peer_rate, 4),
            ci95=stats.ci95,
            # `early_error` and the development claims count moves that lost
            # win probability, so both can state a cost. `opening_disadvantage`
            # counts games the player was already worse in by move 15, which is
            # an outcome rather than a move that lost something -- it has no
            # measurable cost and must not be given one.
            cost_wp=(
                round(tally.cost_wp, 2)
                if kind == EARLY_ERROR or _is_development(key) else None
            ),
            peer_cost_per_game=(
                context.peer_cost_per_game(key)
                if kind == EARLY_ERROR or _is_development(key) else None
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
            tally, f"{SECTION}.{key}:{context.corpus.corpus_id}",
            kind == EARLY_ERROR or _is_development(key),
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
        # Only where the claim is about a *mistake*. `opening_disadvantage`
        # says the player was already worse by move 15, and the position it
        # cites is simply the last one in the window -- often a perfectly good
        # move, which printed as "you played c8e6 (c8e6 was better)".
        Evidence.from_observation(
            observation,
            better_move=observation.best_move if with_better_move else None,
            loss_dp=4,
        )
        for observation in chosen
    )
