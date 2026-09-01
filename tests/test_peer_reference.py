"""The rating-peer reference population.

Design: docs/notes/architecture.peer-reference.md

Its reason for existing is M5's finding: a measurement can be correct for every
player and still be a description of chess rather than of anyone. Only a
population can tell those apart.
"""

from __future__ import annotations

import pytest

from chesscoach.peers import _Contribution, ConditionMeasurement, PeerReference, PeerStats, build_reference


def measurement(key: str, errors: int, moves: int, games: int = 5) -> ConditionMeasurement:
    return ConditionMeasurement(
        claim_key=key,
        instances=errors,
        opportunities=moves,
        distinct_games=games,
        games_with_data=20,
    )


class TestConditionMeasurement:
    def test_rate_is_errors_over_opportunities(self):
        assert measurement("k", 3, 12).rate == 0.25

    def test_a_condition_that_never_arose_has_no_rate(self):
        assert measurement("k", 0, 0).rate is None


class TestBuildReference:
    def test_pools_players_within_a_band_and_time_control(self):
        reference = build_reference(
            [
                ("alice", (measurement("long_think", 10, 100),)),
                ("bob", (measurement("long_think", 20, 100),)),
            ],
            band="1400-1800",
            time_control="rapid",
            depth=15,
        )

        stats = reference.lookup("1400-1800", "rapid", "long_think")
        assert stats.rate == pytest.approx(0.15)
        assert stats.n_players == 2

    def test_records_the_depth_it_was_built_at(self):
        # Peer rates are no more comparable across depths than findings are.
        reference = build_reference(
            [("alice", (measurement("k", 1, 10),))], band="b", time_control="rapid", depth=15
        )

        assert reference.depth == 15

    def test_ignores_conditions_that_never_arose(self):
        reference = build_reference(
            [("alice", (measurement("k", 0, 0),))], band="b", time_control="rapid", depth=15
        )

        assert reference.lookup("b", "rapid", "k") is None

    def test_an_unknown_claim_has_no_entry(self):
        reference = build_reference(
            [("alice", (measurement("k", 1, 10),))], band="b", time_control="rapid", depth=15
        )

        assert reference.lookup("b", "rapid", "other") is None


class TestLeaveOneOut:
    def test_excludes_a_player_from_their_own_reference(self):
        # Comparing a player against a population containing themselves is
        # circular, and with a small reference it distorts their own deviation.
        reference = build_reference(
            [
                ("alice", (measurement("k", 90, 100),)),
                ("bob", (measurement("k", 10, 100),)),
                ("carol", (measurement("k", 10, 100),)),
            ],
            band="b",
            time_control="rapid",
            depth=15,
        )

        without_alice = reference.lookup("b", "rapid", "k", excluding="alice")

        assert without_alice.rate == pytest.approx(0.10)
        assert without_alice.n_players == 2

    def test_returns_nothing_when_excluding_leaves_no_one(self):
        reference = build_reference(
            [("alice", (measurement("k", 1, 10),))], band="b", time_control="rapid", depth=15
        )

        assert reference.lookup("b", "rapid", "k", excluding="alice") is None

    def test_exclusion_is_case_insensitive(self):
        reference = build_reference(
            [("Alice", (measurement("k", 1, 10),)), ("bob", (measurement("k", 1, 10),))],
            band="b",
            time_control="rapid",
            depth=15,
        )

        assert reference.lookup("b", "rapid", "k", excluding="alice").n_players == 1


class TestPersistence:
    def test_round_trips_through_json(self, tmp_path):
        reference = build_reference(
            [("alice", (measurement("k", 1, 10),)), ("bob", (measurement("k", 3, 10),))],
            band="1400-1800",
            time_control="rapid",
            depth=15,
        )
        path = tmp_path / "peers.json"

        reference.save(path)

        assert PeerReference.load(path) == reference

    def test_serialisation_is_stable(self, tmp_path):
        reference = build_reference(
            [("alice", (measurement("k", 1, 10),))], band="b", time_control="rapid", depth=15
        )
        first, second = tmp_path / "a.json", tmp_path / "b.json"

        reference.save(first)
        reference.save(second)

        assert first.read_bytes() == second.read_bytes()

    def test_merging_adds_a_band_without_disturbing_another(self):
        rapid = build_reference(
            [("alice", (measurement("k", 1, 10),))], band="b1", time_control="rapid", depth=15
        )
        blitz = build_reference(
            [("bob", (measurement("k", 5, 10),))], band="b2", time_control="blitz", depth=15
        )

        merged = rapid.merged_with(blitz)

        assert merged.lookup("b1", "rapid", "k").rate == pytest.approx(0.1)
        assert merged.lookup("b2", "blitz", "k").rate == pytest.approx(0.5)

    def test_refuses_to_merge_references_built_at_different_depths(self):
        shallow = build_reference(
            [("a", (measurement("k", 1, 10),))], band="b", time_control="rapid", depth=12
        )
        deep = build_reference(
            [("b", (measurement("k", 1, 10),))], band="b", time_control="rapid", depth=15
        )

        with pytest.raises(ValueError, match="depth"):
            shallow.merged_with(deep)


class TestPeerStats:
    def test_reports_an_interval(self):
        stats = PeerStats(rate=0.1, n_players=5, n_moves=500, instances=50)

        low, high = stats.ci95
        assert low < 0.1 < high


class TestClaimKeysAreCanonical:
    """Four shipped claims were mute because their baseline was keyed differently.

    Every claim in the system is `kind.subject.own`. The six development claims
    were written into the peer reference as `kind.subject`, because they predate
    the convention. Commit 20b1cef then normalised the **section** side through
    `_key()` -- correctly, it fixed the detection sheet -- and the reference on
    disk kept the old spelling. From that point `peer_rate("slow_development.
    book.own")` missed, `_assess` returned None for want of a baseline, and
    `slow_development`, `late_castling`, `repeat_move` and `pawn_error` produced
    **no findings for anybody**.

    I-07 recorded the same shape one pair of arms earlier and called it fixed
    because both sides went through one function. There was a third side: the
    stored artefact.

    Canonicalising on write and on read fixes the files that already exist
    rather than requiring an engine pass to reissue them.
    """

    def test_the_two_spellings_are_one_cell(self):
        reference = PeerReference(depth=15, cells={
            PeerReference.key("1400-1800", "rapid", "slow_development.book"): (
                _Contribution(player="a", instances=3, opportunities=10),
            ),
        })

        assert reference.lookup("1400-1800", "rapid", "slow_development.book.own") is not None

    def test_it_works_in_the_other_direction_too(self):
        reference = PeerReference(depth=15, cells={
            PeerReference.key("1400-1800", "rapid", "early_error.any.own"): (
                _Contribution(player="a", instances=3, opportunities=10),
            ),
        })

        assert reference.lookup("1400-1800", "rapid", "early_error.any") is not None

    def test_an_unrelated_claim_is_still_a_miss(self):
        # Canonicalising must not make every lookup succeed; a genuinely absent
        # claim is exactly what `None` is for.
        reference = PeerReference(depth=15, cells={
            PeerReference.key("1400-1800", "rapid", "early_error.any.own"): (
                _Contribution(player="a", instances=3, opportunities=10),
            ),
        })

        assert reference.lookup("1400-1800", "rapid", "fork.any.own") is None
