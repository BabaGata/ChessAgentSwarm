"""Fetching a whole band's worth of players, one PGN file per player.

The layout `build-peer-reference` reads: `<name>.pgn`, filename is the username.
That layout was produced only by `experiments/e01-engine-throughput/fetch_games.py`,
which is why success criterion 6 was not actually met.

The rules that matter are the ones that decide *what does not get written*: a
player too thin to diagnose, a player already in the corpus, a player whose fetch
fails. Each of those silently going into the reference would corrupt population
rates in a way no later step could detect.
"""

from __future__ import annotations

import pytest

from chesscoach.ingest.lichess import LichessUnavailable
from chesscoach.ingest.population import MIN_GAMES, fetch_population


def pgn(n_games: int) -> str:
    return "".join(
        f'[Event "Rated rapid game"]\n[Site "x{i}"]\n\n1. e4 e5 1-0\n\n' for i in range(n_games)
    )


@pytest.fixture
def out(tmp_path):
    return tmp_path / "corpus"


class TestFetchingAPopulation:
    def wire(self, monkeypatch, candidates, fetcher):
        monkeypatch.setattr(
            "chesscoach.ingest.population.find_candidate_players",
            lambda low, high, wanted: candidates,
        )
        monkeypatch.setattr("chesscoach.ingest.population.fetch_games_pgn", fetcher)
        monkeypatch.setattr("chesscoach.ingest.population.time.sleep", lambda _s: None)

    def test_it_writes_one_file_per_player_named_by_username(self, monkeypatch, out):
        self.wire(monkeypatch, [("alice", 1500), ("bob", 1600)], lambda n, g, perf_types=None: pgn(40))

        written = fetch_population(out, players=2, games=40, band=(1400, 1800))

        assert {p.name for p in out.glob("*.pgn")} == {"alice.pgn", "bob.pgn"}
        assert [w.username for w in written] == ["alice", "bob"]
        assert written[0].n_games == 40

    def test_a_player_too_thin_to_diagnose_is_not_written(self, monkeypatch, out):
        # A four-game player in the reference contributes almost no moves and a
        # very noisy rate, which is worse than not being there at all.
        self.wire(
            monkeypatch,
            [("thin", 1500), ("alice", 1500)],
            lambda name, g, perf_types=None: pgn(2 if name == "thin" else 40),
        )

        written = fetch_population(out, players=5, games=40, band=(1400, 1800))

        assert [w.username for w in written] == ["alice"]
        assert not (out / "thin.pgn").exists()

    def test_a_failed_fetch_skips_that_player_and_continues(self, monkeypatch, out):
        def fetcher(name, games, perf_types=None):
            if name == "gone":
                raise LichessUnavailable("no such user")
            return pgn(40)

        self.wire(monkeypatch, [("gone", 1500), ("alice", 1500)], fetcher)

        assert [w.username for w in fetch_population(out, players=5, games=40,
                                                    band=(1400, 1800))] == ["alice"]

    def test_players_already_in_the_output_are_not_refetched(self, monkeypatch, out):
        # Re-running to top up a corpus must not re-download what is there, and
        # must never write a second copy under a different case.
        out.mkdir(parents=True)
        (out / "alice.pgn").write_text(pgn(40), encoding="utf-8")
        fetched: list[str] = []

        def fetcher(name, games, perf_types=None):
            fetched.append(name)
            return pgn(40)

        self.wire(monkeypatch, [("Alice", 1500), ("bob", 1600)], fetcher)

        fetch_population(out, players=5, games=40, band=(1400, 1800))

        assert fetched == ["bob"]

    def test_an_excluded_directory_keeps_a_held_out_set_held_out(self, monkeypatch, out, tmp_path):
        # E27's whole value was that its players had touched nothing. Whatever
        # rebuilds the reference has to be able to keep it that way.
        spent = tmp_path / "held-out"
        spent.mkdir()
        (spent / "alice.pgn").write_text(pgn(40), encoding="utf-8")
        fetched: list[str] = []

        self.wire(monkeypatch, [("alice", 1500), ("bob", 1600)],
                  lambda n, g, perf_types=None: (fetched.append(n), pgn(40))[1])

        fetch_population(out, players=5, games=40, band=(1400, 1800), exclude=(spent,))

        assert fetched == ["bob"]

    def test_it_stops_at_the_number_asked_for(self, monkeypatch, out):
        self.wire(monkeypatch, [(f"p{i}", 1500) for i in range(10)], lambda n, g, perf_types=None: pgn(40))

        assert len(fetch_population(out, players=3, games=40, band=(1400, 1800))) == 3

    def test_it_asks_for_more_candidates_than_players(self, monkeypatch, out):
        # The band filter, the exclusions and MIN_GAMES all thin the list, so a
        # request for exactly N players returns fewer than N almost every time.
        asked: list[int] = []
        monkeypatch.setattr(
            "chesscoach.ingest.population.find_candidate_players",
            lambda low, high, wanted: (asked.append(wanted), [])[1],
        )
        monkeypatch.setattr("chesscoach.ingest.population.time.sleep", lambda _s: None)

        fetch_population(out, players=30, games=40, band=(1400, 1800))

        assert asked == [30 * 4]

    def test_min_games_is_high_enough_to_be_worth_diagnosing(self):
        assert MIN_GAMES >= 15


class TestFetchingOneSpeed:
    """A stratum has to be built from games actually played at that speed.

    Found by running the documented chain rather than asserting it. Fetching all
    three diagnostic speeds into one directory and then calling
    `build-peer-reference --time-control rapid` files blitz and classical games
    under `rapid`: the label is applied by the command, not read from the games.

    The damage is silent and total. `SectionContext._mixed` looks a claim up
    once per speed in the player's own mix, so a blitz-heavy player meets a
    reference that has no blitz stratum, every lookup returns None, and both the
    peer comparison and the band notes vanish — leaving a report that still
    renders and is quietly running on own-baseline evidence alone.
    """

    def test_a_speed_is_passed_through_to_the_fetch(self, monkeypatch, tmp_path):
        asked: list[tuple] = []

        monkeypatch.setattr(
            "chesscoach.ingest.population.find_candidate_players",
            lambda low, high, wanted: [("alice", 1500)],
        )
        monkeypatch.setattr("chesscoach.ingest.population.time.sleep", lambda _s: None)
        monkeypatch.setattr(
            "chesscoach.ingest.population.fetch_games_pgn",
            lambda name, games, perf_types: (asked.append(perf_types), pgn(40))[1],
        )

        fetch_population(tmp_path / "c", players=1, games=40, band=(1400, 1800), speed="blitz")

        assert asked == [("blitz",)]

    def test_without_a_speed_it_fetches_what_the_swarm_diagnoses_on(self, monkeypatch, tmp_path):
        from chesscoach.ingest.lichess import DIAGNOSTIC_PERF_TYPES

        asked: list[tuple] = []
        monkeypatch.setattr(
            "chesscoach.ingest.population.find_candidate_players",
            lambda low, high, wanted: [("alice", 1500)],
        )
        monkeypatch.setattr("chesscoach.ingest.population.time.sleep", lambda _s: None)
        monkeypatch.setattr(
            "chesscoach.ingest.population.fetch_games_pgn",
            lambda name, games, perf_types: (asked.append(perf_types), pgn(40))[1],
        )

        fetch_population(tmp_path / "c", players=1, games=40, band=(1400, 1800))

        assert asked == [DIAGNOSTIC_PERF_TYPES]
