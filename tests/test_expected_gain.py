"""D5 — ranking by what a weakness costs, not only by how unusual it is.

Spec: docs/notes/state.md D5 · docs/notes/experiments.e15-expected-gain.md

The distinction that makes this tractable at all: E03 asked a **predictive**
question — does feature X predict errors? — and failed. This asks an
**accounting** question — for instances already identified as mistakes, how much
win probability was given away on exactly those moves? No prediction is involved,
and the answer is a sum over evidence the profile already holds.

Which is also why it stops where it stops: a claim whose instances are not
mistakes has nothing to sum.
"""

from __future__ import annotations

import pytest

from chesscoach.arbiter import NEGLIGIBLE_COST_PER_GAME, select_priorities
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

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-08-06")


def a_finding(
    subject: str = "pin",
    kind: str = "missed_motif",
    rate: float = 0.30,
    peer_rate: float = 0.15,
    cost_wp: float | None = 100.0,
    games: int = 24,
) -> Finding:
    return Finding(
        section="S1",
        claim=Claim.of(kind=kind, subject=subject),
        measurement=Measurement(
            instances=20,
            distinct_games=10,
            games_with_data=games,
            rate=rate,
            peer_rate=peer_rate,
            cost_wp=cost_wp,
        ),
        provenance=PROVENANCE,
        confidence=Confidence(tier=ConfidenceTier.FOCUS, replicated=True),
        gap_type=GapType(
            hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED
        ),
        evidence=(Evidence(game_id="g1", ply=20, fen="8/8/8/8/8/8/8/K6k w - - 0 1"),),
    )


class TestTheCostItself:
    def test_it_is_per_game_not_per_instance(self):
        measurement = a_finding(cost_wp=48.0, games=24).measurement

        assert measurement.cost_per_game == pytest.approx(2.0)

    def test_a_claim_whose_instances_are_not_mistakes_has_none(self):
        assert a_finding(cost_wp=None).measurement.cost_per_game is None

    def test_no_games_is_not_a_division_by_zero(self):
        measurement = Measurement(
            instances=1, distinct_games=0, games_with_data=0, rate=0.1, cost_wp=10.0
        )

        assert measurement.cost_per_game is None


class TestRanking:
    def test_the_costlier_weakness_wins(self):
        cheap = a_finding(subject="pin", cost_wp=12.0)
        dear = a_finding(subject="fork", cost_wp=120.0)

        chosen = select_priorities((cheap, dear), limit=1).priorities

        assert chosen[0].finding.claim.subject == "fork"

    def test_cost_outranks_being_unusual(self):
        # The change D5 makes. Before this, the 4x-peers claim won on lift alone
        # while giving away a tenth as much.
        unusual = a_finding(subject="pin", rate=0.40, peer_rate=0.10, cost_wp=10.0)
        costly = a_finding(subject="fork", rate=0.20, peer_rate=0.15, cost_wp=200.0)

        chosen = select_priorities((unusual, costly), limit=1).priorities

        assert chosen[0].finding.claim.subject == "fork"

    def test_a_claim_that_can_price_itself_beats_one_that_cannot(self):
        # S5's design note argued for exactly this before it was measurable.
        priced = a_finding(subject="pin", rate=0.20, peer_rate=0.15, cost_wp=30.0)
        unpriced = a_finding(
            subject="backward", kind="concedes_weakness", rate=0.40, peer_rate=0.10, cost_wp=None
        )

        chosen = select_priorities((priced, unpriced), limit=1).priorities

        assert chosen[0].finding.claim.subject == "pin"

    def test_unpriced_claims_still_rank_among_themselves_by_how_unusual(self):
        # Both arms must be claims players actually differ on, or the one under
        # test gets neutral unusualness and the ranking this checks cannot
        # happen. `concedes_weakness.backward` was the stark arm until E84 found
        # it flat within band; `doubled` is the only subject of that kind left.
        mild = a_finding(subject="queen", kind="endgame_error",
                         rate=0.20, peer_rate=0.15, cost_wp=None)
        stark = a_finding(subject="rook", kind="endgame_error",
                          rate=0.40, peer_rate=0.10, cost_wp=None)

        chosen = select_priorities((mild, stark), limit=1).priorities

        assert chosen[0].finding.claim.subject == "rook"

    def test_confidence_still_comes_first(self):
        # A cheap certainty beats an expensive maybe: evidence quality is not
        # something a big number should be able to buy past.
        from dataclasses import replace

        weak = a_finding(subject="fork", cost_wp=500.0)
        weak = replace(weak, confidence=Confidence(tier=ConfidenceTier.WATCH, replicated=False))
        solid = a_finding(subject="pin", cost_wp=10.0)

        chosen = select_priorities((weak, solid), limit=1).priorities

        assert chosen[0].finding.claim.subject == "pin"


class TestSayingWhy:
    def test_the_cost_is_given_as_a_reason(self):
        chosen = select_priorities((a_finding(cost_wp=48.0, games=24),), limit=1).priorities

        assert any("2.0 points of win probability a game" in r for r in chosen[0].reasons)

    def test_a_negligible_cost_is_not_paraded(self):
        chosen = select_priorities((a_finding(cost_wp=0.1, games=24),), limit=1).priorities

        assert not any("win probability a game" in r for r in chosen[0].reasons)

    def test_an_unpriced_claim_says_so_rather_than_staying_silent(self):
        unpriced = a_finding(kind="concedes_weakness", subject="backward", cost_wp=None)

        chosen = select_priorities((unpriced,), limit=1).priorities

        assert any("choices, not mistakes" in r for r in chosen[0].reasons)


class TestTheReport:
    def profile(self, cost_wp: float | None):
        from chesscoach.arbiter import select_priorities as choose
        from chesscoach.planner import build_plan
        from chesscoach.profile.models import CorpusRef, PlayerProfile, PlayerRef

        finding = a_finding(cost_wp=cost_wp, games=24)
        return PlayerProfile(
            player=PlayerRef(source="lichess", username="alice", band="1400-1800"),
            corpus=CorpusRef(corpus_id="c1", n_games=24),
            findings=(finding,),
            plan=build_plan(choose((finding,)).priorities, created="2026-08-06"),
        )

    def test_the_player_is_told_what_it_costs(self):
        from chesscoach.explainer import render

        report = render(self.profile(cost_wp=48.0))

        assert "Costing you about 2.0 points of win probability a game" in report

    def test_and_that_it_is_a_ceiling_not_a_promise(self):
        # Stopping these mistakes does not mean playing perfectly instead.
        from chesscoach.explainer import render

        assert "the most you could get back" in render(self.profile(cost_wp=48.0))

    def test_an_unpriced_claim_makes_no_claim_about_cost(self):
        from chesscoach.explainer import render

        assert "Costing you" not in render(self.profile(cost_wp=None))

    def test_a_negligible_cost_is_left_out(self):
        from chesscoach.explainer import render

        assert "Costing you" not in render(self.profile(cost_wp=0.5))


class TestTheCostsDoNotAdd:
    """A single mistake can belong to two claims, so the totals overlap."""

    def render_with(self, findings):
        from chesscoach.arbiter import select_priorities as choose
        from chesscoach.explainer import render
        from chesscoach.planner import build_plan
        from chesscoach.profile.models import CorpusRef, PlayerProfile, PlayerRef

        return render(
            PlayerProfile(
                player=PlayerRef(source="lichess", username="alice", band="1400-1800"),
                corpus=CorpusRef(corpus_id="c1", n_games=24),
                findings=findings,
                plan=build_plan(choose(findings).priorities, created="2026-08-06"),
            )
        )

    def test_two_priced_findings_are_told_not_to_be_summed(self):
        report = self.render_with(
            (
                a_finding(subject="pin", cost_wp=48.0),
                a_finding(subject="fork", cost_wp=72.0),
            )
        )

        assert "should not be added together" in report

    def test_one_priced_finding_is_not_warned_about_a_sum_of_one(self):
        report = self.render_with(
            (
                a_finding(subject="pin", cost_wp=48.0),
                a_finding(subject="backward", kind="concedes_weakness", cost_wp=None),
            )
        )

        assert "should not be added together" not in report


def test_the_negligible_threshold_is_below_anything_worth_saying():
    assert 0 < NEGLIGIBLE_COST_PER_GAME < 1.0


def test_cost_survives_a_round_trip():
    from chesscoach.profile.io import from_dict, to_dict
    from chesscoach.profile.models import CorpusRef, PlayerProfile, PlayerRef

    profile = PlayerProfile(
        player=PlayerRef(source="lichess", username="alice"),
        corpus=CorpusRef(corpus_id="c1", n_games=24),
        findings=(a_finding(cost_wp=48.0),),
    )

    assert from_dict(to_dict(profile)).findings[0].measurement.cost_wp == 48.0
