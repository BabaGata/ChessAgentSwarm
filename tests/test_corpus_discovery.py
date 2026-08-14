"""Finding players to build a reference population from.

Spec: docs/notes/vision.md success criterion 6 — *the system is documented well
enough that a third party can reproduce it from this vault.*

That criterion was **asserted and not met**. `build-peer-reference` takes a
directory of ~84 players' games and nothing in the product produced one: the
discovery-and-fetch code lived in `experiments/e01-engine-throughput/`, so a
stranger following the README stopped at the first step that needed it.

This is the same complaint that produced the `coach` command — *"using the swarm
meant running a script from an experiments directory before you could run the
swarm at all"* — reappearing one level further back.

Discovery reads finished arena standings, which is reproducible in **shape**
rather than in exact content: the tournaments differ every day, so a third party
gets a different sample of the same population. That is the honest guarantee, and
it is stated rather than implied.
"""

from __future__ import annotations

import json

import pytest

from chesscoach.ingest.lichess import LichessUnavailable, find_candidate_players

BAND = (1400, 1800)


def standings(*players) -> bytes:
    return json.dumps(
        {"standing": {"players": [{"name": n, "rating": r} for n, r in players]}}
    ).encode()


def tournaments(*ids) -> bytes:
    return json.dumps({"finished": [{"id": i} for i in ids]}).encode()


class TestFindingPlayers:
    def responder(self, monkeypatch, pages: dict[str, bytes]):
        calls: list[str] = []

        def fake(url, accept="application/json"):
            calls.append(url)
            for fragment, payload in pages.items():
                if fragment in url:
                    return payload
            return json.dumps({}).encode()

        monkeypatch.setattr("chesscoach.ingest.lichess._get", fake)
        monkeypatch.setattr("chesscoach.ingest.lichess.time.sleep", lambda _s: None)
        return calls

    def test_it_returns_players_inside_the_band(self, monkeypatch):
        self.responder(monkeypatch, {
            "/tournament/t1": standings(("alice", 1500), ("bob", 2400), ("carol", 1700)),
            "/tournament": tournaments("t1"),
        })

        found = find_candidate_players(*BAND, wanted=10)

        assert [name for name, _ in found] == ["alice", "carol"]

    def test_it_stops_once_it_has_enough(self, monkeypatch):
        self.responder(monkeypatch, {
            "/tournament/t1": standings(("a", 1500), ("b", 1600), ("c", 1700)),
            "/tournament": tournaments("t1", "t2", "t3"),
        })

        assert len(find_candidate_players(*BAND, wanted=2)) == 2

    def test_a_tournament_that_fails_does_not_end_the_search(self, monkeypatch):
        # One bad tournament out of several is not a reason to return nothing.
        def fake(url, accept="application/json"):
            if "/tournament/bad" in url:
                raise LichessUnavailable("HTTP 404")
            if "/tournament/good" in url:
                return standings(("alice", 1500))
            return tournaments("bad", "good")

        monkeypatch.setattr("chesscoach.ingest.lichess._get", fake)
        monkeypatch.setattr("chesscoach.ingest.lichess.time.sleep", lambda _s: None)

        assert [n for n, _ in find_candidate_players(*BAND, wanted=5)] == ["alice"]

    def test_players_without_a_rating_are_skipped(self, monkeypatch):
        self.responder(monkeypatch, {
            "/tournament/t1": json.dumps(
                {"standing": {"players": [{"name": "ghost"}, {"name": "alice", "rating": 1500}]}}
            ).encode(),
            "/tournament": tournaments("t1"),
        })

        assert [n for n, _ in find_candidate_players(*BAND, wanted=5)] == ["alice"]

    def test_the_same_player_is_never_returned_twice(self, monkeypatch):
        # Arena regulars appear in many tournaments, and a corpus with one player
        # counted twice would weight them double in every population rate.
        self.responder(monkeypatch, {
            "/tournament/t1": standings(("alice", 1500)),
            "/tournament/t2": standings(("alice", 1500), ("bob", 1600)),
            "/tournament": tournaments("t1", "t2"),
        })

        found = [n for n, _ in find_candidate_players(*BAND, wanted=5)]

        assert found == ["alice", "bob"]

    def test_no_tournaments_is_an_error_not_an_empty_list(self, monkeypatch):
        # Silence here would look like "the band is empty" rather than "Lichess
        # told us nothing", and the caller would fetch a corpus of zero players.
        self.responder(monkeypatch, {"/tournament": json.dumps({}).encode()})

        with pytest.raises(LichessUnavailable):
            find_candidate_players(*BAND, wanted=5)

    def test_it_is_polite_between_tournaments(self, monkeypatch):
        slept: list[float] = []
        monkeypatch.setattr("chesscoach.ingest.lichess.time.sleep", slept.append)
        monkeypatch.setattr(
            "chesscoach.ingest.lichess._get",
            lambda url, accept="application/json": (
                tournaments("t1", "t2") if url.endswith("/tournament")
                else standings(("x", 1500))
            ),
        )

        find_candidate_players(*BAND, wanted=99)

        assert slept, "a free public API deserves a pause between calls"
