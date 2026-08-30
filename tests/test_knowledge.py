"""The knowledge base, and the gate that keeps unreviewed drafts off a report.

Design: docs/notes/design.knowledge-base.md

The rules under test are the project's, not this module's: `reviewed` means the
**author** endorsed it, every chess claim carries a source (hard rule 7), and
nothing may quietly render empty in front of a player (L-046).
"""

from __future__ import annotations

import pytest

from chesscoach.knowledge import Entry, KnowledgeBase, NotEndorsed, Source


def source(evidence_class: str = "single-expert") -> Source:
    return Source(url="https://en.wikibooks.org/wiki/Chess_Strategy",
                  publisher="Wikibooks", evidence_class=evidence_class)


def drafted(key: str = "fork", **kw) -> Entry:
    return Entry(
        key=key,
        definition=kw.pop("definition", "A move attacking two pieces at once."),
        quote=kw.pop("quote", "A fork is a move that attacks two pieces."),
        sources=kw.pop("sources", (source(),)),
        drafted_by="qwen2.5:3b",
        **kw,
    )


class TestNothingUnreviewedReachesAPlayer:
    def test_a_drafted_entry_is_not_shown(self):
        kb = KnowledgeBase()
        kb.draft(drafted())
        assert kb.for_player("fork") is None

    def test_an_endorsed_entry_is_shown(self):
        kb = KnowledgeBase()
        kb.draft(drafted())
        kb.endorse("fork")
        shown = kb.for_player("fork")
        assert shown["what"]
        assert shown["links"][0]["publisher"] == "Wikibooks"

    def test_drafting_can_never_endorse(self):
        # The same rule as `reviewed` on a guide link and `approve` in the run
        # store: the agent must not be able to sign off its own work.
        kb = KnowledgeBase()
        kb.draft(drafted(reviewed=True))
        assert kb.get("fork").reviewed is False

    def test_a_redraft_does_not_overwrite_a_reviewed_entry(self):
        # Re-running the swarm must not silently discard a human judgement.
        kb = KnowledgeBase()
        kb.draft(drafted())
        kb.endorse("fork", note="checked against the detector")
        kb.draft(drafted(definition="something the model preferred"))
        entry = kb.get("fork")
        assert entry.reviewed is True
        assert entry.note == "checked against the detector"
        assert "preferred" not in entry.definition

    def test_showing_an_unreviewed_entry_raises_rather_than_blanking(self):
        # A blank explanation in front of a player is the L-046 shape with an
        # audience: it reads as "there is nothing to say".
        with pytest.raises(NotEndorsed):
            drafted().shown_to_player()


class TestEveryClaimCarriesASource:
    def test_an_entry_with_no_source_cannot_be_endorsed(self):
        kb = KnowledgeBase()
        kb.draft(drafted(sources=()))
        with pytest.raises(NotEndorsed):
            kb.endorse("fork")

    def test_folklore_is_not_a_usable_source(self):
        # R-03: LLM-generated chess advice is not a source. Recorded so it can
        # be refused, rather than left out and silently accepted.
        kb = KnowledgeBase()
        kb.draft(drafted(sources=(source("folklore"),)))
        assert kb.get("fork").has_source is False
        with pytest.raises(NotEndorsed):
            kb.endorse("fork")

    def test_an_unknown_evidence_class_is_refused_at_construction(self):
        with pytest.raises(ValueError):
            Source(url="u", publisher="p", evidence_class="vibes")

    def test_only_usable_sources_are_offered_as_links(self):
        kb = KnowledgeBase()
        kb.draft(drafted(sources=(source("folklore"), source("expert-consensus"))))
        kb.endorse("fork")
        assert len(kb.for_player("fork")["links"]) == 1


class TestWhatStillNeedsWriting:
    def test_missing_names_the_keys_with_no_usable_entry(self):
        kb = KnowledgeBase()
        kb.draft(drafted("fork"))
        kb.draft(drafted("pin", definition="", sources=()))
        assert kb.missing(("fork", "pin", "skewer")) == ("pin", "skewer")

    def test_pending_lists_what_the_author_has_to_read(self):
        kb = KnowledgeBase()
        kb.draft(drafted("fork"))
        kb.draft(drafted("pin"))
        kb.endorse("fork")
        assert [e.key for e in kb.pending()] == ["pin"]


class TestRoundTrip:
    def test_it_survives_save_and_load(self, tmp_path):
        kb = KnowledgeBase()
        kb.draft(drafted("fork", not_this=("a double attack both pieces survive",)))
        kb.endorse("fork")
        path = tmp_path / "knowledge.json"
        kb.save(path)
        back = KnowledgeBase.load(path)
        entry = back.get("fork")
        assert entry.reviewed is True
        assert entry.not_this == ("a double attack both pieces survive",)
        assert entry.sources[0].publisher == "Wikibooks"

    def test_a_missing_file_is_an_empty_base_not_an_error(self, tmp_path):
        assert len(KnowledgeBase.load(tmp_path / "absent.json")) == 0
