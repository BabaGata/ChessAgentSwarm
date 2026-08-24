"""Evidence a chess player can actually check.

Screen: docs/notes/open-questions.md D18.

The author, after reading three reports against the games: moves print as UCI
where a player reads SAN, and games are cited by bare id with no colours,
opponent or date, so the game cannot be found in the Lichess app.

Both are cheap, and both make every *other* check faster — which is why they come
before the detector work rather than after it.
"""

from __future__ import annotations

import chess

from chesscoach.analysis.observations import Observation
from chesscoach.profile.models import Evidence

START = chess.Board().fen()
# After 1.e4 e5 2.Nf3 -- Black to move, so g8f6 is Nf6.
AFTER_THREE = "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2"


def an_observation(**overrides) -> Observation:
    defaults = dict(
        game_id="abc123", ply=4, mover="tal", mover_is_white=False,
        fen_before=AFTER_THREE, move_played="g8f6", best_move="b8c6",
        score_cp_before=0, score_cp_after=0, loss_wp=3.0, label=None,
        phase="opening", played_best=False, clock_before=None, clock_after=None,
        engine="stub", depth=15, opponent="capablanca", played_on="2026.07.14",
    )
    return Observation(**{**defaults, **overrides})


class TestObservationCarriesTheGameContext:
    def test_it_knows_the_opponent_and_the_date(self):
        o = an_observation()

        assert o.opponent == "capablanca"
        assert o.played_on == "2026.07.14"

    def test_both_are_optional_so_old_fixtures_still_build(self):
        o = Observation(
            game_id="g", ply=1, mover="p", mover_is_white=True, fen_before=START,
            move_played="e2e4", best_move="e2e4", score_cp_before=0,
            score_cp_after=0, loss_wp=0.0, label=None, phase="opening",
            played_best=True, clock_before=None, clock_after=None,
            engine="stub", depth=15,
        )

        assert o.opponent == ""
        assert o.played_on is None


class TestEvidenceFromObservation:
    def test_it_carries_the_context_across(self):
        e = Evidence.from_observation(an_observation(), note="a note")

        assert e.opponent == "capablanca"
        assert e.played_on == "2026.07.14"
        assert e.player_is_white is False
        assert e.note == "a note"

    def test_it_keeps_the_position_and_the_moves(self):
        e = Evidence.from_observation(an_observation(), better_move="b8c6")

        assert e.fen == AFTER_THREE
        assert e.move_played == "g8f6"
        assert e.better_move == "b8c6"

    def test_the_better_move_defaults_to_the_engines(self):
        assert Evidence.from_observation(an_observation()).better_move == "b8c6"


class TestSan:
    def test_a_move_is_shown_the_way_a_player_reads_it(self):
        assert Evidence.from_observation(an_observation()).played_san == "Nf6"

    def test_the_alternative_is_converted_too(self):
        assert Evidence.from_observation(an_observation()).better_san == "Nc6"

    def test_an_unreadable_position_falls_back_to_the_raw_move(self):
        # Never crash a whole report over one bad FEN; the UCI is still true.
        e = Evidence(game_id="g", ply=1, fen="not a fen", move_played="g8f6")

        assert e.played_san == "g8f6"

    def test_a_move_that_is_illegal_in_the_position_falls_back(self):
        e = Evidence(game_id="g", ply=1, fen=START, move_played="g8f6")

        assert e.played_san == "g8f6"

    def test_no_move_is_no_san(self):
        assert Evidence(game_id="g", ply=1, fen=START).played_san is None


class TestCitation:
    def test_it_names_the_colour_the_opponent_and_the_date(self):
        line = Evidence.from_observation(an_observation()).citation()

        assert "as Black" in line
        assert "capablanca" in line
        assert "2026.07.14" in line

    def test_it_gives_a_link_that_opens_at_the_right_move(self):
        # Lichess anchors on the half-move, which is what `ply` already is.
        line = Evidence.from_observation(an_observation()).citation()

        assert "lichess.org/abc123#4" in line

    def test_it_degrades_to_the_id_when_nothing_else_is_known(self):
        line = Evidence(game_id="abc123", ply=4, fen=START).citation()

        assert "abc123" in line


class TestOpponentReplyIsNotAnAlternative:
    """"(d7e5 was better)" was printed about the opponent's move.

    S1 stored the opponent's *punishing* move in `better_moves`, the same field
    the report renders as "X was better". For every `allowed_motif` claim the
    player was therefore told to play a move that was not theirs, and often was
    not legal for their colour at all — which is a large part of what the author
    meant by "examples are just wrong".
    """

    def test_an_opponent_reply_is_rendered_in_the_position_it_was_played_in(self):
        # White plays Nf3; the reply Nc6 is legal only after that move.
        after_e4_e5 = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
        e = Evidence(
            game_id="g", ply=3, fen=after_e4_e5, move_played="g1f3",
            opponent_reply="b8c6",
        )

        assert e.played_san == "Nf3"
        assert e.opponent_reply_san == "Nc6"

    def test_an_opponent_reply_is_never_presented_as_the_better_move(self):
        e = Evidence(game_id="g", ply=3, fen=START, move_played="e2e4",
                     opponent_reply="e7e5")

        assert e.better_move is None
        assert e.better_san is None
