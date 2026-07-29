"""Ingest: PGN parsing and corpus identity."""

from __future__ import annotations

from chesscoach.ingest.corpus import build_corpus
from chesscoach.ingest.pgn import parse_pgn_text

PGN = """[Event "Rapid Arena"]
[Site "https://lichess.org/abc123"]
[GameId "abc123"]
[White "alice"]
[Black "bob"]
[Result "1-0"]
[WhiteElo "1612"]
[BlackElo "1588"]
[TimeControl "600+0"]
[ECO "C02"]
[Opening "French Defense: Advance Variation"]
[Variant "Standard"]

1. e4 { [%clk 0:10:00] } 1... e6 { [%clk 0:09:58] } 2. d4 { [%clk 0:09:55] } 2... d5 { [%clk 0:09:50] } 1-0

[Event "Rapid Arena"]
[Site "https://lichess.org/def456"]
[GameId "def456"]
[White "carol"]
[Black "alice"]
[Result "0-1"]
[TimeControl "600+0"]
[Variant "Standard"]

1. d4 { [%clk 0:10:00] } 1... Nf6 { [%clk 0:09:57] } 0-1
"""


class TestParsePgn:
    def test_reads_every_game(self):
        games = parse_pgn_text(PGN)

        assert len(games) == 2

    def test_extracts_the_identifying_headers(self):
        game = parse_pgn_text(PGN)[0]

        assert game.game_id == "abc123"
        assert game.white == "alice"
        assert game.black == "bob"
        assert game.time_control == "600+0"
        assert game.eco == "C02"

    def test_extracts_clock_readings_per_ply(self):
        # S2 (decision process and clock behaviour) is the first agent, and it
        # needs these more than it needs the engine.
        game = parse_pgn_text(PGN)[0]

        assert game.clocks[:2] == (600.0, 598.0)

    def test_keeps_moves_in_order(self):
        game = parse_pgn_text(PGN)[0]

        assert game.moves[:2] == ("e2e4", "e7e6")

    def test_skips_non_standard_variants(self):
        games = parse_pgn_text(PGN.replace('[Variant "Standard"]', '[Variant "Crazyhouse"]', 1))

        assert len(games) == 1


class TestCorpusIdentity:
    def test_corpus_id_is_deterministic(self):
        games = parse_pgn_text(PGN)

        assert build_corpus("alice", games).corpus_id == build_corpus("alice", games).corpus_id

    def test_game_order_does_not_change_the_corpus_id(self):
        games = parse_pgn_text(PGN)

        assert build_corpus("alice", games).corpus_id == build_corpus("alice", games[::-1]).corpus_id

    def test_a_different_game_set_is_a_different_corpus(self):
        games = parse_pgn_text(PGN)

        assert build_corpus("alice", games).corpus_id != build_corpus("alice", games[:1]).corpus_id

    def test_counts_only_the_players_own_games(self):
        corpus = build_corpus("alice", parse_pgn_text(PGN))

        assert corpus.n_games == 2

    def test_collects_the_time_controls_present(self):
        corpus = build_corpus("alice", parse_pgn_text(PGN))

        assert corpus.time_controls == ("600+0",)
