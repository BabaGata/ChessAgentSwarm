"""How much theory a player knows, per opening rather than as one number.

Spec: docs/notes/design.better-claims.md

`out_of_book` was one tally over every game, and it separates players strongly
(8.3x within band). But *"you leave theory early"* is not a thing anyone can
study. **Which** opening they leave early is, and the opening family is already
carried on every game -- `GameDevelopment.family` -- so the split costs nothing
new to compute.

This is the pattern `endgame_error` already uses and that E84 measured working:
it splits by the **kind of position**, which is a body of knowledge a player can
own or lack, and all six of its splits separate players. Knowledge is patchy in
a way skill is not.

The aggregate stays. A player with thirty games across eight families has about
four games each, which the confidence policy will refuse -- so the per-family
claims fire only where a player actually has a repertoire, and the total is the
safety net that always has enough data.
"""

from __future__ import annotations

import chess
import pytest

from chesscoach.development_norms import DevelopmentNorms
from chesscoach.opening_development import ANY_OPENING, OUT_OF_BOOK, count
from chesscoach.openings import OpeningBook

from test_opening_development import PLAYER, observations_for

# White in both, and in both it is **White's** move that leaves the book -- which
# the comment used to claim and the moves did not deliver. `out_of_book` now
# charges only the player's own departure, so a line whose last theory move is
# Black's produces nothing for White and the split had no Sicilian to find.
#
# Italian leaves at ply 11 (`Bg5`), Sicilian at ply 15 (`a3`); the Najdorf line
# below is book to ply 14, so `f3` -- which is theory -- became `a3`, which is
# not.
ITALIAN = ("e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "O-O", "Nf6", "d3", "d6",
           "Bg5", "Bg4", "Nbd2", "Nd4")
SICILIAN = ("e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4", "Nf6", "Nc3", "a6",
            "Be3", "e5", "Nb3", "Be6", "a3", "Be7")


@pytest.fixture(scope="module")
def two_family_games():
    rows = []
    for n, sans in enumerate((ITALIAN, ITALIAN, SICILIAN)):
        rows.extend(observations_for(sans, f"g{n:03d}"))
    return tuple(rows)


@pytest.fixture(scope="module")
def book():
    return OpeningBook.load()


def counted(games, book):
    return count(games, PLAYER, book, DevelopmentNorms({}))


def keys_of(tallies) -> set[str]:
    return {k for k in tallies if k.startswith(OUT_OF_BOOK)}


class TestTheSplit:
    def test_the_total_is_still_there(self, two_family_games, book):
        tallies = counted(two_family_games, book)

        assert f"{OUT_OF_BOOK}.{ANY_OPENING}" in keys_of(tallies)

    def test_each_family_played_gets_its_own_tally(self, two_family_games, book):
        tallies = counted(two_family_games, book)

        assert f"{OUT_OF_BOOK}.Italian Game" in keys_of(tallies)
        assert f"{OUT_OF_BOOK}.Sicilian Defense" in keys_of(tallies)

    def test_a_family_never_played_gets_nothing(self, two_family_games, book):
        # An absent opening must be absent, not present with a zero -- a claim
        # measured over no games is the empty case answering like a real one.
        assert f"{OUT_OF_BOOK}.French Defense" not in keys_of(counted(two_family_games, book))

    def test_the_family_tallies_sum_to_the_total(self, two_family_games, book):
        tallies = counted(two_family_games, book)
        total = tallies[f"{OUT_OF_BOOK}.{ANY_OPENING}"]
        parts = [t for k, t in tallies.items()
                 if k.startswith(OUT_OF_BOOK) and not k.endswith(ANY_OPENING)]

        assert sum(p.instances for p in parts) == total.instances
        assert sum(p.opportunities for p in parts) == total.opportunities

    def test_every_instance_is_still_citeable(self, two_family_games, book):
        # `Measurement` refuses a claim reporting more instances than it can
        # point at, and the split must not lose the evidence.
        for key, tally in counted(two_family_games, book).items():
            if key.startswith(OUT_OF_BOOK):
                assert len(tally.examples) <= tally.instances
