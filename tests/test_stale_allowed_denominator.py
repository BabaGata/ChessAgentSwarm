"""A reference built before D2 cannot price `allowed_motif`.

Spec: docs/notes/design.claims-that-do-not-separate.md § D2

D2 changed what `allowed_motif.X`'s denominator counts: the errors where X was
available to punish them, rather than every error the player made. A reference
written before that carries the old rates, so comparing a player's new-style
rate against them compares two differently defined quantities -- which is L-046,
the arms of a comparison not being what the comparison claims.

The reference is otherwise untouched by D2, so the whole file is not discarded:
only the claims whose definition moved are refused.
"""

from __future__ import annotations

import json

import pytest

from chesscoach.peers import SCHEMA_VERSION, ConditionMeasurement, PeerReference, build_reference


@pytest.fixture
def written(tmp_path):
    def write(version: int):
        reference = build_reference(
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


class TestAStaleReference:
    def test_still_loads_and_still_prices_everything_else(self, written):
        stale = written(2)

        assert stale.lookup("1400-1800", "blitz", "missed_motif.hangingPiece") is not None

    def test_refuses_the_claims_whose_denominator_moved(self, written):
        stale = written(2)

        assert stale.lookup("1400-1800", "blitz", "allowed_motif.fork") is None

    def test_a_current_reference_prices_them_normally(self, written):
        current = written(SCHEMA_VERSION)

        assert current.lookup("1400-1800", "blitz", "allowed_motif.fork") is not None

    def test_the_version_is_recorded_rather_than_assumed(self, written):
        assert written(2).schema_version == 2
        assert written(SCHEMA_VERSION).schema_version == SCHEMA_VERSION

    def test_a_reference_built_in_memory_is_current(self):
        # Nothing that was just measured by this code can be stale.
        fresh = build_reference(
            [("p1", (ConditionMeasurement("allowed_motif.fork.own", 3, 10, 2, 4),))],
            band="1400-1800",
            time_control="blitz",
            depth=15,
        )
        assert fresh.schema_version == SCHEMA_VERSION
