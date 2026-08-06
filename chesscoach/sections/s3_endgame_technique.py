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
from chesscoach.confidence import MIN_GAMES_WITH_DATA, ClaimStats, assign_tier
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
from chesscoach.sections.base import (
    SectionContext,
    SectionReport,
    diagnosable,
    drop_redundant_aggregates,
)

SECTION = "S3"

ENDGAME_ERROR = "endgame_error"
ADVANTAGE_ERROR = "advantage_error"

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

        findings = drop_redundant_aggregates(
            tuple(
                finding
                for key in sorted(counts.tallies)
                if (finding := _assess(key, counts, context))
            )
        )
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
        )


# --- counting ---------------------------------------------------------------


def _count(context: SectionContext) -> _Counts:
    """One pass over the player's diagnosable moves."""
    moves = diagnosable(context.player_observations())
    tallies: dict[str, _Tally] = defaultdict(_Tally)
    endgame_games: set[str] = set()

    for observation in moves:
        if observation.phase == "endgame":
            endgame_games.add(observation.game_id)
            _tally(tallies, _key(ENDGAME_ERROR, ANY), observation)
            _tally(tallies, _key(ENDGAME_ERROR, material_class(observation.fen_before)), observation)

        if _is_clearly_better(observation):
            _tally(tallies, _key(ADVANTAGE_ERROR, CLEAR), observation)

    # The section gate counts **every** diagnosable game, not only those that
    # reached an endgame. Gating on endgame games blocked `advantage_error`,
    # which is not an endgame claim -- one real player had 12 games and 130
    # opportunities of it suppressed by an endgame count of 3. Per-claim
    # specificity is `distinct_games`' job, and the confidence policy already
    # enforces it.
    return _Counts(
        tallies=dict(tallies),
        games_with_data=len({o.game_id for o in moves}),
        endgame_games=len(endgame_games),
    )


def _tally(tallies: dict[str, _Tally], key: str, observation: Observation) -> None:
    tally = tallies[key]
    tally.opportunities += 1
    if observation.label is None:
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
        rate=rate,
        baseline_rate=peer_rate,
        ci95=wilson_interval(tally.instances, tally.opportunities),
        replicated=_replicates(tally, peer_rate),
    )
    decision = assign_tier(stats)
    if not decision.is_assertable:
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
            cost_wp=round(tally.cost_wp, 2),
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
        Evidence(
            game_id=observation.game_id,
            ply=observation.ply,
            fen=observation.fen_before,
            move_played=observation.move_played,
            better_move=observation.best_move,
            loss_wp=round(observation.loss_wp, 4),
        )
        for observation in chosen
    )
