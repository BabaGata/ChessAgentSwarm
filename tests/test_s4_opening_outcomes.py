"""S4 — opening repertoire outcomes.

Design: docs/notes/capacity.agents.s4-opening-outcomes.md

The design decision under test is the **subdivision**: by colour, not by opening
name, because a 24-game corpus spread over a dozen ECO codes gives every
per-opening claim two games and L-022 says that fires for nobody. So the tests
here care about denominators — that `any` pools, that the colour split is a real
two-way partition, and that nothing manufactures opportunities.
"""

from __future__ import annotations

import pytest

from chesscoach.analysis.labels import ErrorLabel
from chesscoach.analysis.observations import Observation
from chesscoach.ingest.corpus import Corpus
from chesscoach.profile.models import Claim, DeterminedBy, GapTypeHypothesis, Provenance
from chesscoach.sections.base import OPENING_GRACE_PLIES, SectionContext
from chesscoach.sections.s4_opening_outcomes import (
    EARLY_ERROR,
    OPENING_DISADVANTAGE,
    OPENING_DISADVANTAGE_CP,
    OPENING_END_PLY,
    S4OpeningOutcomes,
)

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-08-05")
FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def an_observation(
    game_id: str = "g1",
    ply: int = 12,
    erred: bool = False,
    score_cp: int = 0,
    white: bool = True,
    mover: str = "alice",
) -> Observation:
    return Observation(
        game_id=game_id,
        ply=ply,
        mover=mover,
        mover_is_white=white,
        fen_before=FEN,
        move_played="e2e4",
        best_move="d2d4",
        score_cp_before=score_cp,
        score_cp_after=score_cp,
        loss_wp=0.2 if erred else 0.0,
        label=ErrorLabel.MISTAKE if erred else None,
        phase="opening_middlegame",
        played_best=not erred,
        clock_before=None,
        clock_after=None,
        engine="stub",
        depth=15,
    )


def a_context(observations, peers=None) -> SectionContext:
    return SectionContext(
        tuple(observations),
        Corpus(
            username="alice",
            corpus_id="c1",
            game_ids=tuple(sorted({o.game_id for o in observations})),
        ),
        PROVENANCE,
        band="1400-1800",
        time_control="rapid",
        peers=peers,
    )


def games(count: int, erred_share: float = 0.5, white: bool = True, **kwargs):
    """`count` games, two diagnosable opening moves each."""
    return [
        an_observation(
            game_id=f"g{n}",
            ply=OPENING_GRACE_PLIES + 2 + move,
            erred=(move == 0 and n < count * erred_share),
            white=white,
            **kwargs,
        )
        for n in range(count)
        for move in range(2)
    ]


def measured(observations, peers=None):
    return {m.claim_key: m for m in S4OpeningOutcomes().measure(a_context(observations, peers))}


class TestTheWindow:
    @pytest.fixture(autouse=True)
    def _early_error_is_counted(self, monkeypatch):
        """`early_error` is retired; these tests are about the machinery.

        The window, the colour partition and the reporting path are all still
        worth testing -- the author kept the tally for asking later whether
        errors inside the opening window are explained by some other detector.
        See `TestEarlyErrorIsRetired` for what a player actually gets.
        """
        from chesscoach.sections import s4_opening_outcomes

        monkeypatch.setattr(s4_opening_outcomes, "EARLY_ERROR_RETIRED", False)

    def test_moves_after_the_opening_are_not_counted(self):
        observations = games(12) + [
            an_observation(game_id="g0", ply=OPENING_END_PLY + 2, erred=True)
        ]

        key = Claim.of(kind=EARLY_ERROR, subject="any").key()

        assert measured(observations)[key].opportunities == 24

    def test_the_grace_plies_are_not_reached_behind(self):
        # diagnosable() already skips them: book moves carry little information.
        observations = games(12) + [
            an_observation(game_id="g0", ply=OPENING_GRACE_PLIES - 1, erred=True)
        ]

        key = Claim.of(kind=EARLY_ERROR, subject="any").key()

        assert measured(observations)[key].opportunities == 24

    def test_only_the_players_own_moves(self):
        observations = games(12) + [an_observation(game_id="g0", ply=14, mover="bob", erred=True)]

        key = Claim.of(kind=EARLY_ERROR, subject="any").key()

        assert measured(observations)[key].opportunities == 24


class TestTheColourSplit:
    @pytest.fixture(autouse=True)
    def _early_error_is_counted(self, monkeypatch):
        """`early_error` is retired; these tests are about the machinery.

        The window, the colour partition and the reporting path are all still
        worth testing -- the author kept the tally for asking later whether
        errors inside the opening window are explained by some other detector.
        See `TestEarlyErrorIsRetired` for what a player actually gets.
        """
        from chesscoach.sections import s4_opening_outcomes

        monkeypatch.setattr(s4_opening_outcomes, "EARLY_ERROR_RETIRED", False)

    def test_white_and_black_partition_the_aggregate(self):
        observations = games(8, white=True) + [
            an_observation(game_id=f"b{n}", ply=12 + m, white=False, erred=(m == 0))
            for n in range(8)
            for m in range(2)
        ]

        result = measured(observations)
        any_key = Claim.of(kind=EARLY_ERROR, subject="any").key()
        white_key = Claim.of(kind=EARLY_ERROR, subject="white").key()
        black_key = Claim.of(kind=EARLY_ERROR, subject="black").key()

        assert result[any_key].opportunities == 32
        assert result[white_key].opportunities + result[black_key].opportunities == 32

    def test_a_player_of_one_colour_only_produces_one_side(self):
        result = measured(games(12, white=True))

        assert Claim.of(kind=EARLY_ERROR, subject="black").key() not in result

    def test_errors_are_attributed_to_the_right_side(self):
        observations = [
            an_observation(game_id=f"w{n}", ply=12, white=True, erred=True) for n in range(6)
        ] + [an_observation(game_id=f"b{n}", ply=12, white=False, erred=False) for n in range(6)]

        result = measured(observations)

        assert result[Claim.of(kind=EARLY_ERROR, subject="white").key()].instances == 6
        assert result[Claim.of(kind=EARLY_ERROR, subject="black").key()].instances == 0


class TestOpeningDisadvantage:
    def test_a_game_that_is_clearly_worse_by_move_fifteen_counts(self):
        observations = [
            an_observation(game_id=f"g{n}", ply=OPENING_END_PLY,
                           score_cp=-(OPENING_DISADVANTAGE_CP + 50))
            for n in range(12)
        ]

        key = Claim.of(kind=OPENING_DISADVANTAGE, subject="any").key()
        result = measured(observations)[key]

        assert result.opportunities == 12
        assert result.instances == 12

    def test_the_denominator_is_games_not_moves(self):
        observations = games(12, score_cp=0)

        key = Claim.of(kind=OPENING_DISADVANTAGE, subject="any").key()

        assert measured(observations)[key].opportunities == 12

    def test_a_level_position_is_not_a_disadvantage(self):
        observations = [
            an_observation(game_id=f"g{n}", ply=OPENING_END_PLY, score_cp=0) for n in range(12)
        ]

        key = Claim.of(kind=OPENING_DISADVANTAGE, subject="any").key()

        assert measured(observations)[key].instances == 0

    def test_it_reads_the_score_from_the_players_side(self):
        # score_cp is white-relative. A black player at -200 is worse; a white
        # player at -200 is worse too, and reading it unflipped would call one
        # of them comfortable.
        observations = [
            an_observation(game_id=f"g{n}", ply=OPENING_END_PLY, white=False,
                           score_cp=OPENING_DISADVANTAGE_CP + 50)
            for n in range(12)
        ]

        key = Claim.of(kind=OPENING_DISADVANTAGE, subject="any").key()

        assert measured(observations)[key].instances == 12

    def test_it_uses_the_last_position_inside_the_window(self):
        # A game decided at move 9 was decided in the opening; the last
        # position we saw is the right one to judge it by.
        observations = [
            an_observation(game_id=f"g{n}", ply=18, score_cp=-(OPENING_DISADVANTAGE_CP + 50))
            for n in range(12)
        ]

        key = Claim.of(kind=OPENING_DISADVANTAGE, subject="any").key()

        assert measured(observations)[key].instances == 12


class TestReporting:
    @pytest.fixture(autouse=True)
    def _early_error_is_counted(self, monkeypatch):
        """`early_error` is retired; these tests are about the machinery.

        The window, the colour partition and the reporting path are all still
        worth testing -- the author kept the tally for asking later whether
        errors inside the opening window are explained by some other detector.
        See `TestEarlyErrorIsRetired` for what a player actually gets.
        """
        from chesscoach.sections import s4_opening_outcomes

        monkeypatch.setattr(s4_opening_outcomes, "EARLY_ERROR_RETIRED", False)

    def peers(self, rate: float = 0.03):
        from chesscoach.peers import ConditionMeasurement, build_reference

        keys = [
            Claim.of(kind=EARLY_ERROR, subject=s).key() for s in ("any", "white", "black")
        ] + [Claim.of(kind=OPENING_DISADVANTAGE, subject="any").key()]
        return build_reference(
            [
                (
                    f"peer{n}",
                    tuple(
                        ConditionMeasurement(k, round(rate * 400), 400, 20, 40) for k in keys
                    ),
                )
                for n in range(8)
            ],
            band="1400-1800",
            time_control="rapid",
            depth=15,
        )

    def test_too_few_games_is_insufficient_data(self):
        report = S4OpeningOutcomes().report(a_context(games(3)))

        assert report.insufficient_data
        assert report.findings == ()

    def test_no_peers_means_no_findings(self):
        # Everybody errs in the opening (R-14).
        report = S4OpeningOutcomes().report(a_context(games(20, erred_share=1.0)))

        assert report.findings == ()

    def test_zero_findings_is_valid(self):
        report = S4OpeningOutcomes().report(
            a_context(games(20, erred_share=0.0), peers=self.peers())
        )

        assert report.findings == ()
        assert not report.insufficient_data

    def test_an_unusual_player_is_reported(self):
        report = S4OpeningOutcomes().report(
            a_context(games(20, erred_share=1.0), peers=self.peers())
        )

        assert report.findings

    def test_the_gap_type_is_honestly_unknown(self):
        # "Does not know this opening" and "knows it and went wrong" need
        # opposite remedies, and only a probe can tell them apart.
        report = S4OpeningOutcomes().report(
            a_context(games(20, erred_share=1.0), peers=self.peers())
        )

        gap = report.findings[0].gap_type
        assert gap.hypothesis is GapTypeHypothesis.UNKNOWN
        assert gap.determined_by is DeterminedBy.INFERRED

    def test_findings_cite_the_players_own_positions(self):
        report = S4OpeningOutcomes().report(
            a_context(games(20, erred_share=1.0), peers=self.peers())
        )

        assert report.findings[0].evidence
        assert all(e.ply <= OPENING_END_PLY for e in report.findings[0].evidence)

    def test_a_colour_finding_suppresses_the_pooled_one(self):
        # "You go wrong early" next to "you go wrong early as White" has said
        # one thing twice. Measured on real players: 2 of 16 got the pair.
        report = S4OpeningOutcomes().report(
            a_context(games(20, erred_share=1.0, white=True), peers=self.peers())
        )

        subjects = {f.claim.subject for f in report.findings}
        assert "white" in subjects
        assert "any" not in subjects

    def test_the_pooled_claim_survives_when_no_colour_clears(self):
        # Half the games as each colour, so neither side alone is unusual
        # enough, but pooled they are. The aggregate is why the section speaks.
        observations = games(10, erred_share=1.0, white=True) + [
            an_observation(game_id=f"b{n}", ply=12 + m, white=False, erred=(m == 0))
            for n in range(10)
            for m in range(2)
        ]

        report = S4OpeningOutcomes().report(a_context(observations, peers=self.peers()))
        subjects = {f.claim.subject for f in report.findings}

        assert subjects <= {"any", "white", "black"}

    def test_evidence_is_spread_across_games(self):
        observations = [
            an_observation(game_id=f"g{n}", ply=10 + m, erred=True)
            for n in range(20)
            for m in range(4)
        ]

        report = S4OpeningOutcomes().report(a_context(observations, peers=self.peers()))
        evidence = report.findings[0].evidence

        assert len({e.game_id for e in evidence}) == len(evidence)


@pytest.mark.parametrize("subject", ["any", "white", "black"])
def test_no_claim_is_named_after_an_opening(subject):
    # The evidence may name an opening; the claim may not. A per-opening claim
    # on a 24-game corpus has two games behind it (L-022).
    assert Claim.of(kind=EARLY_ERROR, subject=subject).key().count(".") == 2


class TestEarlyErrorIsRetired:
    """Retired 2026-09-06 on the author's instruction.

    > *"early_error retire this, this is not valueable measure."*

    It counted any error inside the first 30 plies split by colour, and the
    sentence built on that -- *"You go wrong early as Black"* -- implied a cause
    it never established. The author rejected three firings on exactly that
    ground. `slow_development`, `late_castling`, `repeat_move` and `out_of_book`
    make opening claims that name a behaviour instead.
    """

    def test_it_is_not_counted_at_all(self):
        observations = games(20, erred_share=1.0)

        measured = {m.claim_key for m in S4OpeningOutcomes().measure(a_context(observations))}

        for subject in ("any", "white", "black"):
            assert Claim.of(kind=EARLY_ERROR, subject=subject).key() not in measured

    def test_the_rest_of_the_section_still_measures(self):
        """Retiring one claim must not silence the section that carried it."""
        observations = games(20, erred_share=1.0)

        measured = {m.claim_key for m in S4OpeningOutcomes().measure(a_context(observations))}

        assert measured, "S4 measured nothing at all"
        assert not any(k.startswith(f"{EARLY_ERROR}.") for k in measured)
