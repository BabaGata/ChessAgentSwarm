"""What gates what, and the answer that is neither yes nor no.

Source: docs/notes/domain.chess-concepts.md § C

`chesscoach/arbiter.py` refused to rank on prerequisites and said why:
*"inventing one would be fabricated pedagogy"*. The structure existed — as prose
in the domain note — and nothing could read it. This is that structure as data,
and the property that matters most is that **it returns three answers**.

A function answering only yes or no would let the arbiter order tactics before
process, or process before tactics, while looking careful. The note calls K9 and
K10 *"cross-cutting, teachable at any level"*: they gate nothing and nothing
gates them, so the honest answer about them is that no order was ever stated.
"""

from __future__ import annotations

import pytest

from chesscoach.domains import (
    CLAIM_DOMAINS,
    DOMAINS,
    PREREQUISITES,
    UNMAPPED_ON_PURPOSE,
    claim_gates,
    domain_of,
    gates,
)


class TestTheDomains:
    def test_all_ten_are_present(self):
        assert len(DOMAINS) == 10
        assert {d.key for d in DOMAINS} == {f"K{n}" for n in range(1, 11)}

    def test_every_prerequisite_names_real_domains(self):
        known = {d.key for d in DOMAINS}
        for gate, gated in PREREQUISITES:
            assert gate in known and gated in known, (gate, gated)

    def test_nothing_gates_itself(self):
        for gate, gated in PREREQUISITES:
            assert gate != gated


class TestGating:
    def test_the_note_s_load_bearing_claim(self):
        # "Calculation depends on the tactical pattern vocabulary. You cannot
        # generate good candidate moves for patterns you do not know."
        assert gates("K2", "K3") is True

    def test_gating_is_transitive(self):
        # K1 gates K2 gates K3, so fundamentals gate calculation.
        assert gates("K1", "K3") is True

    def test_the_reverse_of_a_gate_is_a_no(self):
        assert gates("K3", "K2") is False

    def test_two_unordered_domains_are_unknown_not_no(self):
        # K9 is cross-cutting: the note orders it against nothing. Answering
        # "no" would say the note settled something it explicitly did not.
        assert gates("K2", "K9") is None
        assert gates("K9", "K2") is None

    def test_an_unrecognised_domain_is_unknown(self):
        assert gates("K2", "K99") is None

    def test_the_order_has_no_cycles(self):
        # A cycle would make "is A before B" unanswerable and would mean the
        # note's partial order had been transcribed wrongly.
        for gate, gated in PREREQUISITES:
            assert gates(gated, gate) is not True, (gate, gated)


class TestClaimsToDomains:
    def test_a_motif_claim_is_tactics(self):
        assert domain_of("allowed_motif") == "K2"
        assert domain_of("missed_motif") == "K2"

    def test_a_clock_claim_is_practical_process(self):
        assert domain_of("long_think_error") == "K9"
        assert domain_of("time_pressure_error") == "K9"

    def test_an_endgame_claim_is_endgames(self):
        assert domain_of("endgame_error") == "K7"

    def test_an_arguable_claim_is_unmapped(self):
        # `late_castling` is an opening principle or a practical habit depending
        # on why the player delayed, and the detector cannot tell which.
        assert domain_of("late_castling") is None

    def test_every_deliberate_gap_says_why(self):
        for kind, reason in UNMAPPED_ON_PURPOSE.items():
            assert kind not in CLAIM_DOMAINS
            assert len(reason) > 20, kind

    def test_an_unknown_claim_is_none_rather_than_a_guess(self):
        assert domain_of("something_invented") is None


class TestTheQuestionTheArbiterWouldAsk:
    def test_tactics_gates_calculation_at_the_claim_level(self):
        assert claim_gates("missed_motif", "long_think_error") is None

    def test_a_claim_pair_in_the_order_answers_yes(self):
        # Motifs (K2) gate calculation (K3); no shipped claim is K3 yet, so the
        # nearest real pair is motifs gating attack and defence through it.
        assert claim_gates("missed_motif", "allows_pressure") is True

    def test_an_unmapped_claim_makes_the_pair_unknown(self):
        assert claim_gates("late_castling", "missed_motif") is None

    @pytest.mark.parametrize("first,second", [
        ("long_think_error", "time_pressure_error"),   # both K9
        ("allowed_motif", "missed_motif"),             # both K2
    ])
    def test_two_claims_in_one_domain_are_unordered(self, first, second):
        assert claim_gates(first, second) is None

    def test_unknown_is_the_common_answer(self):
        """The design note's own definition of done for this stage.

        If most pairs came back yes or no, the structure would be claiming far
        more than the source supports.
        """
        kinds = sorted(set(CLAIM_DOMAINS) | set(UNMAPPED_ON_PURPOSE))
        answers = [claim_gates(a, b) for a in kinds for b in kinds if a != b]
        unknown = sum(1 for x in answers if x is None)

        assert unknown / len(answers) > 0.5
