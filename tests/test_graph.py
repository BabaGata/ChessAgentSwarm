"""Talking to the graph, and where its address comes from.

Design: docs/notes/design.graph-knowledge-base.md

Two things are pinned here and only one needs a database.

**The address is configuration, never an assumption.** The engine is already a
path argument and Ollama's host is already a parameter; Neo4j joins them, so
whether the database runs in a container on this laptop, natively, or on another
machine is a deployment choice and not a property of the code. That is the whole
answer to "what about the future agent" -- the topology is made not to matter.

**Loading is idempotent.** Neo4j is a derived index rebuilt from files, so
running the loader twice must leave what running it once left. Anything else
would make `docker compose down -v` a scary operation instead of the ordinary
one it should be.

The tests that need a live database skip when there is none, so a checkout with
no container still runs the suite green.
"""

from __future__ import annotations

import pytest

from chesscoach.graph import Settings, settings_from_env

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


class TestSettings:
    def test_it_defaults_to_the_local_container(self):
        got = settings_from_env({})

        assert got.uri == "bolt://localhost:7687"
        assert got.user == "neo4j"

    def test_every_field_can_be_overridden(self):
        got = settings_from_env({
            "NEO4J_URI": "bolt://elsewhere:7687",
            "NEO4J_USER": "someone",
            "NEO4J_PASSWORD": "secret",
            "NEO4J_DATABASE": "other",
        })

        assert got.uri == "bolt://elsewhere:7687"
        assert got.user == "someone"
        assert got.password == "secret"
        assert got.database == "other"

    def test_the_password_is_not_printed(self):
        # A connection failure prints the settings, and a password in a log is
        # a password in a bug report.
        got = Settings(uri="bolt://x", user="u", password="hunter2", database="neo4j")

        assert "hunter2" not in repr(got)
        assert "bolt://x" in repr(got)


def _store():
    """A live store, or a skip. Never a failure: a checkout may have no database."""
    from chesscoach.graph import GraphStore, GraphUnavailable

    try:
        store = GraphStore.connect()
    except GraphUnavailable as error:
        pytest.skip(f"no graph database reachable ({error})")
    return store


@pytest.mark.integration
class TestAgainstALiveGraph:
    def test_the_schema_can_be_applied_twice(self):
        with _store() as store:
            store.ensure_schema()
            store.ensure_schema()

    def test_loading_the_rules_twice_leaves_one_copy(self):
        with _store() as store:
            store.ensure_schema()
            store.load_rules()
            once = store.counts()
            store.load_rules()

            assert store.counts() == once

    def test_the_rules_are_actually_there(self):
        with _store() as store:
            store.ensure_schema()
            store.load_rules()
            counts = store.counts()

            assert counts.get("Rule", 0) >= 12   # 6 pieces + 6 outcomes
            assert counts.get("TimeControl", 0) == 5

    def test_a_question_a_small_model_would_ask_can_be_answered(self):
        # The point of the layer: retrieval, not storage.
        with _store() as store:
            store.ensure_schema()
            store.load_rules()

            answer = store.rule_about("knight")

            assert answer is not None
            assert "b3" in answer["attacks_from_centre"]

    def test_an_unknown_subject_returns_nothing_rather_than_guessing(self):
        with _store() as store:
            store.ensure_schema()

            assert store.rule_about("zugzwang-machine") is None
