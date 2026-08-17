"""The progress check must say when its own constant was fitted elsewhere.

`INACCURACY_WP` dropped from 10.0 to 5.0 on 2026-08-16
([[experiments.e33-error-threshold]]). `NO_CHANGE_RATIO = 0.58` was fitted at
10.0, from 57 predictions across 84 players, cross-validated at 2 and 5 folds
([[experiments.e05-natural-drift]]). Refitting needs that corpus, which is not
committed, so the constant is **outstanding**.

An out-of-date calibration is not a reason to withhold the progress check — it
still measures whether a rate fell — but it is a reason to stop claiming the
"15-23 % of players meet this anyway" figure, because that number was measured
against a different definition of "an error".

The whole point of the progress check is that it can be **proven wrong**. A
verdict quoting a false-positive rate from a different measurement regime cannot
be, which would make it the one thing this project must not ship.
"""

from __future__ import annotations

from datetime import date

from chesscoach.analysis.labels import (
    INACCURACY_WP,
    NO_CHANGE_RATIO_FITTED_AT_WP,
    calibration_is_stale,
)
from chesscoach.planner import UNTREATED_MET_SHARE_RANGE, _progress_sign
from chesscoach.profile.models import ConfidenceTier
from tests.test_costly_priorities import finding


class TestTheFlagItself:
    def test_it_knows_the_calibration_is_out_of_date(self):
        # Fails the day someone refits E05 and forgets to update the marker,
        # which is the direction of failure that matters.
        assert calibration_is_stale() is (INACCURACY_WP != NO_CHANGE_RATIO_FITTED_AT_WP)

    def test_it_is_currently_stale_and_that_is_recorded_not_hidden(self):
        assert INACCURACY_WP == 5.0
        assert NO_CHANGE_RATIO_FITTED_AT_WP == 10.0
        assert calibration_is_stale() is True


class TestThePlanStopsQuotingTheUntreatedShare:
    """The untreated-share range only appears when a no-change expectation does,
    and that needs a peer reference — so these exercise `_progress_sign` directly
    rather than building a plan without one and testing the wrong branch."""

    def _sign(self, expected: float | None = 0.252) -> str:
        priority = finding(
            "missed_motif", "fork", ConfidenceTier.FOCUS, cost=4.2, peer_cost=3.9,
            rate=0.32, peer_rate=0.17,
        )
        return _progress_sign(priority, target=0.146, games=20, expected=expected)

    def test_the_untreated_share_is_not_quoted_while_stale(self):
        # "15-23 % of players reach this target without changing anything" was
        # measured at a 10 wp floor. Quoting it against 5 wp rates is a claim
        # about a measurement that was never made.
        assert calibration_is_stale()
        assert f"{UNTREATED_MET_SHARE_RANGE[0]:.0%}" not in self._sign()

    def test_it_says_why_rather_than_going_quiet(self):
        # Dropping the caveat silently would read as more confidence, not less.
        assert "not been recalibrated" in self._sign()

    def test_the_target_itself_is_unchanged(self):
        # Only the false-positive claim is withdrawn. The prediction is still a
        # number the system can be held to, and the no-change estimate — which
        # is computed per player, not calibrated — still appears.
        sign = self._sign()

        assert "below 14.6%" in sign
        assert "if nothing changes" in sign

    def test_without_a_no_change_estimate_nothing_changes(self):
        assert "not been recalibrated" not in self._sign(expected=None)
