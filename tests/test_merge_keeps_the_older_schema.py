"""Merging cannot upgrade what it merges.

Spec: docs/notes/design.claims-that-do-not-separate.md

`PeerReference.load` carries the schema version a file was written under, so a
consumer can tell an older reference's numbers from a current one's.

`merged_with` rebuilt the reference without carrying that version, so merging an
older file into a current one produced something *labelled* current while
holding older cells. Found while building the D2 guard; kept after D2 was
reverted, because it is wrong independently of what any version means.

A merge is only as current as its oldest input.
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


def a_reference(band: str, speed: str):
    return build_reference(
        [
            (
                name,
                (
                    ConditionMeasurement("allowed_motif.fork.own", 30, 100, 20, 40),
                    ConditionMeasurement("missed_motif.hangingPiece.own", 30, 100, 20, 40),
                ),
            )
            for name in ("peer1", "peer2", "peer3")
        ],
        band=band,
        time_control=speed,
        depth=15,
    )


@pytest.fixture
def stale(tmp_path):
    """A reference written under v1 -- the oldest version still readable.

    It has to be genuinely older than SCHEMA_VERSION or the test asserts that a
    current file is current, which passes for the wrong reason.
    """
    path = tmp_path / "old.json"
    a_reference("1400-1800", "blitz").save(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["schema_version"] = OLDEST_READABLE
    path.write_text(json.dumps(payload), encoding="utf-8")
    return PeerReference.load(path)


class TestMergingSchemas:
    def test_a_merge_is_as_current_as_its_oldest_input(self, stale):
        current = a_reference("1600-2000", "blitz")

        assert current.merged_with(stale).schema_version == OLDEST_READABLE
        assert stale.merged_with(current).schema_version == OLDEST_READABLE
        assert OLDEST_READABLE < SCHEMA_VERSION, "the fixture must be genuinely older"

    def test_merging_two_current_references_stays_current(self):
        merged = a_reference("1400-1800", "blitz").merged_with(a_reference("1600-2000", "blitz"))

        assert merged.schema_version == SCHEMA_VERSION

    def test_both_halves_still_price_normally(self, stale):
        # The version is a label on provenance, not a mute: v1 and v2 rates mean
        # the same thing. It exists so a future definition change has something
        # to key on rather than discovering the mix afterwards.
        merged = a_reference("1600-2000", "blitz").merged_with(stale)

        assert merged.lookup("1600-2000", "blitz", "missed_motif.hangingPiece") is not None
        assert merged.lookup("1400-1800", "blitz", "missed_motif.hangingPiece") is not None
