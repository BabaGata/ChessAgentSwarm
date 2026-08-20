"""Two claims that describe the same moves are one thing to work on.

Screen: docs/notes/experiments.e42-claim-overlap.md

The threshold is calibrated, not chosen: `drop_redundant_aggregates` already
declares a pooled parent redundant against its own subdivision, and measured on
real players those pairs sit at 60-69 % coverage. A cross-section rule set at
60 % therefore deletes nothing the codebase would not already delete if the two
claims happened to share a claim kind.
"""

from __future__ import annotations

from chesscoach.overlap import REDUNDANT_COVERAGE, coverage, drop_covered_claims
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

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-08-20")


def a_finding(
    kind: str = "early_error",
    subject: str = "any",
    section: str = "S4",
    moves: tuple[tuple[str, int], ...] = (),
    tier: ConfidenceTier = ConfidenceTier.FOCUS,
) -> Finding:
    return Finding(
        section=section,
        claim=Claim.of(kind=kind, subject=subject),
        measurement=Measurement(
            instances=len(moves) or 5,
            instances_at=moves,
            distinct_games=min(4, len(moves) or 4),
            games_with_data=30,
            rate=0.3,
            peer_rate=0.15,
            baseline_rate=0.15,
        ),
        provenance=PROVENANCE,
        confidence=Confidence(tier=tier, replicated=True),
        gap_type=GapType(
            hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED
        ),
        evidence=(Evidence(game_id="g1", ply=21, fen="8/8/8/8/8/8/8/K6k w - - 0 1"),),
    )


def moves(*plies: int, game: str = "g1") -> tuple[tuple[str, int], ...]:
    return tuple((game, ply) for ply in plies)


class TestCoverage:
    def test_a_claim_wholly_inside_another_is_fully_covered(self):
        wide = a_finding(moves=moves(10, 12, 14, 16))
        narrow = a_finding(moves=moves(10, 12, 14, 16))

        assert coverage(wide, narrow) == 1.0

    def test_coverage_is_the_share_of_the_wide_claim_the_narrow_one_accounts_for(self):
        wide = a_finding(moves=moves(10, 12, 14, 16))
        narrow = a_finding(moves=moves(10, 12))

        assert coverage(wide, narrow) == 0.5

    def test_disjoint_claims_do_not_cover_each_other(self):
        assert coverage(a_finding(moves=moves(1, 2)), a_finding(moves=moves(3, 4))) == 0.0

    def test_a_claim_that_reports_no_moves_covers_nothing(self):
        # Empty means "not recorded", never "no instances" -- so it must not read
        # as fully covered and get deleted.
        assert coverage(a_finding(moves=()), a_finding(moves=moves(1))) == 0.0
        assert coverage(a_finding(moves=moves(1)), a_finding(moves=())) == 0.0

    def test_the_threshold_is_the_calibrated_one(self):
        # Stated as a test because it came from measurement (E42b): the weakest
        # tenth of the pairs the project already calls redundant sat at 60 %.
        assert REDUNDANT_COVERAGE == 0.60


class TestDropping:
    def test_a_wide_claim_mostly_restating_a_narrow_one_is_dropped(self):
        wide = a_finding(kind="time_pressure_error", section="S2", moves=moves(*range(10, 20)))
        narrow = a_finding(kind="endgame_error", section="S3", moves=moves(*range(10, 18)))

        asserted, watched = drop_covered_claims((wide, narrow), ())

        assert [f.claim.kind for f in asserted] == ["endgame_error"]
        assert watched == ()

    def test_partial_overlap_keeps_both(self):
        wide = a_finding(kind="time_pressure_error", section="S2", moves=moves(*range(10, 20)))
        narrow = a_finding(kind="endgame_error", section="S3", moves=moves(10, 11, 12))

        asserted, _ = drop_covered_claims((wide, narrow), ())

        assert len(asserted) == 2

    def test_the_narrow_claim_is_the_one_kept(self):
        # Same reasoning as drop_redundant_aggregates: the specific claim names
        # the same problem and says where to look.
        wide = a_finding(kind="early_error", section="S4", moves=moves(*range(1, 11)))
        narrow = a_finding(kind="missed_motif", subject="fork", section="S1",
                           moves=moves(*range(1, 8)))

        asserted, _ = drop_covered_claims((wide, narrow), ())

        assert [f.claim.kind for f in asserted] == ["missed_motif"]

    def test_a_wide_claim_is_kept_when_the_narrow_one_cannot_be_asserted(self):
        # Across pools this matters: deleting a claim the player can be told
        # about, in favour of one they cannot, leaves them with nothing.
        wide = a_finding(kind="time_pressure_error", section="S2",
                         moves=moves(*range(10, 20)), tier=ConfidenceTier.FOCUS)
        narrow = a_finding(kind="endgame_error", section="S3",
                           moves=moves(*range(10, 18)), tier=ConfidenceTier.WATCH)

        asserted, watched = drop_covered_claims((wide,), (narrow,))

        assert [f.claim.kind for f in asserted] == ["time_pressure_error"]
        assert [f.claim.kind for f in watched] == ["endgame_error"]

    def test_suppression_reaches_across_the_two_pools(self):
        # The existing within-section rule runs on each pool separately, so a
        # parent in one and its subdivision in the other both survive. Measured
        # on real players, 2 of 2 such pairs escaped it that way (E42b).
        wide = a_finding(kind="allows_square", subject="any", section="S6",
                         moves=moves(*range(10, 20)), tier=ConfidenceTier.WATCH)
        narrow = a_finding(kind="allows_square", subject="outpost", section="S6",
                           moves=moves(*range(10, 18)), tier=ConfidenceTier.WATCH)

        asserted, watched = drop_covered_claims((), (wide, narrow))

        assert asserted == ()
        assert [f.claim.subject for f in watched] == ["outpost"]

    def test_claims_that_do_not_report_moves_are_never_dropped(self):
        wide = a_finding(kind="concedes_weakness", section="S5", moves=())
        narrow = a_finding(kind="missed_motif", section="S1", moves=())

        asserted, _ = drop_covered_claims((wide, narrow), ())

        assert len(asserted) == 2

    def test_equal_sized_claims_are_both_kept(self):
        # Neither is the narrower one, so there is no principled way to say which
        # survives, and a tiebreak on id would delete the more useful claim as
        # often as not. Deliberately conservative: the slot is worth less than
        # the wrong deletion. Exact ties did not occur in E42's 501 pairs.
        one = a_finding(kind="early_error", section="S4", moves=moves(1, 2, 3))
        two = a_finding(kind="endgame_error", section="S3", moves=moves(1, 2, 3))

        asserted, _ = drop_covered_claims((one, two), ())

        assert len(asserted) == 2

    def test_dropping_is_not_chained_into_deleting_everything(self):
        # A covers B covers C must not leave the player with nothing.
        a = a_finding(kind="early_error", section="S4", moves=moves(*range(1, 13)))
        b = a_finding(kind="endgame_error", section="S3", moves=moves(*range(1, 11)))
        c = a_finding(kind="missed_motif", section="S1", moves=moves(*range(1, 9)))

        asserted, _ = drop_covered_claims((a, b, c), ())

        assert len(asserted) >= 1

    def test_nothing_is_dropped_when_there_is_only_one_claim(self):
        only = a_finding(moves=moves(1, 2, 3))

        assert drop_covered_claims((only,), ()) == ((only,), ())
