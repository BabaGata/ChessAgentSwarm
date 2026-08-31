"""S3 — endgame technique and advantage retention.

Design: docs/notes/capacity.agents.s3-endgame-technique.md

Where a player's errors concentrate once material comes off, and whether they go
wrong when they are on top. Not *which* tactic they missed (S1) and not *whether
the clock caused it* (S2) — S3 owns **where** and **under what advantage**.

Two properties are load-bearing.

**The aggregate exists because of a measurement.** E08 found the swarm silent
for 29 of 38 real players, because per-thing denominators are too thin to clear
the confidence gate. `endgame_error.any` pools every class so that this section
can speak at all; the per-class claims refine it when the data allows.

**"Conversion" is not what is measured, and the name matters.**
docs/notes/domain.sections.md asks S3 for conversion of winning positions, but
`diagnosable()` excludes anything beyond DECIDED_CP because win probability
compresses at the extremes (L-009) -- errors in won positions are both cheap to
make and nearly invisible to measure. Overriding that would manufacture a
conversion rate out of measurement artefact. So this measures **advantage
retention**: going wrong while clearly better but not yet winning.
"""

from __future__ import annotations

import hashlib
import random
from collections import defaultdict
from dataclasses import dataclass, field

import chess

from chesscoach.analysis.observations import Observation
from chesscoach.tactics import detect_motifs
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
    instance_moves,
    split_by_tier,
)

SECTION = "S3"

ENDGAME_ERROR = "endgame_error"

# How many losing moves in a row make a run, and how wide a window they may be
# spread over. The author:
#
# > *"Endgame error should be calculated just when there are big drops of the
# > advantage in a few consecutive moves. So that it can be seen that the player
# > is imprecise one move after the other and lacks knowledge of how to play the
# > endgame."*
#
# One bad move in an endgame is a mistake; three in a row is not knowing the
# endgame, and only the second is what this claim is for. The window is in the
# player's OWN moves -- their word was "moves" -- so an opponent's reply between
# two of them does not break the run.
RUN_LENGTH = 3
RUN_WINDOW = 4
ADVANTAGE_ERROR = "advantage_error"

# **Retired 2026-08-29, not deleted.** The author, having marked all five sampled
# instances "cannot tell": *"Advantage error should be totally removed, or kept
# for future but not used nor calculated. It is completely uninformative."*
#
# It fired 182 times across six players -- the second-commonest claim in the
# system -- and named a circumstance ("you go wrong when you are winning") that
# no player can act on. Every error it counted was already counted by the
# detector that explains it.
#
# The code stays because the author named a future use: as a way to check
# whether the ORIGIN of such errors is detected elsewhere -- improper defence
# and the like -- which is a question about the swarm's coverage rather than a
# claim about a player. Deleting the section would make that question expensive
# to ask again.
#
# → [[design.detectors-name-consequences]] § 2
ADVANTAGE_ERROR_RETIRED = True

# The pooled claim. Named rather than absent so a report can say "endgames"
# without implying a particular material class.
ANY = "any"
CLEAR = "clear"

# Clearly better, but short of DECIDED_CP where the labels stop meaning much.
# The window is deliberately narrow: it is the range in which a player still has
# something to lose and the measurement still has resolution.
ADVANTAGE_CP = 150

EVIDENCE_SAMPLE_SIZE = 4


@dataclass
class _Tally:
    instances: int = 0
    opportunities: int = 0
    games_hit: set[str] = field(default_factory=set)
    examples: list[Observation] = field(default_factory=list)
    # Every instance here is a mistake, so the win probability lost on them is
    # what the claim costs (D5).
    cost_wp: float = 0.0


@dataclass
class _Counts:
    tallies: dict[str, _Tally]
    games_with_data: int
    endgame_games: int


def material_class(fen: str) -> str:
    """Which kind of endgame this is, by what is still on the board.

    Coarse on purpose. Finer classes -- by count, by colour, by bishop pair --
    are more useful to a coach and would fire for nobody, which is the failure
    E08 measured. Queens dominate the naming because they make a position
    volatile regardless of what else remains.
    """
    board = chess.Board(fen)

    def count(piece_type: int) -> int:
        return len(board.pieces(piece_type, chess.WHITE)) + len(
            board.pieces(piece_type, chess.BLACK)
        )

    if count(chess.QUEEN):
        return "queen"

    rooks = count(chess.ROOK)
    minors = count(chess.BISHOP) + count(chess.KNIGHT)
    if rooks and minors:
        return "rook_minor"
    if rooks:
        return "rook"
    if minors:
        return "minor"
    return "pawn"


class S3EndgameTechnique:
    """Diagnoses where a player's endgame errors concentrate."""

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
                cost_wp=round(tally.cost_wp, 2),
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
        sub_threshold = drop_redundant_aggregates(watched)
        # Said even when the advantage claim had plenty to work with, because
        # silence about endgames would otherwise read as "your endgames are
        # fine" when the truth is that few of the player's games produce a
        # measurable one -- most endgames arrive already decided.
        notes = ()
        if counts.endgame_games < MIN_GAMES_WITH_DATA:
            notes = (
                f"only {counts.endgame_games} games reached an endgame that was still "
                "competitive enough to diagnose; endgame findings are not available",
            )
        return SectionReport(
            section=SECTION,
            findings=tuple(sorted(findings, key=lambda f: f.id)),
            notes=notes,
            sub_threshold=tuple(sorted(sub_threshold, key=lambda f: f.id)),
        )


# --- counting ---------------------------------------------------------------


def _count(context: SectionContext) -> _Counts:
    """One pass over the player's diagnosable moves."""
    moves = diagnosable(context.player_observations())
    tallies: dict[str, _Tally] = defaultdict(_Tally)
    endgame_games: set[str] = set()

    in_a_run = _runs_of_imprecision(moves)

    for observation in moves:
        if observation.phase == "endgame":
            endgame_games.add(observation.game_id)
            counts_here = _ref(observation) in in_a_run
            _tally(tallies, _key(ENDGAME_ERROR, ANY), observation, counts_here)
            _tally(tallies, _key(ENDGAME_ERROR, material_class(observation.fen_before)),
                   observation, counts_here)

        if not ADVANTAGE_ERROR_RETIRED and _is_clearly_better(observation):
            _tally(tallies, _key(ADVANTAGE_ERROR, CLEAR), observation)

    # The section gate counts **every** diagnosable game, not only those that
    # reached an endgame. That rule was written for `advantage_error`, which is
    # not an endgame claim -- one real player had 12 games and 130 opportunities
    # suppressed by an endgame count of 3. It is kept now that the claim is
    # retired, because `endgame_error` is about to become a residual of the
    # motif detectors and will want the same denominator.
    return _Counts(
        tallies=dict(tallies),
        games_with_data=len({o.game_id for o in moves}),
        endgame_games=len(endgame_games),
    )



def _ref(observation: Observation) -> tuple[str, int]:
    return (observation.game_id, observation.ply)


def _is_tactical(observation: Observation) -> bool:
    """Did a tactic explain this drop? Then it belongs to S1, not here.

    The author:

    > *"If the sudden loss of the advantage of the one move is detected by other
    > motif tests this should not be taken in the account because those are
    > tactical losses and this is lack of knowledge of the endgames."*

    Checked on the move the ENGINE wanted: if the best move executes a motif,
    the player missed a tactic. Saying *"you do not understand endgames"* to
    someone who missed a fork names the wrong weakness, and the report already
    has a section for the right one.

    A move with no engine opinion is treated as **not** tactical rather than
    skipped -- refusing it would drop the drop entirely, and an absent answer
    must not read as a positive one.
    """
    if not observation.best_move:
        return False
    board = chess.Board(observation.fen_before)
    try:
        best = chess.Move.from_uci(observation.best_move)
    except ValueError:
        return False
    if best not in board.legal_moves:
        return False
    return bool(detect_motifs(board, best))


def _runs_of_imprecision(moves) -> frozenset[tuple[str, int]]:
    """The moves belonging to a run of consecutive endgame drops.

    A run is `RUN_LENGTH` losing moves inside a window of `RUN_WINDOW` of the
    player's own endgame moves. Every move in a qualifying run is returned --
    not only the third -- because the claim is about the run and its evidence
    should be able to show it.

    **Tactical drops are removed before the run is looked for**, not after. A
    hung rook in the middle of three inaccuracies does not join them into a run,
    because it is not the same failure: one is not knowing the endgame and the
    other is not seeing a threat.
    """
    by_game: dict[str, list[Observation]] = {}
    for observation in moves:
        if observation.phase == "endgame":
            by_game.setdefault(observation.game_id, []).append(observation)

    found: set[tuple[str, int]] = set()
    for game_id, played in by_game.items():
        played.sort(key=lambda o: o.ply)
        losing = [
            index
            for index, o in enumerate(played)
            if o.label is not None and not _is_tactical(o)
        ]
        for start in range(len(losing) - RUN_LENGTH + 1):
            window = losing[start:start + RUN_LENGTH]
            if window[-1] - window[0] < RUN_WINDOW:
                found |= {_ref(played[i]) for i in window}
    return frozenset(found)


def _tally(tallies: dict[str, _Tally], key: str, observation: Observation,
           counts: bool | None = None) -> None:
    """Record one opportunity, and an instance when `counts`.

    `counts` defaults to the observation's own error label, which is what every
    caller but `endgame_error` wants. That claim passes it explicitly, because
    an endgame error is now a property of a **run** rather than of a move: a
    single blunder in a rook ending is a mistake and not a gap in endgame
    knowledge.
    """
    tally = tallies[key]
    tally.opportunities += 1
    occurred = (observation.label is not None) if counts is None else counts
    if not occurred:
        return
    tally.instances += 1
    tally.games_hit.add(observation.game_id)
    tally.examples.append(observation)
    tally.cost_wp += observation.loss_wp


def _is_clearly_better(observation: Observation) -> bool:
    """Ahead enough to have something to lose, short of the game being decided.

    Read from the mover's point of view: `score_cp_before` is white-relative, so
    a black player being better is a negative score.
    """
    score = observation.score_cp_before
    if not observation.mover_is_white:
        score = -score
    return score >= ADVANTAGE_CP


def _key(kind: str, subject: str) -> str:
    return Claim.of(kind=kind, subject=subject).key()


# --- assertion --------------------------------------------------------------


def _assess(key: str, counts: _Counts, context: SectionContext) -> Finding | None:
    tally = counts.tallies[key]
    kind, subject = key.split(".")[0], key.split(".")[1]

    if tally.opportunities == 0 or not tally.examples:
        return None

    # Peer comparison is not optional here. "You make mistakes in endgames" is
    # true of every player alive (R-14); only being unusual is a diagnosis, and
    # this section has no meaningful within-player baseline to fall back on --
    # unlike S1, where a player's other motifs are a real contrast.
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
        replicated=_replicates(tally, peer_rate),
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
            cost_wp=round(tally.cost_wp, 2),
            peer_cost_per_game=context.peer_cost_per_game(key),
            opportunities=tally.opportunities,
            peer_opportunities_per_game=context.peer_opportunities_per_game(key),
        ),
        provenance=context.provenance,
        confidence=Confidence(
            tier=decision.tier, replicated=stats.replicated, reasons=decision.reasons
        ),
        # An endgame error cannot distinguish "does not know the technique" from
        # "knew it and miscalculated" -- that needs a probe (V9). S3's positions
        # are unusually good probe material, because endgame technique is both
        # teachable and checkable.
        gap_type=GapType(
            hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED
        ),
        evidence=_sample_evidence(tally, f"{SECTION}.{key}:{context.corpus.corpus_id}"),
    )


def _replicates(tally: _Tally, comparison: float) -> bool:
    """Does the claim survive a split of the player's own games?"""
    by_game: dict[str, list[Observation]] = defaultdict(list)
    for observation in tally.examples:
        by_game[observation.game_id].append(observation)
    return len(by_game) >= 2 and tally.instances / max(tally.opportunities, 1) > comparison


def _sample_evidence(tally: _Tally, seed: str) -> tuple[Evidence, ...]:
    """One example per game first, then fill. Seeded, so a profile is reproducible.

    Never the worst blunder: choosing evidence for severity would make the
    pattern look sharper than it is.

    Spreading across games matters for how the claim reads. A uniform sample of
    a claim seen in five games gave three examples from the *same* game, which
    invites the reader to dismiss a real pattern as one bad day -- the opposite
    of the cherry-picking problem, and just as misleading.
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
        Evidence.from_observation(observation, loss_dp=4)
        for observation in chosen
    )
