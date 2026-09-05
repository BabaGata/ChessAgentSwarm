"""S1 — tactical pattern gaps.

Design: docs/notes/capacity.agents.s1-tactical-gaps.md

The property that matters most is that rates are **per opportunity**: the
denominator for "misses forks" is positions where a fork was there to be found,
not every move. A per-move rate would mostly measure how tactical the player's
games happen to be, which is a fact about their opponents.
"""

from __future__ import annotations

import chess
import pytest

from chesscoach.analysis.labels import ErrorLabel
from chesscoach.analysis.observations import Observation
from chesscoach.ingest.corpus import Corpus
from chesscoach.peers import ConditionMeasurement, build_reference
from chesscoach.profile.models import Claim, DeterminedBy, GapTypeHypothesis, Provenance
from chesscoach.punishment import Punishment
from chesscoach.sections.base import SectionContext
from chesscoach.sections.s1_tactical_gaps import S1TacticalGaps
from chesscoach.tactics import Motif

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-07-31")

# White to move; Ne4-f6+ forks the king on g8 and the rook on e8. Nd6 does not.
FORK_FEN = "4r1k1/8/8/8/4N3/8/8/6K1 w - - 0 1"
FORK_MOVE = "e4f6"
QUIET_MOVE = "e4d6"

# A position whose best move carries no motif at all.
DULL_FEN = "4k3/8/8/8/8/8/8/R3K3 w - - 0 1"
DULL_MOVE = "a1a2"
DULL_ALT = "a1a3"

# Black to move; Ne5-f3 forks the white king on g1 and the rook on e1.
# White to move; Rxa5 wins an undefended pawn, Ra3 does not. `missed_motif
# .hangingPawn` is a claim players *do* differ on within their own band (E84,
# dispersion 1.42x), so it is what the peer comparison can be tested through.
# It was `hangingPiece` until E84 screened within band and found that one flat.
HANGING_FEN = "4k3/8/8/p7/8/8/8/R3K3 w - - 0 1"
HANGING_MOVE = "a1a5"
HANGING_QUIET = "a1a3"

REPLY_FORK_FEN = "6k1/8/8/4n3/8/8/8/4R1K1 b - - 0 1"
REPLY_FORK_MOVE = "e5f3"

# What analysis attaches to an error the opponent could answer with that fork.
ALLOWS_FORK = (Punishment(motif="fork", uci=REPLY_FORK_MOVE, wp=80.0, behind_best_wp=0.0),)


def observation(
    game: int,
    ply: int,
    *,
    fen: str,
    played: str,
    best: str,
    error: bool,
    mover: str = "alice",
    punishments: tuple[Punishment, ...] = (),
) -> Observation:
    """One observation. `punishments` is what analysis attaches to an error --
    the replies executing a motif that were worth playing (design.punishment
    -validity), which is what S1 now reads instead of re-deriving from the
    opponent's next move."""
    return Observation(
        game_id=f"g{game:03d}",
        ply=ply,
        mover=mover,
        mover_is_white=chess.Board(fen).turn == chess.WHITE,
        fen_before=fen,
        move_played=played,
        best_move=best,
        score_cp_before=0,
        score_cp_after=-300 if error else 0,
        loss_wp=40.0 if error else 0.0,
        label=ErrorLabel.BLUNDER if error else None,
        phase="late_middlegame",
        played_best=played == best,
        clock_before=None,
        clock_after=None,
        engine="stub",
        depth=15,
        punishments=punishments,
    )


def a_context(observations, n_games: int = 30, peers=None) -> SectionContext:
    corpus = Corpus(
        username="alice", corpus_id="c1", game_ids=tuple(f"g{n:03d}" for n in range(n_games))
    )
    return SectionContext(
        observations=tuple(observations),
        corpus=corpus,
        provenance=PROVENANCE,
        band="1400-1800" if peers else None,
        time_control="rapid" if peers else None,
        peers=peers,
    )


def player_missing_forks(n_games: int, misses: int, takes: int = 0) -> list[Observation]:
    """Fork chances offered repeatedly; `misses` of them muffed each game."""
    observations: list[Observation] = []
    for game in range(n_games):
        ply = 11
        for _ in range(misses):
            observations.append(
                observation(game, ply, fen=FORK_FEN, played=QUIET_MOVE, best=FORK_MOVE, error=True)
            )
            ply += 2
        for _ in range(takes):
            observations.append(
                observation(game, ply, fen=FORK_FEN, played=FORK_MOVE, best=FORK_MOVE, error=False)
            )
            ply += 2
        # Plenty of ordinary moves, so a per-move rate would look tiny.
        for _ in range(20):
            observations.append(
                observation(game, ply, fen=DULL_FEN, played=DULL_MOVE, best=DULL_MOVE, error=False)
            )
            ply += 2
    return observations


class TestMissedMotifs:
    def test_finds_a_player_who_keeps_missing_forks(self):
        findings = S1TacticalGaps().findings(a_context(player_missing_forks(30, misses=3)))

        assert [(f.claim.kind, f.claim.subject) for f in findings] == [
            ("missed_motif", Motif.FORK)
        ]

    def test_says_nothing_about_a_player_who_takes_them(self):
        findings = S1TacticalGaps().findings(a_context(player_missing_forks(30, 0, takes=3)))

        assert findings == ()

    def test_rate_is_per_opportunity_not_per_move(self):
        # 3 misses out of 3 fork chances, among 23 moves per game. Per move that
        # would read 13%; per opportunity it is 100%, which is the real claim.
        finding = S1TacticalGaps().findings(a_context(player_missing_forks(30, misses=3)))[0]

        assert finding.measurement.rate == pytest.approx(1.0)

    def test_counts_opportunities_only_where_the_motif_was_available(self):
        finding = S1TacticalGaps().findings(a_context(player_missing_forks(30, misses=3)))[0]

        assert finding.measurement.instances == 90  # 3 per game across 30 games


class TestAllowedMotifs:
    def test_finds_a_player_who_walks_into_forks(self):
        observations: list[Observation] = []
        for game in range(30):
            ply = 11
            for _ in range(3):
                # The player errs, and the opponent's best reply is a fork.
                observations.append(
                    observation(
                        game, ply, fen=DULL_FEN, played=DULL_ALT, best=DULL_MOVE,
                        error=True, punishments=ALLOWS_FORK,
                    )
                )
                observations.append(
                    observation(
                        game,
                        ply + 1,
                        fen=REPLY_FORK_FEN,
                        played=REPLY_FORK_MOVE,
                        best=REPLY_FORK_MOVE,
                        error=False,
                        mover="bob",
                    )
                )
                ply += 2
            for _ in range(20):
                observations.append(
                    observation(game, ply, fen=DULL_FEN, played=DULL_MOVE, best=DULL_MOVE, error=False)
                )
                ply += 2

        findings = S1TacticalGaps().findings(a_context(observations))

        assert any(f.claim.kind == "allowed_motif" for f in findings)

    def test_allowed_is_measured_against_errors_not_all_moves(self):
        # Dividing by all moves made this track the overall error rate, so
        # weaker players lit up for every motif at once. The question is
        # pattern-specific: when you go wrong, what punishes you?
        observations: list[Observation] = []
        for game in range(30):
            ply = 11
            for _ in range(2):
                observations.append(
                    observation(game, ply, fen=DULL_FEN, played=DULL_ALT, best=DULL_MOVE,
                                error=True, punishments=ALLOWS_FORK)
                )
                observations.append(
                    observation(game, ply + 1, fen=REPLY_FORK_FEN, played=REPLY_FORK_MOVE,
                                best=REPLY_FORK_MOVE, error=False, mover="bob")
                )
                ply += 2
            for _ in range(20):
                observations.append(
                    observation(game, ply, fen=DULL_FEN, played=DULL_MOVE, best=DULL_MOVE, error=False)
                )
                ply += 2

        measured = {
            m.claim_key: m for m in S1TacticalGaps().measure(a_context(observations))
        }

        allowed = measured[f"allowed_motif.{Motif.FORK}.own"]
        assert allowed.opportunities == 60  # the 2 errors per game, not all 22 moves
        assert allowed.instances == 60


class TestFindingContent:
    def test_admits_it_cannot_tell_knowledge_from_skill(self):
        # A missed fork cannot distinguish not knowing the pattern from knowing
        # it and not seeing it here. Only a probe can, which is the point of V9.
        finding = S1TacticalGaps().findings(a_context(player_missing_forks(30, 3)))[0]

        assert finding.gap_type.hypothesis is GapTypeHypothesis.UNKNOWN
        assert finding.gap_type.determined_by is DeterminedBy.INFERRED

    def test_attaches_evidence_from_the_players_own_games(self):
        finding = S1TacticalGaps().findings(a_context(player_missing_forks(30, 3)))[0]

        assert len(finding.evidence) > 0
        assert all(e.better_move == FORK_MOVE for e in finding.evidence)

    def test_belongs_to_section_s1(self):
        findings = S1TacticalGaps().findings(a_context(player_missing_forks(30, 3)))

        assert all(f.section == "S1" for f in findings)

    def test_is_deterministic(self):
        observations = player_missing_forks(30, 3)

        first = S1TacticalGaps().findings(a_context(observations))
        second = S1TacticalGaps().findings(a_context(observations))

        assert [f.id for f in first] == [f.id for f in second]
        assert first[0].evidence == second[0].evidence


def player_missing_hanging_pawns(n_games: int, misses: int) -> list[Observation]:
    """The same shape as `player_missing_forks`, on a claim that separates."""
    observations: list[Observation] = []
    for game in range(n_games):
        ply = 11
        for _ in range(misses):
            observations.append(
                observation(game, ply, fen=HANGING_FEN, played=HANGING_QUIET,
                            best=HANGING_MOVE, error=True)
            )
            ply += 2
        for _ in range(20):
            observations.append(
                observation(game, ply, fen=DULL_FEN, played=DULL_MOVE, best=DULL_MOVE, error=False)
            )
            ply += 2
    return observations


class TestPeerComparison:
    """The peer comparison, and the claims that are no longer allowed one.

    E83 measured whether players differ on each claim by more than sampling
    noise. Where they do not, no peer comparison can be asserted -- so these
    tests exercise the mechanism through `hangingPiece`, which separates, and
    assert the *absence* of a comparison for `fork`, which does not.
    """

    def peers_at(self, kind: str, subject: str, rate: float):
        key = Claim.of(kind=kind, subject=subject).key()
        return build_reference(
            [
                (name, (ConditionMeasurement(key, int(rate * 100), 100, 20, 40),))
                for name in ("peer1", "peer2", "peer3")
            ],
            band="1400-1800",
            time_control="rapid",
            depth=15,
        )

    def test_stays_silent_when_everyone_misses_them_just_as_often(self):
        context = a_context(
            player_missing_hanging_pawns(30, 3),
            peers=self.peers_at("missed_motif", Motif.HANGING_PAWN, 1.0),
        )

        assert S1TacticalGaps().findings(context) == ()

    def test_speaks_when_the_player_is_worse_than_their_peers(self):
        context = a_context(
            player_missing_hanging_pawns(30, 3),
            peers=self.peers_at("missed_motif", Motif.HANGING_PAWN, 0.2),
        )

        findings = S1TacticalGaps().findings(context)

        assert findings[0].measurement.peer_rate == pytest.approx(0.2)

    def test_a_claim_players_do_not_differ_on_carries_no_peer_rate(self):
        # The reference holds a rate for forks and it is deliberately not used:
        # comparing on it would rank the player by sampling noise (E83). The
        # claim is still measured and still costed -- the arbiter puts it in the
        # sub-threshold pool rather than dropping it.
        context = a_context(
            player_missing_forks(30, 3),
            peers=self.peers_at("missed_motif", Motif.FORK, 0.2),
        )

        findings = S1TacticalGaps().findings(context)

        missed = [f for f in findings if f.claim.subject == Motif.FORK]
        assert missed and missed[0].measurement.peer_rate is None


class TestMeasure:
    def test_reports_raw_rates_without_judgement(self):
        measurements = S1TacticalGaps().measure(a_context(player_missing_forks(30, 3)))

        by_key = {m.claim_key: m for m in measurements}
        missed = by_key[f"missed_motif.{Motif.FORK}.own"]
        assert missed.instances == 90
        assert missed.opportunities == 90

    def test_measures_motifs_the_player_executed_without_asserting_them(self):
        context = a_context(player_missing_forks(30, 0, takes=3))

        measurements = S1TacticalGaps().measure(context)
        findings = S1TacticalGaps().findings(context)

        assert any("executed_motif" in m.claim_key for m in measurements)
        assert all("executed_motif" not in f.claim.kind for f in findings)


class TestContract:
    def test_stays_silent_with_too_few_games(self):
        assert S1TacticalGaps().findings(a_context(player_missing_forks(4, 3), n_games=4)) == ()

    def test_returns_nothing_for_an_empty_corpus(self):
        assert S1TacticalGaps().findings(a_context([], 0)) == ()

    def test_ignores_the_opponents_moves(self):
        opponent_only = [
            observation(g, 11, fen=FORK_FEN, played=QUIET_MOVE, best=FORK_MOVE, error=True,
                        mover="bob")
            for g in range(30)
        ]

        assert S1TacticalGaps().findings(a_context(opponent_only)) == ()
