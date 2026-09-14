"""Which mark a position carries when earlier sheets disagree about it.

Screen: docs/notes/experiments.e55-detector-precision.md

The author's rules, after seeing `long_think_error` at zU1S5uVh#47 carried as
`[?]` because a later sheet marked it unsure where an earlier one said `[y]`:

    "[y], then [?] for cases like this keep y, only in case n the mark should
     not be transferred or it could but with leaving the annotation to double
     check"

Two rules, then. **An unsure mark never overrides a definite one.** And **a
rejection that another sheet disagreed with is carried with a note to re-check
it.** A rejection every sheet agreed on is carried as it is -- the author
narrowed the rule explicitly: *"not all n should be double checked, only n where
there was y or ? on some other sheet."*
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "experiments/e55-detector-precision/carry_marks.py"


def resolve(history):
    spec = importlib.util.spec_from_file_location("e55_carry", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.resolve(history)


class TestAnUnsureMarkDoesNotOverrideADefiniteOne:
    def test_yes_then_unsure_keeps_yes(self):
        mark, check = resolve([("a.txt", "y"), ("b.txt", "?")])

        assert mark == "y"
        assert check is None

    def test_unsure_then_yes_keeps_yes(self):
        assert resolve([("a.txt", "?"), ("b.txt", "y")]) == ("y", None)

    def test_only_unsure_stays_unsure(self):
        assert resolve([("a.txt", "?"), ("b.txt", "?")]) == ("?", None)

    def test_the_latest_definite_mark_wins_when_they_agree(self):
        assert resolve([("a.txt", "y"), ("b.txt", "y")]) == ("y", None)


class TestADisputedRejectionIsCarriedWithANoteToRecheck:
    def test_a_lone_rejection_is_carried_without_a_note(self):
        assert resolve([("a.txt", "n")]) == ("n", None)

    def test_a_rejection_every_sheet_agreed_on_is_carried_without_a_note(self):
        assert resolve([("a.txt", "n"), ("b.txt", "n")]) == ("n", None)

    def test_yes_and_no_on_different_sheets_is_flagged_and_names_both(self):
        mark, check = resolve([("a.txt", "y"), ("b.txt", "n")])

        assert mark == "n"
        assert "a.txt" in check and "b.txt" in check

    def test_a_later_yes_over_an_earlier_no_is_still_flagged(self):
        """The disagreement is the reason to look, whichever way it went."""
        mark, check = resolve([("a.txt", "n"), ("b.txt", "y")])

        assert mark == "y"
        assert check is not None

    def test_unsure_does_not_hide_a_rejection(self):
        mark, check = resolve([("a.txt", "n"), ("b.txt", "?")])

        assert mark == "n"
        assert check is not None
