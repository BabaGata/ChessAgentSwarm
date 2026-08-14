"""build-peer-reference must refuse to file games under a speed they were not played at.

`--time-control` labels a whole directory. Nothing checked that the label was
true, and the failure it allows is silent: a mixed directory built as `rapid`
produces a reference with a rapid stratum and no blitz one, so a blitz-heavy
player's `_mixed` lookups all return None and both the peer comparison and the
band notes drop out of a report that still renders and still looks complete.

Found by running the documented reproduction chain end to end rather than
asserting it — the exact thing success criterion 6 is for.

Every game carries its own `TimeControl`, so the label is checkable against the
games it is being applied to. Refused rather than warned: a warning in a
several-minute engine run scrolls past, and the resulting reference is
indistinguishable from a good one afterwards.
"""

from __future__ import annotations

import pytest

from chesscoach.peers import declared_speed_is_wrong


def game(time_control: str):
    class _Game:
        pass

    g = _Game()
    g.time_control = time_control
    return g


BLITZ = "180+2"     # 180 + 40*2 = 260s -> blitz
RAPID = "600+0"     # 600s -> rapid
CLASSICAL = "1800+0"


class TestStratumGuard:
    def test_a_matching_directory_passes(self):
        games = [game(RAPID)] * 9 + [game(BLITZ)]

        assert declared_speed_is_wrong(games, "rapid") is None

    def test_a_blitz_directory_declared_rapid_is_refused(self):
        games = [game(BLITZ)] * 9 + [game(RAPID)]

        problem = declared_speed_is_wrong(games, "rapid")

        assert problem is not None
        assert "blitz" in problem

    def test_an_evenly_mixed_directory_is_refused(self):
        # Neither speed is a majority, so whichever label is applied is wrong for
        # about half the games.
        games = [game(BLITZ)] * 10 + [game(RAPID)] * 10

        assert declared_speed_is_wrong(games, "rapid") is not None

    def test_a_bare_majority_is_not_enough(self):
        # The real corpus this was first run against: 88 rapid, 51 blitz, 1
        # classical. A majority test passes it and 51 blitz games are filed as
        # rapid anyway. Purity is the property that matters, not plurality.
        games = [game(RAPID)] * 88 + [game(BLITZ)] * 51 + [game(CLASSICAL)]

        problem = declared_speed_is_wrong(games, "rapid")

        assert problem is not None
        assert "blitz" in problem

    def test_games_with_no_readable_control_do_not_decide_it(self):
        # Correspondence games have no speed. They should not be able to outvote
        # the games that do.
        games = [game(RAPID)] * 5 + [game(None)] * 20

        assert declared_speed_is_wrong(games, "rapid") is None

    def test_no_readable_speeds_at_all_is_not_an_accusation(self):
        # Nothing to check against is not the same as a mismatch, and refusing
        # here would block a legitimate corpus of unusual controls.
        assert declared_speed_is_wrong([game(None), game(None)], "rapid") is None

    @pytest.mark.parametrize("speed,control", [("blitz", BLITZ), ("classical", CLASSICAL)])
    def test_it_works_for_every_stratum_not_just_rapid(self, speed, control):
        assert declared_speed_is_wrong([game(control)] * 10, speed) is None
        assert declared_speed_is_wrong([game(control)] * 10, "rapid") is not None

    def test_the_message_names_both_speeds_so_the_fix_is_obvious(self):
        problem = declared_speed_is_wrong([game(BLITZ)] * 10, "rapid")

        assert "blitz" in problem and "rapid" in problem

    def test_a_contaminated_directory_is_not_told_its_label_is_wrong(self):
        # "these games are mostly rapid, not rapid" was the first thing this
        # printed. The label is right here; the contamination is the fault, and
        # saying otherwise sends the reader to change the wrong flag.
        problem = declared_speed_is_wrong([game(RAPID)] * 88 + [game(BLITZ)] * 51, "rapid")

        assert "mostly rapid, not rapid" not in problem
        assert "51 of these 139 games are not rapid" in problem
