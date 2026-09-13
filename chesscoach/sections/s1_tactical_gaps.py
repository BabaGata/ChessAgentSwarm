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

from chesscoach.analysis.labels import win_probability
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
    instance_moves,
    worth_citing,
    split_by_tier,
)
from chesscoach.punishment import WORTH_PLAYING_WP, primary
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
    #
    # Conditioning further, on the motif having been *available*, was built and
    # measured in E84 and **reverted**. It leaves the engine's move choice as the
    # only thing varying -- whether the available tactic is objectively best is
    # not the player's doing -- so it saturates (a forced mate is always best, so
    # `backRankMate` read exactly 1.000) and it collapses the denominator. Same
    # band and speed, it cost three claims their separation and left two
    # unmeasurable, improving none.
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
    """Motifs the player could have played: an opportunity either way.

    **Not only the engine's single best move.** `allowed_motif` was rebuilt on
    *"not best, good enough"* -- a punishment counts when it was within an
    inaccuracy of the opponent's best ([[design.punishment-validity]]) -- and
    this side was left reading `best_move` alone. So a fork the player could
    have played, second best by a hair, was not a missed fork and was not even
    an opportunity: it never reached the denominator.

    Measured over 187 positions, best-move-only found **10** tactics where
    within-an-inaccuracy found **32**, and `missed_motif.pin` found **zero**
    against eight. A pin is a quiet move and the engine rarely ranks it first,
    so a rule keyed on *first* cannot see one at all
    ([[design.multipv-candidate-moves]]). The author confirmed the rule is
    symmetric when asked.

    **One threshold, one owner**: `WORTH_PLAYING_WP` is the same constant on
    both sides, reused from the error threshold rather than chosen.

    An observation with no candidates -- an older profile, or an analyser that
    cannot do MultiPV -- is judged the old way, on the best move alone. That
    measures less rather than nothing (L-046).
    """
    best = _legal(board, observation.best_move)
    if best is None:
        return

    erred = observation.label is not None and not observation.played_best

    for motif in _available_motifs(board, best, observation):
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


def _available_motifs(
    board: chess.Board, best: chess.Move, observation: Observation
) -> frozenset[str]:
    """Every motif the player could have executed by a move worth playing.

    Read off `observation.available`, which the analysis pass computed with the
    **same function** that produces `punishments` one ply later -- so the
    author's *"doesn't have to be the very best move"* holds on both sides by
    one code path rather than two rules that happen to agree.

    **A motif counts once however many moves execute it.** Two squares offering
    the same fork is one fork missed, which is what `_count_allowed` already
    does on the other side; `frozenset` is the whole of that rule.

    The engine's own best move is always included, so this can only ever widen
    what the old rule found. That matters when reading the rebuild: a change in
    a `missed_motif` rate is an addition, never a substitution.

    An observation with nothing recorded -- an older profile, or a move that was
    not an error -- falls back to the best move alone. That measures less rather
    than nothing (L-046).
    """
    found = set(detect_motifs(board, best))
    found |= {candidate.motif for candidate in observation.available}
    return frozenset(found)


def _count_allowed(
    tallies: dict[str, _Tally],
    observation: Observation,
    replies: dict[tuple[str, int], Observation],
) -> None:
    """Tactics the opponent could have punished this error with.

    Reads `observation.punishments`, computed during analysis: every reply that
    executes a motif **and was worth playing** -- within an inaccuracy of the
    opponent's best. Not only their single best reply, which missed a fork that
    was excellent but second-best, and missed a good fork whenever mate was also
    on the board. See [[design.punishment-validity]].

    S1 still makes **no engine call of its own**; the evaluations this needs were
    made once, in the analysis pass, where the position was already open.

    **One mistake pays once.** A blunder can leave a fork, a pin and a skewer all
    available; every one of them is counted as an instance, because detection
    stays broad, but the win probability it cost is charged only to the
    punishment that would be *named* -- the one reaching the highest evaluation,
    which makes mate outrank material without a table saying so. Charging the
    loss to each would treble it, and the arbiter ranks on cost.
    """
    if observation.label is None or not observation.punishments:
        return

    named = primary(observation.punishments)

    # A motif is one instance per error however many moves would execute it:
    # two squares offering the same fork is one fork allowed, not two.
    seen: set[str] = set()
    for punishment in observation.punishments:
        if punishment.motif in seen:
            continue
        seen.add(punishment.motif)

        tally = tallies[_key(ALLOWED, punishment.motif)]
        tally.instances += 1
        tally.games_hit.add(observation.game_id)
        tally.examples.append(observation)
        tally.better_moves[_ref(observation)] = punishment.uci
        if named is not None and punishment.motif == named.motif:
            # The player's own move is what conceded it, so the loss on that
            # move is what the concession cost.
            tally.cost_wp += observation.loss_wp


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
        corpus_games=context.corpus.n_games,
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
            instances_at=instance_moves(tally.examples),
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
        evidence=_sample_evidence(
            tally, motif, f"{SECTION}.{key}:{context.corpus.corpus_id}",
            allowed=key.startswith(ALLOWED),
        ),
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


def _sample_evidence(
    tally: _Tally, motif: str, seed_key: str, allowed: bool = False
) -> tuple[Evidence, ...]:
    """A uniform sample of supporting positions, reproducibly chosen.

    `allowed` decides what `tally.better_moves` *means*. For a missed motif it is
    the move the player should have found. For an allowed one it is the move the
    **opponent** played to punish them, which is not an alternative for the
    player and is not even legal for their colour -- printing it as "was better"
    is how the report came to recommend moves nobody could make.
    """
    digest = hashlib.sha256(seed_key.encode("utf-8")).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))

    # Prefers instances that cost the player something -- see
    # `base.worth_citing`. The seed keeps a profile reproducible.
    chosen = worth_citing(tally.examples, EVIDENCE_SAMPLE_SIZE, seed_key)
    return tuple(
        Evidence.from_observation(
            o,
            better_move=None if allowed else tally.better_moves.get(_ref(o)),
            opponent_reply=tally.better_moves.get(_ref(o)) if allowed else None,
            note=(
                f"you allowed {motif} here" if allowed
                else f"{motif} was available here"
            ),
        )
        for o in chosen
    )
