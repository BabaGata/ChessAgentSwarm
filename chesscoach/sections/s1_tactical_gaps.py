"""S1 — tactical pattern gaps. Which patterns this player does not see.

Design: docs/notes/capacity.agents.s1-tactical-gaps.md

Two directions, and nothing about *why*:

  * **missed** -- a tactic was available and they played something that cost them;
  * **allowed** -- their move handed the opponent a tactic.

Why it happened belongs to another section. If the misses cluster under time
pressure, that is S2's finding, and the two together are what turn "you miss
forks" into "you miss forks when short of time".

Two properties are load-bearing. **Denominators are opportunities, not moves**:
missing forks is measured over positions where a fork was there to be found,
because a per-move rate would mostly measure how tactical the player's opponents
made the game. And **no engine call of its own** -- the opponent's best reply
after the player's move is already the `best_move` of the next observation, so
consecutive observations carry both directions.
"""

from __future__ import annotations

import hashlib
import random
from collections import defaultdict
from dataclasses import dataclass, field

import chess

from chesscoach.analysis.observations import Observation
from chesscoach.confidence import MIN_GAMES_WITH_DATA, ClaimStats, assign_tier
from chesscoach.evaluation.splithalf import split_half_check
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
from chesscoach.tactics import detect_motifs

SECTION = "S1"

MISSED = "missed_motif"
ALLOWED = "allowed_motif"
EXECUTED = "executed_motif"

# Measured but never asserted: knowing what a player does well matters for not
# prescribing it, but it is not a weakness and must not be reported as one.
NOT_ASSERTED = frozenset({EXECUTED})

EVIDENCE_SAMPLE_SIZE = 4


@dataclass
class _Tally:
    """One claim's counts, and the positions that produced them."""

    instances: int = 0
    opportunities: int = 0
    games_hit: set[str] = field(default_factory=set)
    examples: list[Observation] = field(default_factory=list)
    # Win probability given away on the instances. Summed over *every* instance,
    # not the sampled evidence, because this is what the claim costs (D5).
    cost_wp: float = 0.0
    better_moves: dict[tuple[str, int], str] = field(default_factory=dict)


@dataclass
class _Counts:
    """Everything one pass over the player's moves produces."""

    tallies: dict[str, _Tally]
    games_with_data: int
    moves_examined: int


class S1TacticalGaps:
    """Diagnoses which tactical patterns a player misses or walks into."""

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
                # So the population can be asked what this claim costs
                # *everyone*, which is what makes a cost recoverable (step 3).
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
        findings, watched = split_by_tier(candidates)
        return SectionReport(
            section=SECTION,
            findings=tuple(sorted(findings, key=lambda f: f.id)),
            sub_threshold=tuple(sorted(watched, key=lambda f: f.id)),
        )


# --- counting ---------------------------------------------------------------


def _count(context: SectionContext) -> _Counts:
    """Walk the player's moves once, counting every claim they bear on."""
    replies = {(o.game_id, o.ply): o for o in context.observations}
    moves = diagnosable(context.player_observations())
    tallies: dict[str, _Tally] = defaultdict(_Tally)

    for observation in moves:
        board = chess.Board(observation.fen_before)
        _count_available(tallies, board, observation)
        _count_allowed(tallies, observation, replies)

    # The denominator for an "allowed" claim is the player's **errors**, not all
    # their moves. Measured across 38 players, dividing by all moves made this
    # track the overall error rate: weaker players lit up for every motif at
    # once, because erring more often means being punished more often by
    # everything. Conditioning on having erred asks the pattern-specific
    # question instead -- when you go wrong, what punishes you?
    errors = sum(1 for o in moves if o.label is not None)
    for key, tally in tallies.items():
        if key.startswith(ALLOWED):
            tally.opportunities = errors

    return _Counts(
        tallies=dict(tallies),
        games_with_data=len({o.game_id for o in moves}),
        moves_examined=len(moves),
    )


def _count_available(
    tallies: dict[str, _Tally], board: chess.Board, observation: Observation
) -> None:
    """Motifs the engine's move would have executed: an opportunity either way."""
    best = _legal(board, observation.best_move)
    if best is None:
        return

    erred = observation.label is not None and not observation.played_best

    for motif in detect_motifs(board, best):
        missed = tallies[_key(MISSED, motif)]
        missed.opportunities += 1

        executed = tallies[_key(EXECUTED, motif)]
        executed.opportunities += 1

        if erred:
            missed.instances += 1
            missed.games_hit.add(observation.game_id)
            missed.examples.append(observation)
            missed.cost_wp += observation.loss_wp
            missed.better_moves[_ref(observation)] = best.uci()
        elif observation.played_best:
            executed.instances += 1
            executed.games_hit.add(observation.game_id)


def _count_allowed(
    tallies: dict[str, _Tally],
    observation: Observation,
    replies: dict[tuple[str, int], Observation],
) -> None:
    """Tactics the opponent's best reply would execute, when the move was an error."""
    if observation.label is None:
        return

    reply = replies.get((observation.game_id, observation.ply + 1))
    if reply is None:
        return

    board = chess.Board(reply.fen_before)
    punishment = _legal(board, reply.best_move)
    if punishment is None:
        return

    for motif in detect_motifs(board, punishment):
        tally = tallies[_key(ALLOWED, motif)]
        tally.instances += 1
        tally.games_hit.add(observation.game_id)
        tally.examples.append(observation)
        # The player's own move is what conceded it, so the loss on that move is
        # what the concession cost.
        tally.cost_wp += observation.loss_wp
        tally.better_moves[_ref(observation)] = punishment.uci()


# --- assertion --------------------------------------------------------------


def _assess(key: str, counts: _Counts, context: SectionContext) -> Finding | None:
    tally = counts.tallies[key]
    kind, motif = key.split(".")[0], key.split(".")[1]

    if kind in NOT_ASSERTED or tally.opportunities == 0 or not tally.examples:
        return None

    rate = tally.instances / tally.opportunities
    baseline = _rate_on_other_motifs(key, kind, counts.tallies)
    peer_rate = context.peer_rate(key)

    # Where both comparisons exist the claim must beat both: worse than this
    # player is at other tactics, *and* worse than players at their level. A
    # self-baseline alone overstates by however much the behaviour is universal
    # (L-012), and a peer rate alone ignores what they are otherwise good at.
    comparison = max(baseline, peer_rate) if peer_rate is not None else baseline

    stats = ClaimStats(
        distinct_games=len(tally.games_hit),
        games_with_data=counts.games_with_data,
        rate=rate,
        baseline_rate=comparison,
        ci95=wilson_interval(tally.instances, tally.opportunities),
        replicated=_replicates(tally, comparison),
    )
    decision = assign_tier(stats)
    # `watch` is built and returned rather than dropped -- see SectionReport
    # .sub_threshold. `none` still means there is nothing here worth carrying.
    if decision.tier is ConfidenceTier.NONE:
        return None

    return Finding(
        section=SECTION,
        claim=Claim.of(kind=kind, subject=motif),
        measurement=Measurement(
            instances=tally.instances,
            distinct_games=stats.distinct_games,
            games_with_data=counts.games_with_data,
            rate=round(rate, 4),
            baseline_rate=round(baseline, 4),
            peer_rate=round(peer_rate, 4) if peer_rate is not None else None,
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
        # A missed fork cannot distinguish "does not know the pattern" from
        # "knows it and did not see it here". Only a probe can (V9); claiming
        # otherwise would be the guess this project exists to avoid.
        gap_type=GapType(
            hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED
        ),
        evidence=_sample_evidence(tally, motif, f"{SECTION}.{key}:{context.corpus.corpus_id}"),
    )


def _rate_on_other_motifs(key: str, kind: str, tallies: dict[str, _Tally]) -> float:
    """This player's rate on every *other* motif of the same kind.

    "You miss forks more than you miss other tactics" is a real within-player
    contrast, and a different question from how they compare with their peers.
    """
    others = [(k, t) for k, t in tallies.items() if k != key and k.startswith(kind)]
    opportunities = sum(t.opportunities for _, t in others)
    if not opportunities:
        return 0.0
    return sum(t.instances for _, t in others) / opportunities


def _replicates(tally: _Tally, comparison: float) -> bool:
    """Does the claim survive a split of the player's own games?"""
    by_game: dict[str, list[Observation]] = defaultdict(list)
    for example in tally.examples:
        by_game[example.game_id].append(example)
    if len(by_game) < 2:
        return False

    per_game = tally.opportunities / len(by_game)

    def measure(game_ids):
        hits = sum(len(by_game.get(game_id, ())) for game_id in game_ids)
        return hits, max(1, round(per_game * len(game_ids)))

    return split_half_check(by_game.keys(), measure, reference_rate=comparison).replicated


# --- helpers ----------------------------------------------------------------


def _key(kind: str, motif: str) -> str:
    return Claim.of(kind=kind, subject=motif).key()


def _ref(observation: Observation) -> tuple[str, int]:
    return (observation.game_id, observation.ply)


def _legal(board: chess.Board, uci: str | None) -> chess.Move | None:
    if not uci:
        return None
    move = chess.Move.from_uci(uci)
    return move if move in board.legal_moves else None


def _sample_evidence(tally: _Tally, motif: str, seed_key: str) -> tuple[Evidence, ...]:
    """A uniform sample of supporting positions, reproducibly chosen."""
    digest = hashlib.sha256(seed_key.encode("utf-8")).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))

    ordered = sorted(tally.examples, key=lambda o: (o.game_id, o.ply))
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
            better_move=tally.better_moves.get(_ref(o)),
            loss_wp=round(o.loss_wp, 1),
            note=f"{motif} was available here",
        )
        for o in chosen
    )
