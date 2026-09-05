"""The best phrase for a concept must actually be asked.

Spec: docs/notes/experiments.e89-why-nothing-usable.md

`queries` wrapped the topic phrase in "what is a ..." and "why ... matters" and
never asked it plainly. Measured against the local search instance, the wrapping
is what returned nothing usable:

    'outpost chess'               -> en.wikipedia.org/wiki/Outpost_(chess)
    'what is a outpost chess'     -> chessmetrics.com, missiveapp.com

    'undefended pawn chess'       -> en.wikipedia.org/wiki/Chess_tactic
    'what is a undefended pawn'   -> en.wikipedia.org/wiki/Turochamp

The wrapping also produces ungrammatical queries -- "what is a castling in
chess" -- because it prefixes an article to a phrase that may not take one.
"""

from __future__ import annotations

import pytest

from chesscoach.knowledge_swarm import TERMS, KnowledgeScout, terms_for


def queries_for(key: str) -> list[str]:
    return KnowledgeScout(searcher=None, skiplist=None).queries(key)


class TestTheBestPhraseIsAsked:
    @pytest.mark.parametrize("key", ["fork", "allows_square", "late_castling", "hangingPawn"])
    def test_the_topic_phrase_is_asked_verbatim(self, key):
        assert terms_for(key)[0] in queries_for(key)

    @pytest.mark.parametrize("key", ["fork", "allows_square", "late_castling"])
    def test_it_is_asked_first(self, key):
        # First, because a search engine's own ranking of the plain phrase is
        # the best signal available and later queries only widen.
        assert queries_for(key)[0] == terms_for(key)[0]

    def test_the_other_phrases_are_still_asked(self):
        # `allows_square` is an outpost to the web and a hole to Staunton;
        # dropping the alternatives would lose half the writing about it.
        got = queries_for("allows_square")

        assert any("hole" in q for q in got)

    def test_no_query_is_ungrammatical_article_plus_phrase(self):
        # "what is a castling in chess" and "what is a undefended pawn chess"
        # were both produced by prefixing an article blindly.
        for key in TERMS:
            for query in queries_for(key):
                assert not query.startswith("what is a "), f"{key}: {query!r}"

    def test_every_claim_gets_at_least_two_queries(self):
        for key in TERMS:
            assert len(queries_for(key)) >= 2, key

    def test_queries_are_unique(self):
        for key in TERMS:
            got = queries_for(key)
            assert len(got) == len(set(got)), key
