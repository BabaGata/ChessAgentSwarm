"""A claim that cannot distinguish players must not compare them to peers.

Spec: docs/notes/design.claims-that-do-not-separate.md § D1

[[experiments.e83-spread-rescreen]] found nine asserted claims on which players
are statistically interchangeable, and showed the finding is real rather than
underpowered. The detectors keep running and keep citing evidence; what is
removed is the sentence "more than your peers", and the unearned rank the
baseline fallback would hand it in its place.
"""

from __future__ import annotations

import pytest

from chesscoach import separation
from chesscoach.arbiter import _unusualness
from chesscoach.ingest.corpus import Corpus
from chesscoach.peers import ConditionMeasurement, build_reference
from chesscoach.profile.models import (
    Claim,
    Confidence,
    ConfidenceTier,
    DeterminedBy,
    Evidence,
    Finding,
    GapType,
    GapTypeHypothesis,
    Measurement,
    Provenance,
)
from chesscoach.sections.base import SectionContext

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-07-31")


def a_context(rates: dict[str, float]) -> SectionContext:
    """A context whose reference holds a rate for every claim named."""
    peers = build_reference(
        [
            (
                name,
                tuple(
                    ConditionMeasurement(key, int(rate * 100), 100, 20, 40)
                    for key, rate in rates.items()
                ),
            )
            for name in ("peer1", "peer2", "peer3")
        ],
        band="1400-1800",
        time_control="rapid",
        depth=15,
    )
    return SectionContext(
        observations=(),
        corpus=Corpus(username="alice", corpus_id="c1", game_ids=("g001",)),
        provenance=PROVENANCE,
        band="1400-1800",
        time_control="rapid",
        peers=peers,
    )


def a_finding(kind: str, subject: str, lift: float) -> Finding:
    """A finding whose baseline lift is `lift` -- the arbiter derives it as
    rate / baseline_rate, so the baseline is set from the wanted lift."""
    return Finding(
        section="S1",
        claim=Claim.of(kind=kind, subject=subject),
        measurement=Measurement(
            instances=12,
            distinct_games=6,
            games_with_data=30,
            rate=0.30,
            peer_rate=None,
            baseline_rate=0.30 / lift,
        ),
        provenance=PROVENANCE,
        confidence=Confidence(tier=ConfidenceTier.FOCUS, replicated=True),
        gap_type=GapType(
            hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED
        ),
        evidence=(Evidence(game_id="g001", ply=11, fen="8/8/8/8/8/8/8/K6k w - - 0 1"),),
    )


class TestTheRegister:
    def test_a_claim_players_share_does_not_separate_them(self):
        assert not separation.separates("allowed_motif.backRankMate")

    def test_a_claim_players_differ_on_does(self):
        assert separation.separates("long_think_error.long_think")

    def test_an_unscreened_claim_is_allowed_rather_than_silenced(self):
        # Absence from the register is absence of evidence. Muting on it would
        # silence every claim the screen never reached.
        assert separation.separates("some_claim_e83_never_saw.any")

    # **The example is a stand-in, and it has moved once already.** These tests
    # are about key matching and withholding, not about which claim happens to
    # be flat -- and they named `allowed_motif.fork`, which **left the register**
    # when the fork/skewer relabel and the missed_motif widening landed
    # (2026-09-13). `discoveredAttack` is the stand-in now, chosen because it
    # was flat and conclusive on both the old reference and the rebuilt one.
    #
    # If it moves too, swap it again -- do not weaken the assertion. A test that
    # reads the register to decide what to assert would pass whatever the
    # register said, which is no test at all.
    FLAT = "allowed_motif.discoveredAttack"

    @pytest.mark.parametrize("written", [FLAT, FLAT + ".own"])
    def test_keys_match_with_or_without_the_direction_suffix(self, written):
        # Sections pass "kind.subject"; the reference stores "kind.subject.own".
        # I-10 was exactly this mismatch, and it muted four shipped claims.
        assert not separation.separates(written)

    def test_every_entry_carries_its_evidence(self):
        for key, why in separation.DOES_NOT_SEPARATE.items():
            assert why.source, key
            assert why.dispersion > 0, key
            assert 0.0 <= why.p <= 1.0, key
            assert why.smallest_visible > 1.0, key

    def test_the_inconclusive_ones_are_marked_as_such(self):
        # backRankMate failed at an MDE too wide to call flat, and E83 says so;
        # the register must not flatten that into one verdict.
        assert not separation.DOES_NOT_SEPARATE["allowed_motif.backRankMate.own"].conclusive
        assert separation.DOES_NOT_SEPARATE[self.FLAT + ".own"].conclusive


class TestNoComparisonIsMade:
    # A claim in the register and one that is not, both with the same rate, so
    # only the register can explain the difference. `discoveredAttack` is flat
    # and `hangingPiece` separates; see `TestTheRegister.FLAT` on why the flat
    # one is not `fork` any more.
    def test_peer_rate_is_withheld_even_when_the_reference_has_the_number(self):
        context = a_context(
            {
                "allowed_motif.discoveredAttack.own": 0.30,
                "allowed_motif.hangingPiece.own": 0.30,
            }
        )
        assert context.peer_rate("allowed_motif.hangingPiece") == pytest.approx(0.30)
        assert context.peer_rate("allowed_motif.discoveredAttack") is None

    def test_a_withheld_claim_gets_neutral_unusualness(self):
        # Without this the claim would inherit lift_vs_baseline and outrank
        # claims that earned their place -- L-012, a universal behaviour scoring
        # high against the player's own average.
        assert _unusualness(a_finding("allowed_motif", "discoveredAttack", 3.0)) == 1.0

    def test_a_separating_claim_keeps_its_baseline_lift(self):
        assert _unusualness(a_finding("allowed_motif", "hangingPiece", 3.0)) == 3.0
