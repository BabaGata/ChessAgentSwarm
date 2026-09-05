"""Which replies count as punishing a mistake, and which one gets named.

Spec: docs/notes/design.punishment-validity.md — Option 3 + severity ordering

Two rules, and both came out of the author's objection that `allowed_motif`
currently fires only when the opponent's *single best* reply executes the motif:

  1. **Worth playing.** A punishment counts if playing it would not itself have
     been an inaccuracy — within `INACCURACY_WP` of the opponent's best reply.
     Not the very best; good enough. The "actually punishes" half is already
     enforced statically by the detectors, which only report a motif that wins
     material, so it costs nothing and is not re-tested here.
  2. **Severity.** When several punishments qualify, the one that gets named is
     the one reaching the highest win probability. Mate wins automatically,
     because mate *is* the maximum — no chess taxonomy is invented to say so.
"""

from __future__ import annotations

import pytest

from chesscoach.punishment import (
    WORTH_PLAYING_WP,
    Candidate,
    primary,
    qualifying,
)


def a_candidate(motif: str, uci: str, wp: float) -> Candidate:
    return Candidate(motif=motif, uci=uci, wp=wp)


class TestWorthPlaying:
    def test_the_best_reply_always_qualifies(self):
        got = qualifying((a_candidate("fork", "e4f6", 70.0),), best_wp=70.0)

        assert [p.motif for p in got] == ["fork"]

    def test_a_reply_that_is_nearly_as_good_qualifies(self):
        # The whole point: second-best forks are still real punishments.
        got = qualifying((a_candidate("fork", "e4f6", 66.0),), best_wp=70.0)

        assert [p.motif for p in got] == ["fork"]

    def test_a_reply_that_would_have_been_an_inaccuracy_does_not(self):
        # Losing more than INACCURACY_WP against the best is, by this project's
        # own standard, a mistake -- so the opponent would not have played it and
        # the player is not at fault for allowing it.
        got = qualifying((a_candidate("fork", "e4f6", 50.0),), best_wp=70.0)

        assert got == ()

    def test_the_boundary_is_inclusive(self):
        got = qualifying((a_candidate("fork", "e4f6", 70.0 - WORTH_PLAYING_WP),), best_wp=70.0)

        assert len(got) == 1

    def test_a_losing_fork_is_refused_however_forking_it_is(self):
        # The author's first case: a fork that costs the opponent the game is
        # not something the player was wrong to allow.
        got = qualifying((a_candidate("fork", "e4f6", 5.0),), best_wp=80.0)

        assert got == ()

    def test_several_replies_are_each_judged_on_their_own(self):
        got = qualifying(
            (
                a_candidate("fork", "e4f6", 68.0),
                a_candidate("pin", "c1g5", 40.0),
                a_candidate("skewer", "a1a8", 70.0),
            ),
            best_wp=70.0,
        )

        assert sorted(p.motif for p in got) == ["fork", "skewer"]

    def test_nothing_available_is_not_an_error(self):
        # An empty case must answer as empty, not as a pass (L-046).
        assert qualifying((), best_wp=70.0) == ()


class TestSeverity:
    def test_the_punishment_reaching_the_highest_win_probability_is_named(self):
        got = primary(
            qualifying(
                (a_candidate("fork", "e4f6", 68.0), a_candidate("skewer", "a1a8", 70.0)),
                best_wp=70.0,
            )
        )

        assert got is not None and got.motif == "skewer"

    def test_mate_outranks_material_without_a_table_of_which_beats_which(self):
        # "Checkmate should be prioritized" falls out of the arithmetic: mate is
        # 100 win probability, which nothing else can reach. No chess judgement
        # is encoded, so none needs a source (R-03).
        got = primary(
            qualifying(
                (
                    a_candidate("fork", "e4f6", 96.0),
                    a_candidate("backRankMate", "a1a8", 100.0),
                ),
                best_wp=100.0,
            )
        )

        assert got is not None and got.motif == "backRankMate"

    def test_the_others_are_still_returned_alongside(self):
        # Detection stays broad; only what gets *said* is ordered.
        got = qualifying(
            (a_candidate("fork", "e4f6", 96.0), a_candidate("backRankMate", "a1a8", 100.0)),
            best_wp=100.0,
        )

        assert len(got) == 2

    def test_ties_break_deterministically(self):
        # Same evidence must produce the same report every run.
        pair = (a_candidate("pin", "c1g5", 70.0), a_candidate("fork", "e4f6", 70.0))
        first = primary(qualifying(pair, best_wp=70.0))
        second = primary(qualifying(tuple(reversed(pair)), best_wp=70.0))

        assert first is not None and first.motif == second.motif

    def test_nothing_qualifying_has_no_primary(self):
        assert primary(()) is None


class TestCostIsNotCountedTwice:
    def test_one_mistake_names_one_punishment(self):
        # A single blunder can leave a fork, a pin and a skewer all available.
        # Counting its cost against each would treble it, and the arbiter ranks
        # on cost -- so one mistake must pay once.
        got = qualifying(
            (
                a_candidate("fork", "e4f6", 70.0),
                a_candidate("pin", "c1g5", 69.0),
                a_candidate("skewer", "a1a8", 68.0),
            ),
            best_wp=70.0,
        )

        assert len(got) == 3
        assert primary(got).motif == "fork"
