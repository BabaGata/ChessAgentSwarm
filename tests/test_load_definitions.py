"""The knowledge base has to reach the graph, or nothing can retrieve it.

Spec: docs/notes/experiments.e90-retrieval.md

`answer()` searches the graph. The graph held 1,159 book passages, 12 generated
rules and **no definitions** -- there was no loader for `knowledge.json` at all.
So asking "what is a fork" returned three unrelated passages, one of them an
ASCII board diagram, while a correct sourced definition of a fork sat in a file
the retriever never reads.

Two stores, one of them invisible.

The gate is the same one that governs everything else here: an entry reaches the
graph when it is **complete** -- a definition and a usable source -- and it is
marked `servable` only when the author has **endorsed** it. Loading is not
endorsing, so an unreviewed entry is retrievable for the author to inspect and
refused to a player by the same rule as before.
"""

from __future__ import annotations

import pytest

from chesscoach.knowledge import Entry, KnowledgeBase, Source

SOURCE = Source(url="https://example.org/x", publisher="Example",
                evidence_class="expert-consensus")


class FakeStore:
    """Records what would be written, so the loader is testable without Neo4j."""

    def __init__(self):
        self.nodes: list[tuple[str, str, str, bool]] = []

    def _run(self, *args, **kwargs):
        return []

    def _retrievable(self, label, node_id, text):
        self.nodes.append((label, node_id, text, True))


def a_base(**entries) -> KnowledgeBase:
    base = KnowledgeBase()
    for key, entry in entries.items():
        base.entries[key] = entry
    return base


class TestWhatReachesTheGraph:
    def test_a_complete_entry_is_loaded(self):
        from chesscoach.graph import definitions_to_load

        base = a_base(fork=Entry(key="fork", definition="A fork attacks two pieces.",
                                 quote="A fork attacks two pieces.", sources=(SOURCE,)))

        assert [d.key for d in definitions_to_load(base)] == ["fork"]

    def test_an_entry_with_no_source_is_refused(self):
        # Hard rule 7: every chess claim carries a source. An entry without one
        # is not loaded, however good the sentence looks.
        from chesscoach.graph import definitions_to_load

        base = a_base(fork=Entry(key="fork", definition="A fork attacks two pieces."))

        assert definitions_to_load(base) == ()

    def test_an_entry_with_no_definition_is_refused(self):
        from chesscoach.graph import definitions_to_load

        base = a_base(moved_into_attack=Entry(key="moved_into_attack", sources=(SOURCE,)))

        assert definitions_to_load(base) == ()

    def test_loading_is_not_endorsing(self):
        # An unreviewed entry is still loaded, so the author can retrieve and
        # inspect it -- but it must not be marked servable.
        from chesscoach.graph import definitions_to_load

        base = a_base(fork=Entry(key="fork", definition="A fork attacks two pieces.",
                                 quote="A fork attacks two pieces.", sources=(SOURCE,)))

        assert definitions_to_load(base)[0].servable is False

    def test_an_endorsed_entry_is_servable(self):
        from chesscoach.graph import definitions_to_load

        base = a_base(fork=Entry(key="fork", definition="A fork attacks two pieces.",
                                 quote="A fork attacks two pieces.", sources=(SOURCE,),
                                 reviewed=True))

        assert definitions_to_load(base)[0].servable is True

    def test_the_locator_names_the_claim_it_defines(self):
        # A retrieved definition has to be traceable back to the claim whose
        # entry it is, the same way a passage carries its book locator.
        from chesscoach.graph import definitions_to_load

        base = a_base(fork=Entry(key="fork", definition="A fork attacks two pieces.",
                                 quote="A fork attacks two pieces.", sources=(SOURCE,)))

        assert definitions_to_load(base)[0].locator == "definition://fork"

    def test_the_source_travels_with_it(self):
        from chesscoach.graph import definitions_to_load

        base = a_base(fork=Entry(key="fork", definition="A fork attacks two pieces.",
                                 quote="A fork attacks two pieces.", sources=(SOURCE,)))

        assert definitions_to_load(base)[0].publisher == "Example"
