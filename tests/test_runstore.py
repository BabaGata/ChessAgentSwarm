"""Keeping what the swarm did, so it can be asked about later.

Design: docs/notes/decisions.0016-a-run-store-for-the-swarm.md

The property that decided the design: **a run that dies halfway must leave
everything it had collected.** Rate limits and suspended search engines are the
failure that actually happens here, and a store that only wrote at the end would
lose the expensive part — the fetches and the model calls — every time.
"""

from __future__ import annotations

from dataclasses import dataclass

from chesscoach.grounding import Grounding
from chesscoach.runstore import RunStore


@dataclass(frozen=True)
class FakePoint:
    text: str
    kind: str
    grounding: Grounding | None = None
    dropped_for: str = ""

    @property
    def kept(self) -> bool:
        return not self.dropped_for


def a_grounding(novelty: float = 0.2) -> Grounding:
    return Grounding(grounded=True, ungrounded_moves=(), novelty=novelty,
                     novel_words=())


class TestWritingAsTheRunProceeds:
    def test_a_run_that_never_finished_keeps_its_pages_and_notes(self, tmp_path):
        store = RunStore(tmp_path / "runs.db")
        run_id = store.start_run("Pirc Defense", "qwen2.5:3b")
        page_id = store.record_page(run_id, "https://a.org/x", "a.org", "read")
        store.record_notes(run_id, page_id, ["Black aims to stay flexible."])
        store.close()

        # Reopened as a separate connection, as a later process would.
        again = RunStore(tmp_path / "runs.db")
        run = again.runs()[0]

        assert run.finished is False
        assert run.pages == 1
        assert run.notes == 1

    def test_a_finished_run_is_marked(self, tmp_path):
        store = RunStore(tmp_path / "runs.db")
        run_id = store.start_run("Pirc Defense", "m")
        store.finish_run(run_id)

        assert store.runs()[0].finished is True

    def test_unfinished_runs_can_be_listed(self, tmp_path):
        store = RunStore(tmp_path / "runs.db")
        store.finish_run(store.start_run("Finished", "m"))
        store.start_run("Abandoned", "m")

        assert [r.opening for r in store.unfinished()] == ["Abandoned"]


class TestWhatIsKept:
    def build(self, tmp_path) -> RunStore:
        store = RunStore(tmp_path / "runs.db")
        run_id = store.start_run("Pirc Defense", "qwen2.5:3b", searcher="searx")
        store.record_page(run_id, "", "reddit.com", "skipped")
        good = store.record_page(run_id, "https://a.org/x", "a.org", "read")
        store.record_notes(run_id, good, ["Black aims to stay flexible.",
                                          "Black undermines the centre later."])
        store.record_page(run_id, "https://v.example/x", "v.example", "unusable",
                          skip_reason="video")
        store.record_points(run_id, [
            FakePoint("Undermine the pawns on e4 and d4.", "plan", a_grounding()),
            FakePoint("Develop in harmony.", "plan", a_grounding(),
                      "names nothing on the board"),
            FakePoint("White keeps the centre.", "watch", a_grounding(0.5),
                      "novelty 50% over 45%"),
        ])
        store.finish_run(run_id)
        return store

    def test_dropped_points_are_kept_with_their_reason(self, tmp_path):
        # Why the swarm rejects things is invisible in the brief and is exactly
        # what tuning needs.
        store = self.build(tmp_path)
        points = store.points(store.runs()[0].id)

        assert [p["kept"] for p in points] == [1, 0, 0]
        assert "names nothing" in points[1]["dropped_for"]

    def test_novelty_travels_with_the_point(self, tmp_path):
        store = self.build(tmp_path)

        assert store.points(store.runs()[0].id)[2]["novelty"] == 0.5

    def test_notes_carry_their_publisher(self, tmp_path):
        store = self.build(tmp_path)

        assert {n["publisher"] for n in store.notes(store.runs()[0].id)} == {"a.org"}

    def test_a_skipped_domain_is_recorded_without_a_fetch(self, tmp_path):
        store = self.build(tmp_path)
        skipped = [p for p in store.pages(store.runs()[0].id)
                   if p["outcome"] == "skipped"]

        assert [p["publisher"] for p in skipped] == ["reddit.com"]
        assert skipped[0]["url"] == ""

    def test_counts_come_back_on_the_run_row(self, tmp_path):
        run = self.build(tmp_path).runs()[0]

        assert (run.pages, run.notes, run.points_kept) == (3, 2, 1)


class TestTheQuestionsTheStoreExistsFor:
    def test_drop_reasons_are_counted_across_runs(self, tmp_path):
        store = RunStore(tmp_path / "runs.db")
        for _ in range(2):
            run_id = store.start_run("Pirc Defense", "m")
            store.record_points(run_id, [
                FakePoint("x", "plan", a_grounding(), "names nothing on the board"),
                FakePoint("y", "plan", a_grounding()),
            ])

        reasons = store.drop_reasons()

        assert reasons[0]["dropped_for"] == "names nothing on the board"
        assert reasons[0]["n"] == 2

    def test_productive_domains_rank_by_notes(self, tmp_path):
        store = RunStore(tmp_path / "runs.db")
        run_id = store.start_run("Pirc Defense", "m")
        thin = store.record_page(run_id, "https://thin.org/x", "thin.org", "read")
        rich = store.record_page(run_id, "https://rich.org/x", "rich.org", "read")
        store.record_notes(run_id, thin, ["one sentence."])
        store.record_notes(run_id, rich, ["one.", "two.", "three."])

        assert [d["publisher"] for d in store.productive_domains()][0] == "rich.org"

    def test_runs_can_be_filtered_by_opening(self, tmp_path):
        store = RunStore(tmp_path / "runs.db")
        store.start_run("Pirc Defense", "m")
        store.start_run("London System", "m")

        assert [r.opening for r in store.runs(opening="Pirc Defense")] == \
            ["Pirc Defense"]

    def test_the_latest_run_for_an_opening_is_the_newest(self, tmp_path):
        store = RunStore(tmp_path / "runs.db")
        first = store.start_run("Pirc Defense", "m")
        second = store.start_run("Pirc Defense", "m")

        assert store.latest("Pirc Defense").id == second
        assert first != second

    def test_an_opening_never_run_has_no_latest(self, tmp_path):
        assert RunStore(tmp_path / "runs.db").latest("Grob Opening") is None


class TestTheFileItself:
    def test_the_schema_is_created_on_first_use(self, tmp_path):
        path = tmp_path / "nested" / "runs.db"

        RunStore(path).close()

        assert path.exists()

    def test_opening_an_existing_store_does_not_wipe_it(self, tmp_path):
        store = RunStore(tmp_path / "runs.db")
        store.start_run("Pirc Defense", "m")
        store.close()

        assert len(RunStore(tmp_path / "runs.db").runs()) == 1


class TestAFailedSearchIsVisible:
    """The commonest failure here is a search that cannot run at all.

    Opening the run row after the search was the first version, and it left no
    row when the search raised -- so a rate-limited run was indistinguishable
    from a run that never happened. That is the absence this store exists to
    prevent.
    """

    def test_a_search_that_raises_still_leaves_a_run(self, tmp_path):
        from chesscoach.opening_agent import SearchUnavailable
        from chesscoach.opening_swarm import OpeningSwarm

        class DeadSearcher:
            name = "dead"

            def search_detailed(self, _gap):
                raise SearchUnavailable("every engine is unresponsive")

        store = RunStore(tmp_path / "runs.db")
        swarm = OpeningSwarm(searcher=DeadSearcher(), fetch=lambda _u: "",
                             store=store, transport=lambda _u, _b: {"response": "x"})

        try:
            swarm.run("Owen Defense")
        except SearchUnavailable:
            pass

        run = store.runs()[0]
        assert run.opening == "Owen Defense"
        assert run.finished is False
        assert run.pages == 0
