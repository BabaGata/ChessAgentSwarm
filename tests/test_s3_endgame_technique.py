"""S3 — endgame technique and advantage retention.

Design: docs/notes/capacity.agents.s3-endgame-technique.md

The section exists for **coverage**: E08 measured the swarm silent for 29 of 38
real players, so the tests that matter most here are the ones about denominators
— that `any` pools enough to be able to speak, and that the classes do not
manufacture opportunities to get past the gate.
"""

from __future__ import annotations

import pytest

from chesscoach.analysis.labels import ErrorLabel
from chesscoach.analysis.observations import Observation
from chesscoach.ingest.corpus import Corpus
from chesscoach.profile.models import Claim, DeterminedBy, GapTypeHypothesis, Provenance
from chesscoach.sections.base import DECIDED_CP, SectionContext
from chesscoach.sections.s3_endgame_technique import (
    ADVANTAGE_CP,
    ANY,
    ENDGAME_ERROR,
    S3EndgameTechnique,
    material_class,
)

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-08-05")

# Kings on f2/f7, pawns e4/e5, and whatever else the class needs on the back rank.
FENS = {
    "pawn": "8/5k2/8/4p3/4P3/8/5K2/8 w - - 0 1",
    "rook": "8/5k2/8/4p3/4P3/8/5K2/R7 w - - 0 1",
    "minor": "8/5k2/8/4p3/4P3/8/5K2/5B2 w - - 0 1",
    "rook_minor": "8/5k2/8/4p3/4P3/8/5K2/R4B2 w - - 0 1",
    "queen": "8/5k2/8/4p3/4P3/8/5K2/5Q2 w - - 0 1",
}


def an_observation(
    game_id: str = "g1",
    ply: int = 40,
    fen: str | None = None,
    phase: str = "endgame",
    erred: bool = False,
    score_cp: int = 0,
    mover: str = "alice",
) -> Observation:
    return Observation(
        game_id=game_id,
        ply=ply,
        mover=mover,
        mover_is_white=True,
        fen_before=fen or FENS["rook"],
        move_played="a1a2",
        best_move="a1a8",
        score_cp_before=score_cp,
        score_cp_after=score_cp,
        loss_wp=0.2 if erred else 0.0,
        label=ErrorLabel.MISTAKE if erred else None,
        phase=phase,
        played_best=not erred,
        clock_before=None,
        clock_after=None,
        engine="stub",
        depth=15,
    )


def a_context(observations, peers=None, band="1400-1800") -> SectionContext:
    game_ids = tuple(sorted({o.game_id for o in observations}))
    return SectionContext(
        tuple(observations),
        Corpus(username="alice", corpus_id="c1", game_ids=game_ids),
        PROVENANCE,
        band=band,
        time_control="rapid",
        peers=peers,
    )


def games(count: int, erred_share: float = 0.5, fen_key: str = "rook", **kwargs):
    """`count` games, two diagnosable endgame moves each."""
    observations = []
    for n in range(count):
        for move in range(2):
            observations.append(
                an_observation(
                    game_id=f"g{n}",
                    ply=40 + move,
                    fen=FENS[fen_key],
                    erred=(move == 0 and n < count * erred_share),
                    **kwargs,
                )
            )
    return observations


class TestMaterialClass:
    @pytest.mark.parametrize("expected,fen", FENS.items())
    def test_each_class_is_recognised(self, expected, fen):
        assert material_class(fen) == expected

    def test_a_queen_dominates_whatever_else_is_on(self):
        # Queens make a position volatile regardless of the rest, so the class
        # is named for them.
        assert material_class("8/5k2/8/8/8/8/5K2/R3QB2 w - - 0 1") == "queen"

    def test_rooks_and_minors_together_are_their_own_class(self):
        assert material_class(FENS["rook_minor"]) == "rook_minor"

    def test_a_position_that_is_not_an_endgame_still_classifies(self):
        # Classification is a property of the material, not of the phase; the
        # agent decides what to do with it.
        assert material_class("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1") == "queen"


class TestWhatIsCounted:
    def test_only_endgame_moves(self):
        observations = games(12, fen_key="rook") + [
            an_observation(game_id="g99", phase="opening_middlegame", erred=True)
        ]

        measured = {m.claim_key: m for m in S3EndgameTechnique().measure(a_context(observations))}
        key = Claim.of(kind=ENDGAME_ERROR, subject=ANY).key()

        assert measured[key].opportunities == 24

    def test_only_the_players_own_moves(self):
        observations = games(12) + [an_observation(game_id="g0", ply=42, mover="bob", erred=True)]

        measured = {m.claim_key: m for m in S3EndgameTechnique().measure(a_context(observations))}
        key = Claim.of(kind=ENDGAME_ERROR, subject=ANY).key()

        assert measured[key].opportunities == 24

    def test_decided_positions_are_excluded(self):
        # Beyond DECIDED_CP win probability compresses, so an error there is
        # both cheap to make and nearly invisible (L-009).
        observations = games(12) + [
            an_observation(game_id="g0", ply=44, score_cp=DECIDED_CP + 200, erred=True)
        ]

        measured = {m.claim_key: m for m in S3EndgameTechnique().measure(a_context(observations))}
        key = Claim.of(kind=ENDGAME_ERROR, subject=ANY).key()

        assert measured[key].opportunities == 24


class TestTheAggregate:
    def test_any_pools_every_class(self):
        observations = games(6, fen_key="rook") + games(6, fen_key="pawn")
        for index, observation in enumerate(observations):
            observations[index] = an_observation(
                game_id=f"p{index // 2}", ply=40 + index % 2,
                fen=observation.fen_before, erred=observation.label is not None,
            )

        measured = {m.claim_key: m for m in S3EndgameTechnique().measure(a_context(observations))}
        any_key = Claim.of(kind=ENDGAME_ERROR, subject=ANY).key()
        rook_key = Claim.of(kind=ENDGAME_ERROR, subject="rook").key()

        assert measured[any_key].opportunities > measured[rook_key].opportunities

    def test_the_aggregate_is_the_reason_this_section_can_speak(self):
        # E08: per-thing denominators are too thin to clear the gate. A single
        # class here would have 8 opportunities; pooled it has enough to matter.
        observations = []
        for index, key in enumerate(FENS):
            observations += games(4, fen_key=key)[: 8]
        observations = [
            an_observation(game_id=f"g{i // 2}", ply=40 + i % 2, fen=o.fen_before,
                           erred=o.label is not None)
            for i, o in enumerate(observations)
        ]

        measured = {m.claim_key: m for m in S3EndgameTechnique().measure(a_context(observations))}
        any_key = Claim.of(kind=ENDGAME_ERROR, subject=ANY).key()

        assert measured[any_key].opportunities == len(observations)


class TestAdvantageRetention:
    """Retired 2026-08-29 — measured, uninformative, and no longer counted.

    The tests are kept and inverted rather than deleted: they are what would
    catch the claim coming back by accident, and they document that the
    machinery still works if the author revives it.
    """

    def test_it_is_not_counted_at_all(self):
        # Was 24 opportunities. The author marked all five sampled instances
        # "cannot tell" -- it fires on real errors and names nothing.
        observations = games(12, score_cp=ADVANTAGE_CP + 50)

        measured = {m.claim_key: m for m in S3EndgameTechnique().measure(a_context(observations))}

        assert Claim.of(kind="advantage_error", subject="clear").key() not in measured

    def test_the_machinery_that_made_it_still_works(self):
        # Kept for the use the author named: checking whether the ORIGIN of
        # these errors is detected elsewhere. If `_is_clearly_better` rots, that
        # question becomes expensive to ask again.
        from chesscoach.sections.s3_endgame_technique import _is_clearly_better

        better = games(1, score_cp=ADVANTAGE_CP + 50)[0]
        level = games(1, score_cp=0)[0]

        assert _is_clearly_better(better) is True
        assert _is_clearly_better(level) is False

    def test_retiring_it_does_not_disturb_the_endgame_claim(self):
        # The two shared a pass over the same moves, so the risk of the change
        # is here rather than in the claim being removed.
        observations = games(12, score_cp=ADVANTAGE_CP + 50, phase="endgame")

        measured = {m.claim_key: m for m in S3EndgameTechnique().measure(a_context(observations))}

        assert Claim.of(kind=ENDGAME_ERROR, subject=ANY).key() in measured
class TestReporting:
    def test_too_few_games_is_insufficient_data_not_silence(self):
        # "We could not assess your endgames" and "your endgames are fine" are
        # different statements and must not collapse.
        report = S3EndgameTechnique().report(a_context(games(3)))

        assert report.insufficient_data
        assert report.findings == ()

    def test_a_player_who_never_reaches_an_endgame_is_told_so(self):
        # Not section-wide insufficient_data: advantage retention is still
        # measurable for them, and blocking the whole section would throw that
        # away. The gap is said in a note instead, because silence about
        # endgames would otherwise read as "your endgames are fine".
        observations = [
            an_observation(game_id=f"g{n}", phase="opening_middlegame") for n in range(20)
        ]

        report = S3EndgameTechnique().report(a_context(observations))

        assert not report.insufficient_data
        assert "endgame findings are not available" in report.notes[0]

    def test_the_denominator_counts_every_diagnosable_game(self):
        # Was written for `advantage_error`, which is now retired, and kept
        # because the rule outlived the claim: the section counts every
        # diagnosable game rather than only those reaching an endgame. The bug
        # it guards against suppressed a finding backed by 12 games and 130
        # opportunities because only 3 games reached an endgame.
        #
        # It matters again shortly: `endgame_error` is becoming a residual of
        # the motif detectors and will want this same denominator.
        observations = [
            an_observation(game_id=f"g{n}", ply=20 + m, phase="endgame",
                           score_cp=ADVANTAGE_CP + 50, erred=(m == 0))
            for n in range(20)
            for m in range(2)
        ]

        measured = {m.claim_key: m for m in S3EndgameTechnique().measure(a_context(observations))}
        key = Claim.of(kind=ENDGAME_ERROR, subject=ANY).key()

        assert measured[key].games_with_data == 20

    def test_no_peers_means_no_findings(self):
        # "You make mistakes in endgames" is true of everyone (R-14). Without a
        # population there is nothing to be unusual against.
        report = S3EndgameTechnique().report(a_context(games(20, erred_share=1.0)))

        assert report.findings == ()

    def test_zero_findings_is_a_valid_report(self):
        report = S3EndgameTechnique().report(a_context(games(20, erred_share=0.0)))

        assert report.findings == ()
        assert not report.insufficient_data


class TestFindingShape:
    def peers(self, rate: float = 0.02):
        from chesscoach.peers import ConditionMeasurement, build_reference

        key = Claim.of(kind=ENDGAME_ERROR, subject=ANY).key()
        return build_reference(
            [
                (f"peer{n}", (ConditionMeasurement(key, round(rate * 400), 400, 20, 40),))
                for n in range(8)
            ],
            band="1400-1800",
            time_control="rapid",
            depth=15,
        )

    def test_an_unusual_player_is_reported_against_peers(self):
        report = S3EndgameTechnique().report(
            a_context(games(20, erred_share=1.0), peers=self.peers())
        )

        assert report.findings
        assert report.findings[0].measurement.peer_rate == pytest.approx(0.02, abs=0.005)

    def test_the_gap_type_is_honestly_unknown(self):
        # An endgame error cannot distinguish "does not know the technique" from
        # "knew it and miscalculated". Only a probe can.
        report = S3EndgameTechnique().report(
            a_context(games(20, erred_share=1.0), peers=self.peers())
        )

        gap = report.findings[0].gap_type
        assert gap.hypothesis is GapTypeHypothesis.UNKNOWN
        assert gap.determined_by is DeterminedBy.INFERRED

    def test_findings_cite_positions_from_the_players_games(self):
        report = S3EndgameTechnique().report(
            a_context(games(20, erred_share=1.0), peers=self.peers())
        )

        assert report.findings[0].evidence
        assert all(e.game_id.startswith("g") for e in report.findings[0].evidence)

    def test_evidence_is_spread_across_games_rather_than_bunched(self):
        # A claim seen in five games once cited three examples from the same
        # game, which invites the reader to dismiss a pattern as one bad day.
        observations = []
        for game in range(20):
            for move in range(4):
                observations.append(
                    an_observation(game_id=f"g{game}", ply=40 + move, erred=True)
                )

        report = S3EndgameTechnique().report(a_context(observations, peers=self.peers()))
        evidence = report.findings[0].evidence

        assert len({e.game_id for e in evidence}) == len(evidence)

    def test_a_typical_player_is_not_reported(self):
        report = S3EndgameTechnique().report(
            a_context(games(20, erred_share=0.5), peers=self.peers(rate=0.5))
        )

        assert report.findings == ()
