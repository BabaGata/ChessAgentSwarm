"""The author can write an entry, not only accept or reject one.

Spec: docs/notes/design.better-claims.md

`review.py` offered one verb: endorse what the swarm drafted. For four claims
the swarm has nothing to offer -- they are this project's own error categories
and no source defines them -- so the only door was shut for exactly the entries
that need a human most.

Three fields become writable, and each has a different rule:

* `--definition` replaces the sentence. It is the author's, so it needs the
  author's own source, and `--source` is required with it. Without that an
  entry would carry a claim about chess with nothing behind it (hard rule 7).
* `--not-this` is the field no agent may ever fill, and the docstring already
  said so.
* `--note` records why, and was already there.

Writing is still not endorsing. `--definition` leaves the entry unreviewed
unless `--endorse` is given in the same breath, so an author can draft, read it
back, and decide separately.
"""

from __future__ import annotations

import pytest

from chesscoach.knowledge import Entry, KnowledgeBase, NotEndorsed, Source

SOURCE = Source(url="https://example.org/x", publisher="Example",
                evidence_class="expert-consensus")


@pytest.fixture
def base():
    kb = KnowledgeBase()
    kb.entries["moved_into_attack"] = Entry(key="moved_into_attack")
    kb.entries["fork"] = Entry(key="fork", definition="A fork attacks two.",
                               quote="A fork attacks two.", sources=(SOURCE,))
    return kb


class TestWritingADefinition:
    def test_the_author_can_supply_one_where_the_swarm_found_nothing(self, base):
        from chesscoach.knowledge import write_definition

        write_definition(base, "moved_into_attack",
                         "Moving a piece to a square where it can be taken.",
                         source=SOURCE)

        entry = base.get("moved_into_attack")
        assert entry.definition.startswith("Moving a piece")
        assert entry.complete

    def test_it_is_marked_as_the_authors_own(self, base):
        from chesscoach.knowledge import write_definition

        write_definition(base, "moved_into_attack", "Anything.", source=SOURCE)

        assert base.get("moved_into_attack").drafted_by == "author"

    def test_writing_is_not_endorsing(self, base):
        from chesscoach.knowledge import write_definition

        write_definition(base, "moved_into_attack", "Anything.", source=SOURCE)

        assert base.get("moved_into_attack").reviewed is False

    def test_a_definition_without_a_source_is_refused(self, base):
        # Hard rule 7 does not bend for the author: a chess claim carries a
        # source or it is not stored.
        from chesscoach.knowledge import write_definition

        with pytest.raises(NotEndorsed):
            write_definition(base, "moved_into_attack", "Anything.", source=None)

    def test_it_replaces_rather_than_appends(self, base):
        from chesscoach.knowledge import write_definition

        write_definition(base, "fork", "The author's own wording.", source=SOURCE)

        assert base.get("fork").definition == "The author's own wording."

    def test_an_unknown_key_can_be_created(self, base):
        from chesscoach.knowledge import write_definition

        write_definition(base, "brand_new_claim", "A definition.", source=SOURCE)

        assert base.get("brand_new_claim") is not None


class TestTheFieldNoAgentMayFill:
    def test_not_this_is_writable_by_the_author(self, base):
        from chesscoach.knowledge import write_not_this

        write_not_this(base, "fork", ("a double attack by two different pieces",))

        assert base.get("fork").not_this == ("a double attack by two different pieces",)

    def test_it_does_not_disturb_the_definition(self, base):
        from chesscoach.knowledge import write_not_this

        write_not_this(base, "fork", ("something",))

        assert base.get("fork").definition == "A fork attacks two."
