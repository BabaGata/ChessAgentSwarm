"""Step 3 — what a weakness costs *above what it costs everyone else*.

Spec: docs/notes/design.short-history-prioritisation.md § layer 3

E15 ranked by raw cost and E17 found the defect: raw cost names
`advantage_error` for **70 %** of players, from a vocabulary of six. Costly is not
the same as *unusually* costly. That is L-012's mistake — a quantity compared
against nothing describes the rating band rather than the player — repeated for
costs after having been fixed for rates.

The recoverable quantity is the **excess**: what you give away beyond what a
player at your level gives away on the same claim. Playing this perfectly is not
on offer; playing it like your peers is, so the difference is what a plan can
honestly promise.
"""

from __future__ import annotations

import pytest

from chesscoach.peers import ConditionMeasurement, PeerReference, build_reference
from chesscoach.profile.models import Measurement

BAND, TC = "1400-1800", "rapid"


def a_measurement(key="missed_motif.pin.own", instances=10, opportunities=100,
                  games=20, cost_wp=60.0) -> ConditionMeasurement:
    return ConditionMeasurement(
        claim_key=key,
        instances=instances,
        opportunities=opportunities,
        distinct_games=8,
        games_with_data=games,
        cost_wp=cost_wp,
    )


def a_reference(*players) -> PeerReference:
    return build_reference(list(players), band=BAND, time_control=TC, depth=15)


class TestThePopulationCost:
    def test_it_is_per_game_across_the_population(self):
        # 60 + 40 win probability given away over 20 + 20 games.
        reference = a_reference(
            ("alice", (a_measurement(cost_wp=60.0, games=20),)),
            ("bob", (a_measurement(cost_wp=40.0, games=20),)),
        )

        assert reference.cost_per_game(BAND, TC, "missed_motif.pin.own") == pytest.approx(2.5)

    def test_the_player_is_left_out_of_their_own_comparison(self):
        reference = a_reference(
            ("alice", (a_measurement(cost_wp=1000.0, games=20),)),
            ("bob", (a_measurement(cost_wp=40.0, games=20),)),
        )

        peer = reference.cost_per_game(BAND, TC, "missed_motif.pin.own", excluding="alice")

        assert peer == pytest.approx(2.0)

    def test_a_claim_nobody_can_price_has_no_population_cost(self):
        reference = a_reference(("alice", (a_measurement(cost_wp=None),)))

        assert reference.cost_per_game(BAND, TC, "missed_motif.pin.own") is None

    def test_an_unknown_claim_has_none(self):
        assert a_reference(("alice", (a_measurement(),))).cost_per_game(
            BAND, TC, "nobody.knows.own"
        ) is None

    def test_players_who_cannot_price_it_do_not_dilute_those_who_can(self):
        # Averaging a missing cost as zero would understate the population and
        # inflate every player's excess against it.
        reference = a_reference(
            ("alice", (a_measurement(cost_wp=60.0, games=20),)),
            ("bob", (a_measurement(cost_wp=None, games=20),)),
        )

        assert reference.cost_per_game(BAND, TC, "missed_motif.pin.own") == pytest.approx(3.0)


class TestTheExcess:
    def test_it_is_what_is_left_after_the_population_is_paid(self):
        measurement = Measurement(
            instances=10, distinct_games=8, games_with_data=20, rate=0.1,
            cost_wp=100.0, peer_cost_per_game=2.0,
        )

        # 5.0 a game against a peer's 2.0.
        assert measurement.excess_cost_per_game == pytest.approx(3.0)

    def test_being_better_than_peers_is_not_a_gain_to_be_had(self):
        measurement = Measurement(
            instances=1, distinct_games=1, games_with_data=20, rate=0.01,
            cost_wp=20.0, peer_cost_per_game=5.0,
        )

        # 1.0 a game against 5.0: there is nothing here to recover.
        assert measurement.excess_cost_per_game == pytest.approx(0.0)

    def test_without_a_population_there_is_no_excess_to_state(self):
        measurement = Measurement(
            instances=10, distinct_games=8, games_with_data=20, rate=0.1, cost_wp=100.0
        )

        assert measurement.excess_cost_per_game is None

    def test_a_claim_that_is_not_a_mistake_still_has_none(self):
        measurement = Measurement(
            instances=10, distinct_games=8, games_with_data=20, rate=0.1,
            cost_wp=None, peer_cost_per_game=2.0,
        )

        assert measurement.excess_cost_per_game is None


class TestRankingUsesTheExcess:
    def a_finding(self, subject, cost_wp, peer_cost, rate=0.3, peer_rate=0.15):
        from chesscoach.profile.models import (
            Claim,
            Confidence,
            ConfidenceTier,
            DeterminedBy,
            Evidence,
            Finding,
            GapType,
            GapTypeHypothesis,
            Provenance,
        )

        return Finding(
            section="S1",
            claim=Claim.of(kind="missed_motif", subject=subject),
            measurement=Measurement(
                instances=20, distinct_games=10, games_with_data=24, rate=rate,
                peer_rate=peer_rate, cost_wp=cost_wp, peer_cost_per_game=peer_cost,
            ),
            provenance=Provenance(
                engine="stub", depth=15, corpus_id="c1", analysed_at="2026-08-06"
            ),
            confidence=Confidence(tier=ConfidenceTier.FOCUS, replicated=True),
            gap_type=GapType(
                hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED
            ),
            evidence=(Evidence(game_id="g1", ply=20, fen="8/8/8/8/8/8/8/K6k w - - 0 1"),),
        )

    def test_the_expensive_but_ordinary_claim_loses(self):
        # The exact failure E17 found: advantage_error is costly for everybody,
        # so a big raw number is not a reason to spend a month on it.
        ordinary = self.a_finding("fork", cost_wp=480.0, peer_cost=19.0)   # 20 vs 19
        unusual = self.a_finding("pin", cost_wp=120.0, peer_cost=1.0)      # 5 vs 1

        chosen = __import__(
            "chesscoach.arbiter", fromlist=["select_priorities"]
        ).select_priorities((ordinary, unusual), limit=1).priorities

        assert chosen[0].finding.claim.subject == "pin"

    def test_the_report_says_what_is_actually_recoverable(self):
        from chesscoach.arbiter import select_priorities

        finding = self.a_finding("pin", cost_wp=120.0, peer_cost=1.0)
        reasons = select_priorities((finding,), limit=1).priorities[0].reasons

        assert any("4.0" in r for r in reasons), reasons


def test_peer_cost_survives_a_round_trip():
    from chesscoach.profile.io import from_dict, to_dict
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
        PlayerProfile,
        PlayerRef,
        Provenance,
    )

    finding = Finding(
        section="S1",
        claim=Claim.of(kind="missed_motif", subject="pin"),
        measurement=Measurement(
            instances=10, distinct_games=8, games_with_data=20, rate=0.1,
            cost_wp=100.0, peer_cost_per_game=2.0,
        ),
        provenance=Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-08-06"),
        confidence=Confidence(tier=ConfidenceTier.FOCUS),
        gap_type=GapType(hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED),
        evidence=(Evidence(game_id="g1", ply=20, fen="8/8/8/8/8/8/8/K6k w - - 0 1"),),
    )
    profile = PlayerProfile(
        player=PlayerRef(source="lichess", username="alice"),
        corpus=CorpusRef(corpus_id="c1", n_games=20),
        findings=(finding,),
    )

    assert from_dict(to_dict(profile)).findings[0].measurement.peer_cost_per_game == 2.0


def test_a_reference_written_before_costs_still_loads(tmp_path):
    # v1 references carry no cost. They must load and simply have none, rather
    # than failing or inventing a zero.
    import json

    path = tmp_path / "old.json"
    path.write_text(
        json.dumps({
            "schema_version": 1,
            "depth": 15,
            "cells": {
                f"{BAND}|{TC}|missed_motif.pin.own": [
                    {"player": "alice", "instances": 10, "opportunities": 100}
                ]
            },
        }),
        encoding="utf-8",
    )

    reference = PeerReference.load(path)

    assert reference.lookup(BAND, TC, "missed_motif.pin.own").rate == pytest.approx(0.1)
    assert reference.cost_per_game(BAND, TC, "missed_motif.pin.own") is None
