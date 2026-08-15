"""A costly-but-ordinary pattern must never read as a personal accusation.

The report now carries up to three priorities, and the last of them may have
reached the page on **cost** rather than on being unusual. Those are different
claims about a player and the difference is the whole of E25 condition 2:

    "Players at your level lose about 16 points a game to moves played in under
    two seconds" is a true statement about a population; "you play too fast" is a
    claim about a player that this measurement does not support.

The tests here are about wording, because wording is the entire mechanism.
"""

from __future__ import annotations

from datetime import date

import pytest

from chesscoach.arbiter import select_priorities
from chesscoach.explainer import SHARED_LABEL, render
from chesscoach.planner import build_plan
from chesscoach.profile.models import (
    Claim,
    Confidence,
    ConfidenceTier,
    CorpusRef,
    DeterminedBy,
    Evidence,
    Finding,
    GapType,
    GapTypeHypothesis,
    Measurement,
    PlayerProfile,
    PlayerRef,
    Provenance,
)

PROV = Provenance(
    engine="Stockfish 18", depth=15, corpus_id="c1", analysed_at="2026-08-15"
)


def a_finding(subject, tier, *, cost, peer_cost, rate, peer_rate, games=10):
    return Finding(
        section="S1",
        claim=Claim.of(kind="allowed_motif", subject=subject),
        measurement=Measurement(
            instances=12,
            distinct_games=games,
            games_with_data=53,
            rate=rate,
            baseline_rate=0.05,
            peer_rate=peer_rate,
            ci95=(0.06, 0.18),
            cost_wp=cost * 53,
            peer_cost_per_game=peer_cost,
        ),
        provenance=PROV,
        confidence=Confidence(tier=tier, replicated=True, reasons=()),
        gap_type=GapType(
            hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED
        ),
        evidence=(
            Evidence(
                game_id="g1", ply=20, fen="8/8/8/8/8/8/8/K6k w - - 0 1",
                move_played="a1a2", better_move="a1b1", loss_wp=12.0, note="x",
            ),
        ),
    )


UNUSUAL = dict(tier=ConfidenceTier.FOCUS, cost=4.2, peer_cost=3.9, rate=0.32, peer_rate=0.17)
ORDINARY = dict(tier=ConfidenceTier.WATCH, cost=7.3, peer_cost=8.7, rate=0.107, peer_rate=0.083)


def a_report(*findings):
    selection = select_priorities(
        tuple(f for f in findings if f.confidence.tier is not ConfidenceTier.WATCH),
        limit=3,
        also=tuple(f for f in findings if f.confidence.tier is ConfidenceTier.WATCH),
    )
    profile = PlayerProfile(
        player=PlayerRef(source="lichess", username="p", band="1400-1800"),
        corpus=CorpusRef(corpus_id="c1", n_games=53, game_ids=()),
        findings=findings,
        plan=build_plan(selection.priorities, created=date.today().isoformat()),
    )
    return render(profile)


class TestLabellingASharedPattern:
    def test_the_label_appears_before_the_numbers(self):
        # A reader who meets "11% against 8%" first has already concluded they
        # are unusual by the time any qualifier arrives.
        report = a_report(a_finding("hangingPiece", **ORDINARY))

        assert SHARED_LABEL in report
        assert report.index(SHARED_LABEL) < report.index("How often")

    def test_it_never_promises_a_negative_gain(self):
        # excess = 7.3 - 8.7 = -1.4. Printed with the usual wording this reads
        # "roughly -1.4 a game is what fixing this could get back".
        report = a_report(a_finding("hangingPiece", **ORDINARY))

        assert "-1.4" not in report
        assert "what fixing this could get back" not in report

    def test_it_still_states_what_the_pattern_costs(self):
        # The cost is the reason it is on the page at all. Dropping it would
        # leave a weakness with no stated reason to care.
        report = a_report(a_finding("hangingPiece", **ORDINARY))

        assert "7.3 points of win probability a game" in report

    def test_an_unusual_finding_carries_no_such_label(self):
        report = a_report(a_finding("fork", **UNUSUAL))

        assert SHARED_LABEL not in report

    def test_the_plan_step_repeats_the_label(self):
        # WHAT TO DO is read on its own by anyone skimming, so the qualifier has
        # to survive there too.
        report = a_report(a_finding("hangingPiece", **ORDINARY))

        plan = report[report.index("WHAT TO DO"):]
        assert SHARED_LABEL in plan


class TestOrderingIsTheFocus:
    def test_the_first_step_is_marked_when_there_are_several(self):
        report = a_report(a_finding("fork", **UNUSUAL), a_finding("hangingPiece", **ORDINARY))

        assert "Do this one first" in report

    def test_a_single_step_is_not_marked(self):
        # "Do this one first" against a list of one is noise.
        report = a_report(a_finding("fork", **UNUSUAL))

        assert "Do this one first" not in report

    def test_the_unusual_finding_outranks_the_expensive_one(self):
        # Cost fills what unusualness left empty; it never displaces it, however
        # much more the ordinary pattern costs (7.3 against 4.2 here).
        report = a_report(a_finding("fork", **UNUSUAL), a_finding("hangingPiece", **ORDINARY))

        assert report.index("fork") < report.index("hanging piece")


class TestTheHeadingMatchesTheClaim:
    def test_nothing_stands_out_when_nothing_stood_out(self):
        # Two of the twelve review players had no assertable finding and were
        # still given "WHAT STANDS OUT" over three ordinary patterns. The
        # heading asserted a diagnosis the peer comparison had declined to make.
        report = a_report(a_finding("hangingPiece", **ORDINARY))

        assert "WHAT COSTS YOU MOST" in report
        assert "WHAT STANDS OUT" not in report

    def test_it_says_plainly_that_the_player_is_unremarkable(self):
        report = a_report(a_finding("hangingPiece", **ORDINARY))

        assert "Nothing in your games is unusual for your rating band" in report

    def test_one_unusual_finding_restores_the_original_heading(self):
        report = a_report(a_finding("fork", **UNUSUAL), a_finding("hangingPiece", **ORDINARY))

        assert "WHAT STANDS OUT" in report
        assert "WHAT COSTS YOU MOST" not in report


class TestItSurvivesBeingSaved:
    def test_the_tier_round_trips_so_the_label_does_too(self, tmp_path):
        # `is_shared` reads the tier rather than a stored flag, so if the tier
        # were lost on reload a cost-ranked priority would silently re-render as
        # a peer-relative one — dropping the qualifier without dropping the claim,
        # which is the worst of the available failures. `report` and
        # `check-progress` both work from a reloaded profile.
        from chesscoach.profile.io import load_profile, save_profile

        finding = a_finding("hangingPiece", **ORDINARY)
        selection = select_priorities((), also=(finding,))
        profile = PlayerProfile(
            player=PlayerRef(source="lichess", username="p", band="1400-1800"),
            corpus=CorpusRef(corpus_id="c1", n_games=53, game_ids=()),
            findings=(finding,),
            plan=build_plan(selection.priorities, created=date.today().isoformat()),
        )

        path = tmp_path / "p.json"
        save_profile(profile, path)
        reloaded = load_profile(path)

        assert reloaded.findings[0].confidence.tier is ConfidenceTier.WATCH
        assert SHARED_LABEL in render(reloaded)


class TestTheEvidenceRuleStillHolds:
    def test_a_cost_ranked_priority_cites_positions(self):
        # CLAUDE.md hard rule 6 does not weaken because the claim arrived by a
        # different route.
        report = a_report(a_finding("hangingPiece", **ORDINARY))

        assert "For example game g1" in report

    @pytest.mark.parametrize("tier", [ConfidenceTier.WATCH, ConfidenceTier.FOCUS])
    def test_every_reported_finding_has_a_progress_check(self, tier):
        report = a_report(
            a_finding("hangingPiece", tier=tier, cost=7.3, peer_cost=8.7,
                      rate=0.107, peer_rate=0.083)
        )

        assert "WHAT WOULD SHOW IT WORKED" in report
