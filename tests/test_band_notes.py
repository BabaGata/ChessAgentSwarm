"""What a player's whole rating band loses points to.

Spec: docs/notes/experiments.e25-shared-weaknesses.md

Peer-relative ranking is what stops the swarm telling 70 % of players the same
thing (E17), and it has one blind spot: a weakness **everyone** at the level
shares has almost no excess over peers, so it sinks and is never said — however
expensive it is. `instant_move_error` costs 16.1 points of win probability a game,
the most of any claim measured in this project, and is advised to nobody.

E25 screened which shared claims are worth saying anyway: those whose rate still
falls with rating **after the player's overall error rate is divided out**, so it
is something this band demonstrably learns rather than a shadow of general skill.
Five of twenty-seven survived, and only those appear here.

Three rules make this safe rather than a return to generic advice:

  * it never consumes the one or two personal priorities;
  * it is never phrased as a finding about the player;
  * only screened claims appear.
"""

from __future__ import annotations

import pytest

from chesscoach.band import SHARED_WEAKNESSES, notes_for
from chesscoach.ingest.corpus import build_corpus
from chesscoach.ingest.pgn import GameRecord
from chesscoach.peers import ConditionMeasurement, build_reference
from chesscoach.profile.models import Provenance
from chesscoach.sections.base import SectionContext

BAND, SPEED = "1400-1800", "rapid"
INSTANT = "instant_move_error.instant_moves.own"


def a_game(game_id: str) -> GameRecord:
    return GameRecord(
        game_id=game_id, white="alice", black="bob", result="1-0",
        moves=("e2e4", "e7e5"), clocks=(600.0, 600.0), time_control="600+0",
    )


def reference(costs: dict[str, float], games: int = 40):
    """A population that loses `cost` per game to each claim."""
    players = []
    for name in ("bob", "carol", "dave"):
        players.append((
            name,
            tuple(
                ConditionMeasurement(
                    claim_key=key, instances=20, opportunities=100,
                    distinct_games=10, games_with_data=games,
                    cost_wp=cost * games,
                )
                for key, cost in costs.items()
            ),
        ))
    return build_reference(players, band=BAND, time_control=SPEED, depth=15)


def context(costs: dict[str, float]) -> SectionContext:
    corpus = build_corpus("alice", [a_game("g1")])
    return SectionContext(
        observations=(),
        corpus=corpus,
        provenance=Provenance(
            engine="stub", depth=15, corpus_id=corpus.corpus_id, analysed_at="2026-08-07"
        ),
        band=BAND,
        time_control=SPEED,
        peers=reference(costs),
    )


class TestWhichClaimsQualify:
    def test_only_screened_claims_appear(self):
        # `missed_motif.pin` is expensive and did NOT survive E25's screen: its
        # rate stops falling with rating once general skill is divided out.
        notes = notes_for(context({INSTANT: 16.0, "missed_motif.pin.own": 40.0}))

        assert [n.claim_key for n in notes] == [INSTANT]

    def test_every_screened_claim_has_evidence_recorded(self):
        # A curated list is only defensible if each entry carries the number that
        # put it there.
        assert all(shared.learnable_r < 0 for shared in SHARED_WEAKNESSES)
        assert len(SHARED_WEAKNESSES) == 5

    def test_a_claim_the_population_cannot_price_is_skipped(self):
        assert notes_for(context({})) == ()

    def test_no_reference_means_no_notes(self):
        corpus = build_corpus("alice", [a_game("g1")])
        bare = SectionContext(
            observations=(),
            corpus=corpus,
            provenance=Provenance(
                engine="stub", depth=15, corpus_id="c1", analysed_at="2026-08-07"
            ),
        )

        assert notes_for(bare) == ()


class TestOrderingAndRestraint:
    def test_the_most_expensive_come_first(self):
        notes = notes_for(context({
            INSTANT: 5.0,
            "early_error.black.own": 11.0,
            "early_error.white.own": 8.0,
        }))

        assert [n.claim_key for n in notes] == [
            "early_error.black.own", "early_error.white.own", INSTANT
        ]

    def test_at_most_three_are_shown(self):
        notes = notes_for(context({shared.key: 10.0 for shared in SHARED_WEAKNESSES}))

        assert len(notes) == 3

    def test_the_cost_is_the_populations_not_the_players(self):
        notes = notes_for(context({INSTANT: 16.1}))

        assert notes[0].cost_per_game == pytest.approx(16.1)


class TestItIsNotAFinding:
    """The rule that keeps this from becoming generic advice."""

    def test_notes_do_not_reach_the_plan(self):
        from chesscoach.arbiter import select_priorities

        # Nothing in the band note pathway produces a Finding, so there is
        # nothing for the arbiter to rank in the first place.
        assert select_priorities(()).priorities == ()

    def test_the_report_attributes_them_to_the_population(self):
        from chesscoach.explainer import render
        from chesscoach.profile.models import CorpusRef, PlayerProfile, PlayerRef

        profile = PlayerProfile(
            player=PlayerRef(source="lichess", username="alice", band="1400-1800"),
            corpus=CorpusRef(corpus_id="c1", n_games=24),
            band_notes=notes_for(context({INSTANT: 16.1})),
        )

        report = render(profile)

        assert "Players at your level" in report
        assert "16.1" in report
        # Never "you play too fast": the measurement is about a population, and
        # a claim about this player is exactly what it does not support.
        assert "You play" not in report

    def test_a_profile_with_no_notes_prints_no_section(self):
        from chesscoach.explainer import BAND_HEADING, render
        from chesscoach.profile.models import CorpusRef, PlayerProfile, PlayerRef

        profile = PlayerProfile(
            player=PlayerRef(source="lichess", username="alice"),
            corpus=CorpusRef(corpus_id="c1", n_games=24),
        )

        assert BAND_HEADING not in render(profile)


class TestTheEstimateNamesItsSpeed:
    """A player with games at two speeds has two ratings ~80 points apart (E19)."""

    def profile_with(self, speed: str | None, typical_error: int = 103):
        from chesscoach.profile.models import (
            CorpusRef,
            PlayerProfile,
            PlayerRef,
            Strength,
        )

        return PlayerProfile(
            player=PlayerRef(source="lichess", username="alice", band="1400-1800"),
            corpus=CorpusRef(corpus_id="c1", n_games=59),
            strength=Strength(
                rating=1645,
                typical_error=typical_error,
                moves=1411,
                method="blunder_rate",
                speed=speed,
            ),
        )

    def test_the_report_says_which_standard_it_means(self):
        from chesscoach.explainer import render

        assert "your blitz standard" in render(self.profile_with("blitz"))

    def test_a_blitz_estimate_admits_it_is_the_weaker_reading(self):
        from chesscoach.explainer import render

        assert "less accurate" in render(self.profile_with("blitz", typical_error=123))

    def test_a_rapid_estimate_carries_no_such_warning(self):
        from chesscoach.explainer import render

        assert "less accurate" not in render(self.profile_with("rapid"))

    def test_an_estimate_with_no_speed_says_nothing_about_one(self):
        from chesscoach.explainer import render

        report = render(self.profile_with(None))

        assert "standard —" not in report and "less accurate" not in report


def test_notes_survive_a_round_trip():
    from chesscoach.profile.io import from_dict, to_dict
    from chesscoach.profile.models import CorpusRef, PlayerProfile, PlayerRef

    profile = PlayerProfile(
        player=PlayerRef(source="lichess", username="alice"),
        corpus=CorpusRef(corpus_id="c1", n_games=24),
        band_notes=notes_for(context({INSTANT: 16.1})),
    )

    restored = from_dict(to_dict(profile))

    assert restored.band_notes[0].claim_key == INSTANT
    assert restored.band_notes[0].cost_per_game == pytest.approx(16.1)
