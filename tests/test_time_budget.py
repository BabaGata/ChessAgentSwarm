"""S2 — the long think that costs you later, not at the time.

Spec: docs/notes/experiments.e18-excluded-as-finding.md

S2 already measures the error made **on** a long think, and the error made
**while** short of time. It has never measured the link between them: time spent
early is a budget, and spending it does not hurt on the move it is spent — it
hurts twenty moves later, when there is nothing left.

Screened at a **1.91x** p90/median spread, above `long_think_error` (1.60) and
`allows_king_pressure` (1.59), and correlated only **+0.204** with the existing
time-pressure claim, so it is not that claim renamed.

The baseline is deliberately **late moves in the player's unhurried games**, not
"every other move". Comparing late-and-rushed against everything-else would
fold the opening in and measure the phase as much as the clock.
"""

from __future__ import annotations

from chesscoach.analysis.observations import Observation
from chesscoach.sections.s2_decision_process import (
    OVERSPEND_BUDGET_PLY,
    OVERSPEND_SHARE,
    _overspent_games,
)

FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def move(game_id: str, ply: int, clock_after: float | None, error: bool = False) -> Observation:
    from chesscoach.analysis.labels import ErrorLabel

    return Observation(
        game_id=game_id,
        ply=ply,
        mover="alice",
        mover_is_white=True,
        fen_before=FEN,
        move_played="e2e4",
        best_move="d2d4" if error else "e2e4",
        score_cp_before=0,
        score_cp_after=-100 if error else 0,
        loss_wp=12.0 if error else 0.0,
        label=ErrorLabel.MISTAKE if error else None,
        phase="opening_middlegame",
        played_best=not error,
        clock_before=None,
        clock_after=clock_after,
        engine="stub",
        depth=15,
    )


def a_game(game_id: str, clock_at_budget: float, start: float = 600.0):
    """A game whose clock reads `clock_at_budget` by the budget ply."""
    return [
        move(game_id, 2, start),
        move(game_id, OVERSPEND_BUDGET_PLY, clock_at_budget),
        move(game_id, OVERSPEND_BUDGET_PLY + 2, clock_at_budget - 10),
    ]


class TestSpottingTheOverspend:
    def test_burning_most_of_the_clock_early_counts(self):
        # 200s left of 600 by move 15 -- two thirds gone.
        assert _overspent_games(tuple(a_game("g1", 200.0))) == frozenset({"g1"})

    def test_keeping_the_clock_does_not(self):
        assert _overspent_games(tuple(a_game("g1", 500.0))) == frozenset()

    def test_the_threshold_is_where_it_says_it_is(self):
        just_over = 600.0 * (1 - OVERSPEND_SHARE) - 1
        just_under = 600.0 * (1 - OVERSPEND_SHARE) + 1

        assert _overspent_games(tuple(a_game("g1", just_over))) == frozenset({"g1"})
        assert _overspent_games(tuple(a_game("g2", just_under))) == frozenset()

    def test_the_starting_clock_is_taken_from_the_game_itself(self):
        # A section never sees the PGN's TimeControl tag, only observations, so
        # the highest reading in the game stands in for the starting clock. A
        # 300s game burned to 100s is overspending just as a 600s one is.
        assert _overspent_games(tuple(a_game("g1", 100.0, start=300.0))) == frozenset({"g1"})

    def test_a_game_with_no_late_moves_is_not_judged(self):
        # Nothing was spent *on* anything if the game ended at the budget mark.
        early_only = (move("g1", 2, 600.0), move("g1", OVERSPEND_BUDGET_PLY, 100.0))

        assert _overspent_games(early_only) == frozenset()

    def test_a_game_without_clocks_is_not_judged(self):
        blind = (move("g1", 2, None), move("g1", OVERSPEND_BUDGET_PLY + 2, None))

        assert _overspent_games(blind) == frozenset()

    def test_games_are_judged_separately(self):
        observations = tuple(a_game("rushed", 100.0) + a_game("calm", 550.0))

        assert _overspent_games(observations) == frozenset({"rushed"})


class TestTheCondition:
    def condition(self, observations):
        from chesscoach.sections.s2_decision_process import _conditions

        found = [c for c in _conditions(observations) if c.kind == "time_budget_error"]
        assert found, "S2 should offer a time_budget_error condition"
        return found[0]

    def test_late_moves_in_a_rushed_game_are_inside(self):
        observations = tuple(a_game("rushed", 100.0))
        condition = self.condition(observations)

        late = [o for o in observations if condition.applies(o)]

        assert [o.ply for o in late] == [OVERSPEND_BUDGET_PLY + 2]

    def test_early_moves_of_the_same_game_are_not(self):
        observations = tuple(a_game("rushed", 100.0))
        condition = self.condition(observations)

        assert not condition.applies(observations[0])

    def test_late_moves_in_an_unhurried_game_are_the_baseline(self):
        observations = tuple(a_game("rushed", 100.0) + a_game("calm", 550.0))
        condition = self.condition(observations)

        baseline = [o for o in observations if condition.baseline_applies(o)]

        assert [(o.game_id, o.ply) for o in baseline] == [
            ("calm", OVERSPEND_BUDGET_PLY + 2)
        ]

    def test_the_baseline_excludes_early_moves_entirely(self):
        # Otherwise the claim measures the phase as much as the clock.
        observations = tuple(a_game("rushed", 100.0) + a_game("calm", 550.0))
        condition = self.condition(observations)

        assert not any(
            condition.baseline_applies(o) for o in observations if o.ply <= OVERSPEND_BUDGET_PLY
        )

    def test_it_is_not_withheld_as_selection_confounded(self):
        # `long_think_error` is withheld because a hard position causes both the
        # think and the error. Here the magnitude varies strongly between
        # players (1.18 median, 3.36 max), which is the signature of a player
        # property rather than a base rate -- the M5 test that caught L-011.
        assert self.condition(tuple(a_game("g1", 100.0))).selection_confounded is False


class TestTheOtherConditionsAreUnharmed:
    def test_conditions_without_a_custom_baseline_still_use_everything_else(self):
        from chesscoach.sections.s2_decision_process import _conditions

        observations = tuple(a_game("g1", 500.0))
        pressure = [c for c in _conditions(observations) if c.kind == "time_pressure_error"][0]

        assert pressure.baseline_applies is None

    def test_all_four_conditions_are_offered(self):
        from chesscoach.sections.s2_decision_process import _conditions

        kinds = {c.kind for c in _conditions(tuple(a_game("g1", 100.0)))}

        assert kinds == {
            "time_pressure_error",
            "instant_move_error",
            "long_think_error",
            "time_budget_error",
        }


class TestItCanBeSaid:
    """A claim kind with no wording prints its own machine name at the player."""

    def a_finding(self):
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
            Provenance,
        )

        return Finding(
            section="S2",
            claim=Claim.of(kind="time_budget_error", subject="after_overspending"),
            measurement=Measurement(
                instances=12, distinct_games=6, games_with_data=24, rate=0.18, peer_rate=0.10
            ),
            provenance=Provenance(
                engine="stub", depth=15, corpus_id="c1", analysed_at="2026-08-06"
            ),
            confidence=Confidence(tier=ConfidenceTier.FOCUS, replicated=True),
            gap_type=GapType(
                hypothesis=GapTypeHypothesis.PROCESS, determined_by=DeterminedBy.INFERRED
            ),
            evidence=(Evidence(game_id="g1", ply=40, fen=FEN),),
        )

    def test_the_quantity_is_named_for_a_person(self):
        from chesscoach.phrasing import quantity

        said = quantity(self.a_finding())

        assert "after_overspending" not in said and "time_budget_error" not in said

    def test_the_statement_is_named_for_a_person(self):
        from chesscoach.phrasing import statement

        said = statement(self.a_finding())

        assert "after_overspending" not in said and "time_budget_error" not in said

    def test_the_planner_has_a_remedy_for_it(self):
        from chesscoach.planner import _action

        assert "time_budget_error" not in _action(self.a_finding())

    def test_the_remedy_is_about_the_budget_not_the_symptom(self):
        from chesscoach.planner import _action

        assert "clock" in _action(self.a_finding()).lower()
