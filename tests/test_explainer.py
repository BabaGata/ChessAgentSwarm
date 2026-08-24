"""The report a player actually reads.

Spec: docs/notes/architecture.interaction.md § 7

The constraints tested here are the ones that separate a report from the
coaching anti-pattern: one or two things rather than nine (R-12), every claim
cited (V8), what could not be assessed said out loud, and nothing about talent
or potential.
"""

from __future__ import annotations

import pytest

from chesscoach.explainer import render
from chesscoach.planner import build_plan
from chesscoach.arbiter import MAX_PRIORITIES, select_priorities
from chesscoach.profile.models import (
    Claim,
    Confidence,
    ConfidenceTier,
    CorpusRef,
    DeterminedBy,
    Evidence,
    Finding,
    GapType,
    GapTypeHypothesis,
    Measurement,
    PlayerProfile,
    PlayerRef,
    Provenance,
)

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-08-04")


def a_finding(
    kind: str = "missed_motif",
    subject: str = "pin",
    rate: float = 0.30,
    peer_rate: float | None = 0.12,
    status: str = "asserted",
    gap_type: GapType | None = None,
) -> Finding:
    return Finding(
        section="S1",
        claim=Claim.of(kind=kind, subject=subject),
        measurement=Measurement(
            instances=9, distinct_games=8, games_with_data=24, rate=rate, peer_rate=peer_rate
        ),
        provenance=PROVENANCE,
        confidence=Confidence(tier=ConfidenceTier.PRIORITY, replicated=True),
        gap_type=gap_type
        or GapType(hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED),
        evidence=(
            Evidence(game_id="abc123", ply=40, fen="8/8/8/8/8/8/8/K6k w - - 0 1",
                     move_played="h3", better_move="Bb5"),
        ),
        status=status,
    )


def a_profile(*findings: Finding, with_plan: bool = True) -> PlayerProfile:
    profile = PlayerProfile(
        player=PlayerRef(source="lichess", username="alice", band="1400-1800"),
        corpus=CorpusRef(corpus_id="c1", n_games=24, date_range=("2026-05-01", "2026-07-30")),
        findings=findings,
    )
    if not with_plan:
        return profile
    plan = build_plan(select_priorities(findings).priorities, created="2026-08-04")
    return profile if plan is None else profile.__class__(**{**profile.__dict__, "plan": plan})


class TestShape:
    def test_it_names_the_player_and_the_sample(self):
        report = render(a_profile(a_finding()))

        assert "alice" in report
        assert "24 games" in report

    def test_it_gives_the_dates_the_games_came_from(self):
        assert "2026-05-01 to 2026-07-30" in render(a_profile(a_finding()))


class TestNotTheAntiPattern:
    def test_it_reports_only_what_the_plan_acts_on(self):
        # R-12: a player given nine weaknesses has been given none.
        findings = tuple(
            a_finding(subject=name, rate=0.30 - n * 0.01)
            for n, name in enumerate(["pin", "fork", "skewer", "hangingPiece", "trappedPiece"])
        )

        report = render(a_profile(*findings))

        assert report.count("How often") <= MAX_PRIORITIES

    def test_it_says_how_many_it_set_aside_rather_than_hiding_them(self):
        findings = tuple(
            a_finding(subject=name, rate=0.30 - n * 0.01)
            for n, name in enumerate(["pin", "fork", "skewer", "hangingPiece"])
        )

        assert "1 further pattern was found but not prioritised" in render(a_profile(*findings))

    def test_the_two_numbered_lists_are_in_the_same_order(self):
        # Both sections are numbered, so a reader takes item 1 in one to be item
        # 1 in the other. Profile order is insertion order, not the ranking.
        # Listed fork-first, but pin deviates further and the arbiter ranks it
        # first. Both sections must agree with the arbiter, not with the list.
        findings = (a_finding(subject="fork", rate=0.20), a_finding(subject="pin", rate=0.40))

        report = render(a_profile(*findings))

        assert report.index("miss pin tactics") < report.index("miss fork tactics")
        assert report.index("Drill `pin`") < report.index("Drill `fork`")

    def test_silence_is_explained_when_nothing_reached_confidence(self):
        # An empty report reads as "you are fine", which is not what it means.
        report = render(a_profile(with_plan=False))

        assert "too few of them" in report


class TestEvidence:
    def test_every_reported_finding_cites_a_game(self):
        report = render(a_profile(a_finding()))

        assert "game abc123" in report

    def test_ply_is_shown_as_a_move_number(self):
        # Ply is 1-based, so ply 40 is Black's move 20. This test previously
        # asserted 21, which is the off-by-one the reviewer caught: it encoded
        # the bug rather than the rule, and so could never have failed on it.
        assert "move 20" in render(a_profile(a_finding()))

    def test_it_shows_what_was_played_and_what_was_better(self):
        report = render(a_profile(a_finding()))

        assert "you played h3" in report
        assert "Bb5 was better" in report

    def test_it_does_not_offer_the_move_the_player_already_made(self):
        # Seen in a live session: "you played c8e6 (c8e6 was better)". A claim
        # can cite a position where the player found the best move, because the
        # claim is about the position rather than the move.
        from dataclasses import replace

        finding = a_finding()
        same = replace(finding.evidence[0], move_played="Bb5", better_move="Bb5")
        report = render(a_profile(replace(finding, evidence=(same,))))

        assert "you played Bb5" in report
        assert "was better" not in report

    def test_it_compares_with_peers_rather_than_asserting_badness(self):
        report = render(a_profile(a_finding()))

        assert "for players at your level" in report


class TestGapTypeIsOnlyExplainedWhenProbed:
    def test_an_inferred_gap_type_is_not_explained_away(self):
        # Dressing a guess in an explanation is how a report stops being honest.
        report = render(a_profile(a_finding()))

        assert "unlimited time" not in report

    def test_a_probed_knowledge_gap_says_what_it_means(self):
        probed = GapType(
            hypothesis=GapTypeHypothesis.KNOWLEDGE, determined_by=DeterminedBy.PROBED
        )

        report = render(a_profile(a_finding(gap_type=probed)))

        assert "worth learning" in report

    def test_a_probed_skill_gap_says_something_different(self):
        probed = GapType(hypothesis=GapTypeHypothesis.SKILL, determined_by=DeterminedBy.PROBED)

        report = render(a_profile(a_finding(gap_type=probed)))

        assert "spotting it during a game" in report


class TestHonesty:
    def test_it_states_what_it_does_not_know(self):
        assert "WHAT THIS DOES NOT KNOW" in render(a_profile(a_finding()))

    def test_it_makes_no_claim_about_talent_or_ceiling(self):
        # Not a ban on the words -- the report disclaims exactly these, which is
        # the point. What must never appear is a *prediction* about the player.
        report = render(a_profile(a_finding())).casefold()

        for claim in ("you could reach", "you are capable", "your ceiling is", "with your talent"):
            assert claim not in report

    def test_it_disclaims_them_explicitly(self):
        assert "nothing here estimates your potential" in render(a_profile(a_finding())).casefold()

    def test_it_reports_what_could_not_be_assessed(self):
        # Silence implies competence, so a declined section is named.
        declined = a_finding(subject="fork", status="insufficient_data")

        report = render(a_profile(a_finding(), declined))

        assert "COULD NOT BE ASSESSED" in report

    def test_the_progress_sign_is_stated_as_a_number(self):
        report = render(a_profile(a_finding()))

        assert "WHAT WOULD SHOW IT WORKED" in report
        assert "over your next" in report

    def test_a_plan_without_a_target_says_so_rather_than_faking_one(self):
        # Profiles written before schema v3 carry a sign in prose and no number.
        # "below lower over your next 30 games" is what pretending looks like.
        from dataclasses import replace

        profile = a_profile(a_finding())
        plan = replace(
            profile.plan, steps=tuple(replace(s, target_rate=None) for s in profile.plan.steps)
        )
        report = render(replace(profile, plan=plan))

        assert "no checkable target" in report
        assert "below lower" not in report


@pytest.mark.parametrize(
    "kind,expected",
    [
        ("missed_motif", "miss pin tactics"),
        ("allowed_motif", "punishes you"),
        ("long_think_error", "long thinks"),
    ],
)
def test_each_claim_kind_reads_as_a_sentence(kind, expected):
    report = render(a_profile(a_finding(kind=kind)))

    assert expected in report


class TestNoInternalIdentifiersReachThePlayer:
    """Motif subjects are Lichess theme keys — camelCase identifiers chosen so
    the same name selects the training material. A player does not know what a
    `trappedPiece` is, so they are translated on the way out.

    Caught by reading a real report, not by a test: D4 groundedness scored 100 %
    on the same output because it only checks that a claim cites a game.
    """

    def test_the_finding_reads_in_english(self):
        report = render(a_profile(a_finding(kind="allowed_motif", subject="trappedPiece")))

        assert "a trapped piece that punishes you" in report

    @pytest.mark.parametrize(
        "subject,expected",
        [
            ("trappedPiece", "trapped piece"),
            ("hangingPiece", "hanging piece"),
            ("discoveredAttack", "discovered attack"),
            ("backRankMate", "back-rank mate"),
            ("capturingDefender", "capturing the defender"),
        ],
    )
    def test_the_progress_sign_reads_in_english_too(self, subject, expected):
        report = render(a_profile(a_finding(kind="missed_motif", subject=subject)))

        assert expected in report.split("WHAT WOULD SHOW IT WORKED")[1]

    def test_an_unmapped_subject_is_left_alone_rather_than_guessed_at(self):
        # Better that a new motif looks unfinished than that a spacing rule
        # invents a name for it.
        report = render(a_profile(a_finding(subject="someNewMotif")))

        assert "someNewMotif" in report
