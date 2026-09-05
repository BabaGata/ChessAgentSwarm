"""A reference built before the worth-playing rule cannot price `allowed_motif`.

Spec: docs/notes/design.punishment-validity.md

v2 counted an `allowed_motif` instance only when the opponent's **single best**
reply executed the motif. v3 counts any reply that executes it and was worth
playing, which finds about 20 % more. The rates mean different things, so
comparing a v3 player against a v2 population compares two definitions -- L-046,
the arms of a comparison not being what the comparison claims.

The rest of a v2 file is unaffected, so it is not discarded: only the claims
whose definition moved are refused.
"""

from __future__ import annotations

import json

import pytest

from chesscoach.peers import (
    READABLE_SCHEMA_VERSIONS,
    SCHEMA_VERSION,
    ConditionMeasurement,
    PeerReference,
    build_reference,
)

OLDEST_READABLE = min(READABLE_SCHEMA_VERSIONS)


@pytest.fixture
def written(tmp_path):
    def write(version: int) -> PeerReference:
        reference = build_reference(
            [
                (
                    name,
                    (
                        ConditionMeasurement("allowed_motif.fork.own", 30, 100, 20, 40),
                        ConditionMeasurement("missed_motif.hangingPawn.own", 30, 100, 20, 40),
                    ),
                )
                for name in ("peer1", "peer2", "peer3")
            ],
            band="1400-1800",
            time_control="blitz",
            depth=15,
        )
        path = tmp_path / f"peers-v{version}.json"
        reference.save(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["schema_version"] = version
        path.write_text(json.dumps(payload), encoding="utf-8")
        return PeerReference.load(path)

    return write


class TestAnOlderReference:
    def test_refuses_the_claims_whose_definition_moved(self, written):
        assert written(2).lookup("1400-1800", "blitz", "allowed_motif.fork") is None

    def test_still_prices_everything_else(self, written):
        stale = written(2)

        assert stale.lookup("1400-1800", "blitz", "missed_motif.hangingPawn") is not None

    def test_a_current_reference_prices_them_normally(self, written):
        current = written(SCHEMA_VERSION)

        assert current.lookup("1400-1800", "blitz", "allowed_motif.fork") is not None

    def test_the_version_is_read_from_the_file_not_assumed(self, written):
        assert written(2).schema_version == 2
        assert written(SCHEMA_VERSION).schema_version == SCHEMA_VERSION

    def test_a_reference_built_in_this_process_is_current(self):
        fresh = build_reference(
            [("p1", (ConditionMeasurement("allowed_motif.fork.own", 3, 10, 2, 4),))],
            band="1400-1800",
            time_control="blitz",
            depth=15,
        )

        assert fresh.schema_version == SCHEMA_VERSION

    def test_a_merge_is_as_current_as_its_oldest_input(self, written):
        # Otherwise merging a stale file into a current one launders it.
        merged = written(SCHEMA_VERSION).merged_with(written(OLDEST_READABLE))

        assert merged.schema_version == OLDEST_READABLE
        assert OLDEST_READABLE < SCHEMA_VERSION, "the fixture must be genuinely older"
