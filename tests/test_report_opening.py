"""The opening section of the report, and the gate in front of it.

Design: docs/notes/decisions.0016-a-run-store-for-the-swarm.md

The swarm's brief is a **candidate**, exactly as a guide link is, and the same
rule applies: recommending is endorsing and only the author endorses. So the
report reads the store through one door — `approved_brief` — and that door
returns nothing for a run nobody has approved.

The property these tests hold is that the door cannot be walked around.
"""

from __future__ import annotations

from chesscoach.explainer import _opening_section
from chesscoach.runstore import RunStore, StoredBrief


class FakePoint:
    def __init__(self, text: str, kind: str, kept: bool = True) -> None:
        self.text, self.kind = text, kind
        self.dropped_for = "" if kept else "names nothing on the board"
        self.grounding = None

    @property
    def kept(self) -> bool:
        return not self.dropped_for


def a_run(store: RunStore, opening: str = "Pirc Defense", finish: bool = True) -> int:
    run_id = store.start_run(opening, "qwen2.5:3b")
    store.record_page(run_id, "https://a.org/pirc", "a.org", "read")
    store.record_points(run_id, [
        FakePoint("Undermine the pawns on e4 and d4.", "plan"),
        FakePoint("White will keep a knight on e5.", "watch"),
        FakePoint("Develop in harmony.", "plan", kept=False),
    ])
    if finish:
        store.finish_run(run_id)
    return run_id


class TestNothingUnapprovedReachesAPlayer:
    def test_an_unapproved_run_is_not_returned(self, tmp_path):
        store = RunStore(tmp_path / "runs.db")
        a_run(store)

        assert store.approved_brief("Pirc Defense") is None

    def test_an_approved_run_is(self, tmp_path):
        store = RunStore(tmp_path / "runs.db")
        store.approve(a_run(store))

        brief = store.approved_brief("Pirc Defense")

        assert brief is not None
        assert brief.plans == ("Undermine the pawns on e4 and d4.",)

    def test_an_unfinished_run_is_never_returned_even_if_approved(self, tmp_path):
        # A run that died halfway has a partial brief. Approving it by accident
        # must not be enough to show it.
        store = RunStore(tmp_path / "runs.db")
        store.approve(a_run(store, finish=False))

        assert store.approved_brief("Pirc Defense") is None

    def test_approval_can_be_withdrawn(self, tmp_path):
        store = RunStore(tmp_path / "runs.db")
        run_id = a_run(store)
        store.approve(run_id)
        store.withdraw(run_id)

        assert store.approved_brief("Pirc Defense") is None

    def test_dropped_points_never_reach_the_brief(self, tmp_path):
        store = RunStore(tmp_path / "runs.db")
        store.approve(a_run(store))

        brief = store.approved_brief("Pirc Defense")

        assert all("harmony" not in p for p in brief.plans + brief.watches)

    def test_the_newest_approved_run_wins(self, tmp_path):
        store = RunStore(tmp_path / "runs.db")
        store.approve(a_run(store))
        second = a_run(store)
        store.record_points(second, [FakePoint("Play for the d5 break.", "plan")])
        store.approve(second)

        assert store.approved_brief("Pirc Defense").run_id == second

    def test_another_opening_gets_nothing(self, tmp_path):
        store = RunStore(tmp_path / "runs.db")
        store.approve(a_run(store))

        assert store.approved_brief("London System") is None

    def test_pending_lists_what_is_waiting_to_be_read(self, tmp_path):
        store = RunStore(tmp_path / "runs.db")
        a_run(store)

        assert [r.opening for r in store.pending()] == ["Pirc Defense"]

    def test_an_approved_run_is_no_longer_pending(self, tmp_path):
        store = RunStore(tmp_path / "runs.db")
        store.approve(a_run(store))

        assert store.pending() == []


class TestTheSectionItself:
    def brief(self, plans=("Undermine the pawns on e4 and d4.",),
              watches=("White will keep a knight on e5.",)) -> StoredBrief:
        return StoredBrief(
            run_id=1, opening="Pirc Defense", model="qwen2.5:3b", made_on="2026-08-28",
            plans=plans, watches=watches, sources=("https://a.org/pirc",),
        )

    def test_no_brief_means_no_section(self):
        # Silence, not "we have nothing for your opening": the player did not
        # ask, and a gap in our curation is not news to them.
        assert _opening_section(None) == []

    def test_a_brief_with_no_points_means_no_section(self):
        assert _opening_section(self.brief(plans=(), watches=())) == []

    def test_both_kinds_of_point_are_labelled_distinctly(self):
        text = "\n".join(_opening_section(self.brief()))

        assert "Aim for" in text
        assert "Watch for" in text

    def test_the_sources_are_printed(self):
        # The points are a local model's wording of sentences quoted from these
        # pages. Saying where they came from is the difference between a
        # citation and a claim of expertise (R-03).
        text = "\n".join(_opening_section(self.brief()))

        assert "https://a.org/pirc" in text

    def test_opponent_points_are_optional(self):
        text = "\n".join(_opening_section(self.brief(watches=())))

        assert "Aim for" in text
        assert "Watch for" not in text
