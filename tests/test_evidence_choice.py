"""Which instances a claim cites, when not all of them can demonstrate it.

The author, marking the detection sheet, rejected rows across **four different
detectors** for one reason:

    "this exact move did not had any significant wp loss and should not be
     counted"                                            -- late_castling

    "White played good moves, completing the development"  -- slow_development

    "if it is suspected to be an out of book move then it should have at least
     significant loss in wp"                             -- out_of_book

    "The move didn't had any significant wp loss after all"
                                                         -- miscounted_exchange

**37 of 163 cited rows cost 0.0 wp.** They are not four problems; they are one,
and it is a problem of *citation* rather than of counting.

`late_castling` and `slow_development` are **habit** claims measured over
opportunities, not over errors, so a move that cost nothing can honestly be an
instance of the habit. What is wrong is showing that move as the evidence: the
reader takes "here is the move" to mean "the system says this move was a
mistake", and it is not saying that. The claim is measuring correctly and
pointing badly.

So the counting is untouched and the **choice of what to show** changes.
"""

from __future__ import annotations

from chesscoach.analysis.labels import ErrorLabel
from chesscoach.analysis.observations import Observation
from chesscoach.sections.base import worth_citing


def observation(ply: int, loss: float) -> Observation:
    return Observation(
        game_id=f"g{ply}", ply=ply, mover="alice", mover_is_white=True,
        fen_before="8/8/8/8/8/8/8/K6k w - - 0 1", move_played="a1a2",
        best_move="a1a2", score_cp_before=0, score_cp_after=0, loss_wp=loss,
        label=ErrorLabel.INACCURACY if loss else None, phase="opening",
        played_best=not loss, clock_before=None, clock_after=None,
        engine="stub", depth=15,
    )


class TestChoosingWhatToShow:
    def test_it_prefers_instances_that_cost_something(self):
        free = [observation(ply, 0.0) for ply in range(1, 20)]
        costly = [observation(50, 12.0), observation(52, 8.0)]

        chosen = worth_citing(free + costly, 2, seed="k")

        assert {o.ply for o in chosen} == {50, 52}

    def test_it_tops_up_from_the_free_ones_rather_than_showing_fewer(self):
        """A claim with one costly instance still gets its four citations. The
        alternative -- show only what cost something -- would make a claim look
        thinner than the evidence behind it."""
        rows = [observation(1, 9.0)] + [observation(ply, 0.0) for ply in (2, 3, 4, 5)]

        chosen = worth_citing(rows, 4, seed="k")

        assert len(chosen) == 4
        assert chosen[0].ply == 1

    def test_with_nothing_costly_it_still_cites(self):
        """A habit claim can legitimately have no costly instance at all, and
        silence would read as "no evidence" rather than "no cost" (L-046)."""
        rows = [observation(ply, 0.0) for ply in (1, 2, 3)]

        chosen = worth_citing(rows, 2, seed="k")

        assert len(chosen) == 2

    def test_it_is_deterministic(self):
        rows = [observation(ply, 0.0) for ply in range(1, 30)]

        first = worth_citing(rows, 4, seed="k")
        second = worth_citing(rows, 4, seed="k")

        assert [o.ply for o in first] == [o.ply for o in second]

    def test_a_different_claim_gets_a_different_sample(self):
        """Seeded per claim, so two claims over the same games do not illustrate
        themselves with the same four positions."""
        rows = [observation(ply, 0.0) for ply in range(1, 40)]

        assert [o.ply for o in worth_citing(rows, 4, seed="a")] != [
            o.ply for o in worth_citing(rows, 4, seed="b")
        ]

    def test_it_does_not_rank_by_cost(self):
        """**Preferring costly is not choosing the worst.** Ranking would make
        every claim's evidence its own high-water mark, and a reader who infers
        typical severity from the sample would be misled -- the failure the
        `Evidence` docstring's "never cherry-picked" was written against. Within
        the costly ones the choice stays random."""
        costly = [observation(ply, float(ply)) for ply in range(1, 30)]

        chosen = worth_citing(costly, 4, seed="k")

        assert [o.ply for o in chosen] != sorted(
            (o.ply for o in costly), reverse=True
        )[:4]

    def test_asking_for_more_than_exists_gives_what_exists(self):
        rows = [observation(1, 5.0), observation(2, 0.0)]

        assert len(worth_citing(rows, 10, seed="k")) == 2
