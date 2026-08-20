"""S7 — material safety: what the player did that made the loss possible.

Design: [[experiments.e34-material-causes]] · Answers open question D13.

The slot E10 emptied. S7 was *calculation quality* and was screened and not
built: the quiet-versus-forcing contrast did not vary between players, and the
one rate that did (`missed_quiet`) correlated **+0.737** with another error rate,
so a claim built on it would have restated how often the player went wrong at
all. E34 revives the slot on a different operationalisation — not *how deeply do
you calculate*, but *did you check* — and passes E10's own test to do it.

Three claims, from eight candidates screened across two experiments. The
number in brackets is the correlation with the player's overall error rate --
E10's test, which refused `missed_quiet` at +0.737:

    moved_into_attack      the piece you just moved can be won      [+0.225]
    miscounted_exchange    a losing exchange AWAY from the kings    [-0.060]
    sacrificed_for_attack  material given up at the enemy king      [+0.208]

    left_hanging           [+0.917]  REFUSED -- the error rate renamed
    ignored_threat         [+0.914]  REFUSED -- likewise
    declined_material      spread 1.20x  REFUSED -- everyone does it
    delayed_material_loss  spread 1.20x  REFUSED -- and drifting to +0.604

The first two refusals share a reason worth keeping in view: a player who errs
more has more loose pieces and more unanswered threats **as a consequence**, so
those rates are error-proneness wearing a better name (L-014, E10's grounds).

**The sacrifice split came from the reviewer and improved the measurement.**
E34 shipped one claim over every material-losing capture and called it
`miscounted_exchange`, which is the wrong name for an attacking player: it
prescribes "count the exchange" to someone who counted it and accepted the cost.
Splitting on whether the material went near the enemy king (E35) raised the
spread of *both* halves above the 1.75x of the combined claim -- 2.71x and 1.84x.
A domain distinction sharpened a measurement, which is not the usual direction.

**These read the move the player actually played.** Every other detector in the
project reads the engine's best move or the opponent's best reply, which is the
structural gap E33 named — a piece placed en prise was only ever visible through
whatever punishment the opponent happened to have.

Neither claim is conditioned on the move being an error, and that is deliberate.
"You put the piece you just moved where it can be won, on 11 % of your moves" is
a statement about a habit; conditioning it on the habit having been punished
would make it a statement about your opponents. The **cost** is error-conditioned,
because a move that lost nothing cost nothing.
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
from chesscoach.material import (
    miscounted_exchange_away_from_king,
    moved_into_attack,
    sacrificed_for_attack,
)
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
    split_by_tier,
)

SECTION = "S7"

MOVED_INTO_ATTACK = "moved_into_attack"
MISCOUNTED = "miscounted_exchange"
SACRIFICED = "sacrificed_for_attack"

EVIDENCE_SAMPLE_SIZE = 4


@dataclass
class _Tally:
    instances: int = 0
    opportunities: int = 0
    games_hit: set[str] = field(default_factory=set)
    examples: list[Observation] = field(default_factory=list)
    # Only what the punished instances actually lost. An unpunished walk into an
    # attack is a habit worth naming and cost nothing, and pricing it as though
    # it had would inflate every ranking this claim enters.
    cost_wp: float = 0.0


@dataclass
class _Counts:
    tallies: dict[str, _Tally]
    games_with_data: int


class S7MaterialSafety:
    """Diagnoses whether a player checks a square before releasing a piece."""

    section = SECTION

    def findings(self, context: SectionContext) -> tuple[Finding, ...]:
        return self.report(context).findings

    def measure(self, context: SectionContext) -> tuple[ConditionMeasurement, ...]:
        counts = _count(context)
        return tuple(
            ConditionMeasurement(
                claim_key=_key(kind),
                instances=tally.instances,
                opportunities=tally.opportunities,
                distinct_games=len(tally.games_hit),
                games_with_data=counts.games_with_data,
                cost_wp=round(tally.cost_wp, 2),
            )
            for kind, tally in sorted(counts.tallies.items())
        )

    def report(self, context: SectionContext) -> SectionReport:
        counts = _count(context)

        if counts.games_with_data < MIN_GAMES_WITH_DATA:
            return SectionReport(
                section=SECTION,
                insufficient_data=True,
                notes=(f"only {counts.games_with_data} games with diagnosable moves",),
            )

        candidates = [_assess(kind, counts, context) for kind in sorted(counts.tallies)]
        findings, watched = split_by_tier(candidates)
        return SectionReport(
            section=SECTION,
            findings=tuple(sorted(findings, key=lambda f: f.id)),
            sub_threshold=tuple(sorted(watched, key=lambda f: f.id)),
        )


# --- counting ---------------------------------------------------------------


def _count(context: SectionContext) -> _Counts:
    """One pass over the player's own moves, reading each move as played."""
    moves = diagnosable(context.player_observations())
    tallies: dict[str, _Tally] = {
        MOVED_INTO_ATTACK: _Tally(),
        MISCOUNTED: _Tally(),
        SACRIFICED: _Tally(),
    }

    for observation in moves:
        board = chess.Board(observation.fen_before)
        try:
            move = chess.Move.from_uci(observation.move_played)
        except ValueError:
            continue
        if move not in board.legal_moves:
            continue

        # Every move is a chance to walk into an attack; only a capture is a
        # chance to miscount one. Denominators are opportunities, never moves.
        _record(tallies[MOVED_INTO_ATTACK], observation, moved_into_attack(board, move))
        if board.is_capture(move):
            # Split on the reviewer's distinction, and the split sharpened
            # both halves: the combined claim spread 1.75x, these spread
            # 2.71x and 1.84x (E35). A sacrifice near the king and an
            # exchange that did not add up want opposite advice.
            _record(tallies[SACRIFICED], observation, sacrificed_for_attack(board, move))
            _record(
                tallies[MISCOUNTED],
                observation,
                miscounted_exchange_away_from_king(board, move),
            )

    return _Counts(
        tallies=tallies,
        games_with_data=len({o.game_id for o in moves}),
    )


def _record(tally: _Tally, observation: Observation, fired: bool) -> None:
    tally.opportunities += 1
    if not fired:
        return
    tally.instances += 1
    tally.games_hit.add(observation.game_id)
    tally.examples.append(observation)
    if observation.label is not None:
        tally.cost_wp += observation.loss_wp


# --- assertion --------------------------------------------------------------


def _assess(kind: str, counts: _Counts, context: SectionContext) -> Finding | None:
    tally = counts.tallies[kind]
    if tally.opportunities == 0 or not tally.examples:
        return None

    key = _key(kind)
    rate = tally.instances / tally.opportunities
    peer_rate = context.peer_rate(key)

    # No within-player baseline exists for these: there is no "other kind of
    # square" to compare a square against. Without a population the claim cannot
    # be made at all, which is the honest state rather than a fallback to a
    # comparison that does not mean anything.
    if peer_rate is None:
        return None

    stats = ClaimStats(
        distinct_games=len(tally.games_hit),
        games_with_data=counts.games_with_data,
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
        claim=Claim.of(kind=kind, subject="own_move"),
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
        # This section is closer to a *why* than any other, and still stops short
        # of one. "You did not check the square" and "you checked and misjudged
        # it" need different remedies and look identical in a game record. Only a
        # probe can separate them (V9).
        gap_type=GapType(
            hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED
        ),
        evidence=_sample_evidence(tally, kind, f"{SECTION}.{key}:{context.corpus.corpus_id}"),
    )


def _replicates(tally: _Tally, comparison: float) -> bool:
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


def _key(kind: str) -> str:
    return Claim.of(kind=kind, subject="own_move").key()


def _sample_evidence(tally: _Tally, kind: str, seed_key: str) -> tuple[Evidence, ...]:
    digest = hashlib.sha256(seed_key.encode("utf-8")).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))

    ordered = sorted(tally.examples, key=lambda o: (o.game_id, o.ply))
    chosen = sorted(
        rng.sample(ordered, min(EVIDENCE_SAMPLE_SIZE, len(ordered))),
        key=lambda o: (o.game_id, o.ply),
    )
    notes = {
        MOVED_INTO_ATTACK: "the piece you moved could be won here",
        MISCOUNTED: "this capture loses material once the recaptures are counted",
        SACRIFICED: "material given up here, next to the enemy king",
    }
    note = notes[kind]
    return tuple(
        Evidence(
            game_id=o.game_id,
            ply=o.ply,
            fen=o.fen_before,
            move_played=o.move_played,
            # The engine's move is the alternative worth showing: it is what
            # keeping the piece safe would have looked like.
            better_move=o.best_move if o.best_move != o.move_played else None,
            loss_wp=round(o.loss_wp, 1),
            note=note,
        )
        for o in chosen
    )
