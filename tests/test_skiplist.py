"""Sites the swarm learns not to read, and the guards on that learning.

Design: docs/notes/decisions.0015-a-learned-skip-list-and-a-bullet-brief.md

This is the only persistent state in the project a language model may write to,
and a poisoned skip list fails **silently and forever** — the swarm would simply
stop finding a good source and nothing would say why. So the guards get more
tests than the feature.

The load-bearing one: a domain that has ever produced a sentence worth keeping
can never be skipped, whatever a model votes.
"""

from __future__ import annotations

from chesscoach.skiplist import REASONS, SkipEntry, SkipList, domain_of


class TestMatchingASite:
    def test_a_listed_domain_is_skipped(self):
        assert SkipList.seeded().skips("https://www.tiktok.com/@x/video/1")

    def test_a_subdomain_belongs_to_its_site(self):
        # blog.duolingo.com walked straight past an exact-match list.
        skiplist = SkipList((SkipEntry("duolingo.com", "social", "seed"),))

        assert skiplist.skips("https://blog.duolingo.com/popular-chess-openings/")

    def test_a_lookalike_domain_is_not_the_same_site(self):
        skiplist = SkipList((SkipEntry("reddit.com", "forum", "seed"),))

        assert skiplist.skips("https://notreddit.com/x") is False

    def test_an_unlisted_site_is_not_skipped(self):
        assert SkipList.seeded().skips("https://thechessworld.com/articles/x") is False

    def test_www_is_not_part_of_the_name(self):
        assert domain_of("https://www.reddit.com/r/chess") == "reddit.com"

    def test_a_bare_domain_reads_as_itself(self):
        assert domain_of("tiktok.com") == "tiktok.com"


class TestTheGuardsOnLearning:
    def test_a_site_that_has_helped_can_never_be_skipped(self):
        # The load-bearing guard. Without it a model can delete a source the
        # swarm has already been helped by, and nothing would report the loss.
        skiplist = SkipList().mark_useful("https://thechessworld.com/a")

        after = skiplist.add("thechessworld.com", "shop", "assessor", "2026-08-28")

        assert len(after) == 0
        assert after.skips("https://thechessworld.com/b") is False

    def test_a_reason_outside_the_list_is_refused(self):
        after = SkipList().add("example.org", "i did not like it", "assessor", "x")

        assert len(after) == 0

    def test_every_allowed_reason_is_accepted(self):
        for reason in REASONS:
            assert len(SkipList().add("example.org", reason, "assessor", "x")) == 1

    def test_a_path_cannot_be_skipped_only_a_domain(self):
        after = SkipList().add("https://example.org/one-bad-article", "shop",
                               "assessor", "x")

        assert after.entries[0].domain == "example.org"

    def test_something_that_is_not_a_domain_is_refused(self):
        assert len(SkipList().add("localhost", "shop", "assessor", "x")) == 0
        assert len(SkipList().add("", "shop", "assessor", "x")) == 0

    def test_a_site_is_not_listed_twice(self):
        once = SkipList().add("example.org", "shop", "assessor", "x")
        twice = once.add("example.org", "video", "assessor", "x")

        assert len(twice) == 1

    def test_adding_returns_a_new_list_and_leaves_the_old_one_alone(self):
        before = SkipList()

        before.add("example.org", "shop", "assessor", "x")

        assert len(before) == 0


class TestWhatTheAuthorCanSee:
    def test_learned_entries_are_distinguishable_from_the_seed(self):
        skiplist = SkipList.seeded().add("example.org", "shop", "assessor", "2026-08-28")

        assert [e.domain for e in skiplist.learned] == ["example.org"]

    def test_an_entry_records_who_added_it_and_when(self):
        entry = SkipList().add("example.org", "shop", "assessor", "2026-08-28").entries[0]

        assert entry.added_by == "assessor"
        assert entry.added_on == "2026-08-28"


class TestPersistence:
    def test_a_saved_list_reloads_with_its_guards(self, tmp_path):
        path = tmp_path / "skiplist.json"
        skiplist = (SkipList.seeded()
                    .add("example.org", "shop", "assessor", "2026-08-28")
                    .mark_useful("https://thechessworld.com/a"))
        skiplist.save(path)

        again = SkipList.load(path)

        assert again.skips("https://example.org/x")
        assert "thechessworld.com" in again.useful
        assert len(again.add("thechessworld.com", "shop", "assessor", "x")) == len(again)

    def test_a_missing_file_gives_the_seed_rather_than_nothing(self, tmp_path):
        skiplist = SkipList.load(tmp_path / "absent.json")

        assert skiplist.skips("https://www.tiktok.com/x")
