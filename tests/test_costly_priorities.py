"""Filling the plan with what a pattern COSTS when nothing is unusual enough.

Found by the first expert review. For player `bernes` the reviewer named
"undefended pieces" as the main weakness; the report named missed forks, which
they ranked third. The numbers explain it exactly:

    conceded hanging piece   10.7% of errors, 10 of 53 games, 7.3 wp/game
                             1.29x the population -> interval fails -> `watch`
    missed fork              32.3% of chances,  9 of 53 games, 4.2 wp/game
                             1.89x the population -> `focus` -> reported

The gate was not wrong. On 112 trials 10.7% against 8.3% is not a significant
difference, and calling the player *unusual* there would be a claim the data does
not support. What was wrong was that being unusual is the only way into the
report, so the most expensive pattern in the player's games -- the one a human
reviewer led with -- was measured and discarded.

So the peer-relative priorities keep the first slots, and remaining slots are
filled by **cost**, labelled as shared rather than personal. E17 measured why the
whole ranking must not become cost: raw cost named one claim to 70% of players.
Here cost only fills what unusualness left empty.
"""

from __future__ import annotations

from chesscoach.arbiter import MAX_PRIORITIES, select_priorities
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

PROV = Provenance(
    engine="Stockfish 18", depth=15, corpus_id="c1", analysed_at="2026-08-15"
)


def finding(
    kind: str,
    subject: str,
    tier: ConfidenceTier,
    *,
    cost: float | None = None,
    peer_cost: float | None = None,
    rate: float = 0.2,
    peer_rate: float | None = 0.1,
    games: int = 10,
) -> Finding:
    return Finding(
        section="S1",
        claim=Claim.of(kind=kind, subject=subject),
        measurement=Measurement(
            instances=12,
            distinct_games=games,
            games_with_data=53,
            rate=rate,
            baseline_rate=0.05,
            peer_rate=peer_rate,
            ci95=(0.06, 0.18),
            cost_wp=None if cost is None else cost * 53,
            peer_cost_per_game=peer_cost,
        ),
        provenance=PROV,
        confidence=Confidence(tier=tier, replicated=True, reasons=()),
        gap_type=GapType(
            hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED
        ),
        # A finding without a cited position is refused by the model itself, so a
        # cost-ranked filler is falsifiable on the same terms as any other
        # (CLAUDE.md hard rule 6).
        evidence=(
            Evidence(
                game_id="g1",
                ply=20,
                fen="8/8/8/8/8/8/8/K6k w - - 0 1",
                move_played="a1a2",
                better_move="a1b1",
                loss_wp=12.0,
                note=f"{subject} here",
            ),
        ),
    )


class TestCostFillsEmptySlots:
    def test_an_assertable_finding_still_comes_first(self):
        # The peer-relative diagnosis is what makes this a diagnosis rather than
        # a description (R-14). Cost never displaces it, however large.
        unusual = finding("missed_motif", "fork", ConfidenceTier.FOCUS, cost=4.2, peer_cost=3.9)
        expensive = finding(
            "allowed_motif", "hangingPiece", ConfidenceTier.WATCH, cost=7.3, peer_cost=8.7
        )

        selection = select_priorities((unusual,), also=(expensive,))

        assert selection.priorities[0].finding is unusual
        assert selection.priorities[0].shared is False

    def test_the_costly_pattern_fills_the_next_slot(self):
        unusual = finding("missed_motif", "fork", ConfidenceTier.FOCUS, cost=4.2, peer_cost=3.9)
        expensive = finding(
            "allowed_motif", "hangingPiece", ConfidenceTier.WATCH, cost=7.3, peer_cost=8.7
        )

        selection = select_priorities((unusual,), also=(expensive,))

        assert len(selection.priorities) == 2
        assert selection.priorities[1].finding is expensive
        assert selection.priorities[1].shared is True

    def test_costly_fillers_are_ranked_by_what_they_cost_the_player(self):
        # Not by excess over peers. The whole point is that these are patterns
        # the peer comparison already declined to rank.
        cheap = finding("allowed_motif", "skewer", ConfidenceTier.WATCH, cost=0.4, peer_cost=2.4)
        dear = finding(
            "allowed_motif", "hangingPiece", ConfidenceTier.WATCH, cost=7.3, peer_cost=8.7
        )
        middling = finding("allowed_motif", "pin", ConfidenceTier.WATCH, cost=4.5, peer_cost=8.1)

        selection = select_priorities((), also=(cheap, dear, middling), limit=3)

        assert [p.finding.claim.subject for p in selection.priorities] == [
            "hangingPiece", "pin", "skewer"
        ]

    def test_a_pattern_that_costs_nothing_measurable_is_not_offered(self):
        # Conceding a structure is a choice, not a mistake, and has no cost to
        # state. Filling a training slot with one would be inventing a priority.
        unpriced = finding("concedes_weakness", "isolated", ConfidenceTier.WATCH, cost=None)

        assert select_priorities((), also=(unpriced,)).priorities == ()

    def test_a_negligible_cost_is_not_worth_a_slot(self):
        trivial = finding("allowed_motif", "skewer", ConfidenceTier.WATCH, cost=0.05)

        assert select_priorities((), also=(trivial,)).priorities == ()

    def test_a_pattern_the_player_does_less_than_peers_is_never_offered(self):
        # Caught by running all 12 review players. Sheriwoyama was handed "your
        # play falls off when the clock is short" at **13% against 15% for
        # players at your level** — they are better than average at it — under a
        # heading saying it stands out, with a training step attached.
        #
        # Cost alone cannot filter this: that claim costs 8.6 a game and peers
        # only 7.1, because the condition arises more often for this player, so
        # the *excess* is positive while the *rate* is below the population. A
        # thing you do less than your peers is not a thing to work on, whatever
        # it totals to.
        better_than_peers = finding(
            "time_pressure_error", "clock", ConfidenceTier.WATCH,
            cost=8.6, peer_cost=7.1, rate=0.13, peer_rate=0.15,
        )

        assert select_priorities((), also=(better_than_peers,)).priorities == ()

    def test_a_pattern_with_no_peer_rate_is_still_offered(self):
        # No reference for this claim is not evidence of being better than
        # average, and dropping it would silently narrow the pool to whatever
        # the population happens to cover.
        unmeasured = finding(
            "allowed_motif", "hangingPiece", ConfidenceTier.WATCH,
            cost=7.3, peer_cost=None, rate=0.107, peer_rate=None,
        )

        assert len(select_priorities((), also=(unmeasured,)).priorities) == 1

    def test_the_same_subject_is_never_offered_twice(self):
        # Missing pins and conceding them are one thing to work on. That rule
        # already held within the assertable pool; it has to hold across both.
        unusual = finding("missed_motif", "pin", ConfidenceTier.FOCUS, cost=4.2, peer_cost=3.9)
        same = finding("allowed_motif", "pin", ConfidenceTier.WATCH, cost=9.9, peer_cost=8.1)
        other = finding(
            "allowed_motif", "hangingPiece", ConfidenceTier.WATCH, cost=7.3, peer_cost=8.7
        )

        selection = select_priorities((unusual,), also=(same, other), limit=3)

        subjects = [p.finding.claim.subject for p in selection.priorities]
        assert subjects == ["pin", "hangingPiece"]

    def test_it_never_exceeds_the_limit(self):
        pool = tuple(
            finding("allowed_motif", f"m{i}", ConfidenceTier.WATCH, cost=9.0 - i)
            for i in range(6)
        )

        assert len(select_priorities((), also=pool, limit=3).priorities) == 3

    def test_without_a_second_pool_nothing_changes(self):
        # Every existing caller passes no `also`, and must behave exactly as before.
        unusual = finding("missed_motif", "fork", ConfidenceTier.FOCUS, cost=4.2, peer_cost=3.9)

        selection = select_priorities((unusual,))

        assert len(selection.priorities) == 1
        assert selection.priorities[0].shared is False


class TestTheCapItself:
    def test_three_is_the_cap(self):
        assert MAX_PRIORITIES == 3

    def test_a_shared_priority_says_so_in_its_reasons(self):
        # The reader must be able to tell a "you are unusual" claim from a "this
        # is expensive and ordinary" one. E25 condition 2.
        expensive = finding(
            "allowed_motif", "hangingPiece", ConfidenceTier.WATCH, cost=7.3, peer_cost=8.7
        )

        reasons = select_priorities((), also=(expensive,)).priorities[0].reasons

        assert any("level" in reason for reason in reasons)
