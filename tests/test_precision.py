"""Turning a person's marks into a precision figure that does not overclaim.

Design: docs/notes/experiments.e55-detector-precision.md

The property this exists to hold: **five samples can condemn a detector and
cannot exonerate one.** A screen that reported 5/5 as "confirmed" would clear a
detector on an interval spanning 57-100 %, which is how a measurement becomes a
testimonial.
"""

from __future__ import annotations

from chesscoach.precision import (
    MEASURE_SAMPLE,
    Dated,
    PRECISION_FLOOR,
    SCREEN_SAMPLE,
    Marks,
    Verdict,
    condemned,
    confirmed,
    module_for,
    sample_size,
    unsettled,
)


class TestTheAsymmetryTheScreenRestsOn:
    def test_five_wrong_condemns(self):
        # The author's own case: moved_into_attack at 0/5, "broken".
        marks = Marks("moved_into_attack", right=0, wrong=5)

        assert marks.verdict is Verdict.CONDEMNED
        assert marks.interval[1] < PRECISION_FLOOR

    def test_five_right_does_not_confirm(self):
        # 5/5 spans roughly 57-100 %, which settles nothing.
        marks = Marks("hangingPawn", right=5, wrong=0)

        assert marks.verdict is Verdict.INSUFFICIENT
        assert marks.interval[0] < PRECISION_FLOOR

    def test_the_authors_accepted_case_is_still_not_confirmed_at_five(self):
        # 4/5 was accepted by eye -- "works, leave alone" -- and the interval
        # does not support it yet. The screen says so rather than agreeing.
        marks = Marks("allowed_motif.hangingPawn", right=4, wrong=1)

        assert marks.verdict is Verdict.INSUFFICIENT

    def test_twenty_clean_marks_confirm(self):
        marks = Marks("hangingPiece", right=20, wrong=0)

        assert marks.verdict is Verdict.CONFIRMED
        assert marks.interval[0] >= PRECISION_FLOOR

    def test_the_screen_size_is_smaller_than_the_measuring_size(self):
        assert SCREEN_SAMPLE < MEASURE_SAMPLE


class TestUnsureIsNotAVerdict:
    def test_cannot_tell_is_left_out_of_the_denominator(self):
        # Counting it wrong punishes a detector for a hard position; counting it
        # right flatters it.
        marks = Marks("skewer", right=3, wrong=1, unsure=6)

        assert marks.judged == 4
        assert marks.precision == 0.75

    def test_a_detector_only_marked_unsure_carries_no_verdict(self):
        marks = Marks("trappedPiece", right=0, wrong=0, unsure=5)

        assert marks.verdict is Verdict.UNMARKED
        assert marks.precision is None
        assert marks.interval is None


class TestAnUnmarkedDetectorIsNotAPass:
    def test_no_marks_reads_as_unmarked(self):
        # The commonest way a screen quietly lies: an empty box scoring as fine.
        marks = Marks("fork")

        assert marks.verdict is Verdict.UNMARKED
        assert "nobody has marked" in marks.reason

    def test_an_unmarked_detector_is_in_no_bucket(self):
        marks = [Marks("fork")]

        assert condemned(marks) == ()
        assert confirmed(marks) == ()
        assert unsettled(marks) == ()


class TestWhatToDoNext:
    def test_it_says_how_many_more_marks_would_settle_it(self):
        assert sample_size(5) == MEASURE_SAMPLE - 5
        assert "more marks" in Marks("x", right=5, wrong=0).reason

    def test_a_fully_sampled_but_undecided_detector_says_so(self):
        # 15/20 leaves the floor inside the interval, and more of the same
        # sample will not move it -- the reason must not promise otherwise.
        marks = Marks("x", right=15, wrong=5)

        assert marks.verdict is Verdict.INSUFFICIENT
        assert "even at" in marks.reason

    def test_a_condemned_detector_is_told_to_be_fixed_or_retired(self):
        assert "fix or retire" in Marks("x", right=0, wrong=5).reason


class TestBuckets:
    def marks(self):
        return [
            Marks("broken", right=0, wrong=5),
            Marks("good", right=20, wrong=0),
            Marks("open", right=4, wrong=1),
            Marks("never", right=0, wrong=0),
        ]

    def test_each_marked_detector_lands_in_exactly_one_bucket(self):
        marks = self.marks()
        buckets = condemned(marks) + confirmed(marks) + unsettled(marks)

        assert sorted(m.detector for m in buckets) == ["broken", "good", "open"]


class TestAMarkIsEvidenceAboutTheCodeItJudged:
    """A detector rebuilt after marking has no measured precision.

    Not pedantry: reporting a stale 0/5 as current would send the author to fix
    a detector twice, and reporting a stale 5/5 would credit a rebuild with a
    score it never earned.
    """

    def test_a_mark_older_than_the_code_carries_no_verdict(self):
        marks = Dated("moved_into_attack.own_move.own", right=0, wrong=5,
                      marked_on="2026-08-23", changed_on="2026-08-27")

        assert marks.stale is True
        assert marks.verdict is Verdict.UNMARKED
        assert "must be re-marked" in marks.reason

    def test_a_mark_newer_than_the_code_still_counts(self):
        marks = Dated("moved_into_attack.own_move.own", right=0, wrong=5,
                      marked_on="2026-08-28", changed_on="2026-08-27")

        assert marks.stale is False
        assert marks.verdict is Verdict.CONDEMNED

    def test_a_mark_made_the_same_day_is_kept(self):
        # The commit and the marking cannot be ordered within a day, and
        # discarding on a tie would throw away good marks for nothing.
        marks = Dated("x", right=0, wrong=5,
                      marked_on="2026-08-27", changed_on="2026-08-27")

        assert marks.stale is False

    def test_an_unknown_date_never_invalidates_a_mark(self):
        # git being unavailable must not silently delete evidence (L-046).
        assert Dated("x", right=5, wrong=0, marked_on="2026-08-28").stale is False
        assert Dated("x", right=5, wrong=0, changed_on="2026-08-28").stale is False

    def test_each_claim_maps_to_the_module_that_implements_it(self):
        assert module_for("allowed_motif.fork.own") == "chesscoach/tactics.py"
        assert module_for("moved_into_attack.own_move.own") == "chesscoach/material.py"
        assert module_for("concedes_weakness.doubled.own") == "chesscoach/structure.py"

    def test_a_section_claim_falls_back_to_the_sections_package(self):
        assert module_for("early_error.white.own") == "chesscoach/sections/"
        assert module_for("something_new.any.own") == "chesscoach/sections/"


class TestReadingAMarkedSheet:
    """Every claim's marks are credited to that claim, whatever its name holds.

    `score.read` recognised a section by `[a-z][\w.]*` -- no spaces, hyphens or
    apostrophes. The per-opening claims have all three: `out_of_book.Hungarian
    Opening.own`, `out_of_book.Caro-Kann Defense.own`, `out_of_book.Queen's Pawn
    Game.own`. Their headings were never recognised, so their marks were added
    to **whichever claim came before them on the sheet**.

    It moved a recorded verdict. On the 2026-09-07 sheet `out_of_book.Queen's
    Pawn Game` sat directly under `missed_motif.fork`, and the scorer reported
    fork at 2 of 8, 25 % -- its own 1 of 5 plus the opening claim's 1 of 3. The
    true figure was 20 %. Condemned either way, and still a wrong number in the
    record; and no per-opening claim had ever been scored at all.
    """

    SHEET = """WHAT THE SYSTEM DETECTS

missed_motif.fork.own
    claims: You miss forks.
    5 instances across 2 players
------------------------------------------------------------------------------
  [y] alice   move 10  White Nc7   lost 20.0 wp
  [n] alice   move 12  White Rd1   lost 10.0 wp

out_of_book.Queen's Pawn Game.own
    claims: You leave theory early in the Queen's Pawn Game.
    3 instances across 1 players
------------------------------------------------------------------------------
  [n] bob     move  2  White e3    lost  1.7 wp
  [?] bob     move  5  White Nf3   lost  1.6 wp

out_of_book.Caro-Kann Defense.own
    claims: You leave theory early in the Caro-Kann Defense.
    2 instances across 1 players
------------------------------------------------------------------------------
  [y] carol   move  3  Black e6    lost  6.0 wp
"""

    def read(self, tmp_path):
        import importlib.util
        from pathlib import Path

        script = Path(__file__).resolve().parents[1] / "experiments/e55-detector-precision/score.py"
        spec = importlib.util.spec_from_file_location("e55_score", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sheet = tmp_path / "sheet.txt"
        sheet.write_text(self.SHEET, encoding="utf-8")
        marks, fired = module.read(sheet)
        return {m.detector: (m.right, m.wrong, m.unsure) for m in marks}, fired

    def test_a_claim_with_spaces_and_an_apostrophe_keeps_its_own_marks(self, tmp_path):
        marks, _ = self.read(tmp_path)

        assert marks["out_of_book.Queen's Pawn Game.own"] == (0, 1, 1)

    def test_the_claim_above_it_is_not_credited_with_them(self, tmp_path):
        marks, _ = self.read(tmp_path)

        assert marks["missed_motif.fork.own"] == (1, 1, 0)

    def test_a_hyphenated_claim_is_recognised(self, tmp_path):
        marks, fired = self.read(tmp_path)

        assert marks["out_of_book.Caro-Kann Defense.own"] == (1, 0, 0)
        assert fired["out_of_book.Caro-Kann Defense.own"] == 2
