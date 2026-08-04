"""Profiles must survive a save/load round trip unchanged.

The profile is the integration contract between every agent; if it cannot be
written and read back identically then nothing downstream can be trusted, and
the B4 determinism test in the evaluation plan is impossible.
"""

from __future__ import annotations

import pytest

from chesscoach.profile.io import from_dict, load_profile, save_profile, to_dict
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
    Plan,
    PlanStep,
    PlayerProfile,
    PlayerRef,
    Provenance,
    SCHEMA_VERSION,
    StepOutcome,
)


def a_profile() -> PlayerProfile:
    finding = Finding(
        section="S2",
        claim=Claim.of(kind="time_pressure_error", subject="clock", direction="own",
                       context={"time_control": "rapid"}),
        measurement=Measurement(instances=12, distinct_games=8, games_with_data=40, rate=0.20,
                                peer_rate=0.12),
        provenance=Provenance(engine="Stockfish 18", depth=15, corpus_id="c1",
                              analysed_at="2026-07-28"),
        confidence=Confidence(tier=ConfidenceTier.PRIORITY, replicated=True,
                              reasons=("distinct_games>=8", "peer_lift>1.5")),
        gap_type=GapType(hypothesis=GapTypeHypothesis.PROCESS, determined_by=DeterminedBy.INFERRED),
        evidence=(Evidence(game_id="g7", ply=61, fen="8/8/8/8/8/8/8/K6k w - - 0 1",
                           move_played="Rf1", better_move="Rd8", loss_wp=41.0,
                           note="played in under two seconds with 40s left"),),
    )
    plan = Plan(
        created="2026-07-31",
        steps=(
            PlanStep(
                finding_id=finding.id,
                action="drill it",
                why="seen in 8 of 40 games",
                progress_sign="below 21.0% over the next 30 games",
                check_after_games=30,
                target_rate=0.21,
            ),
        ),
        outcomes=(
            StepOutcome(
                finding_id=finding.id,
                status="not_met",
                target_rate=0.21,
                previous_rate=0.30,
                observed_rate=0.28,
                games_since=31,
                checked_at="2026-09-01",
            ),
        ),
    )
    return PlayerProfile(
        player=PlayerRef(source="lichess", username="someone", ratings={"rapid": 1612}, band="1400-1800"),
        corpus=CorpusRef(corpus_id="c1", n_games=40, time_controls=("rapid",),
                         date_range=("2026-05-02", "2026-07-26"),
                         game_ids=("g1", "g2", "g3")),
        findings=(finding,),
        plan=plan,
    )


class TestRoundTrip:
    def test_dict_round_trip_preserves_the_profile(self):
        original = a_profile()

        assert from_dict(to_dict(original)) == original

    def test_file_round_trip_preserves_the_profile(self, tmp_path):
        original = a_profile()
        path = tmp_path / "profile.json"

        save_profile(original, path)

        assert load_profile(path) == original

    def test_serialisation_is_stable(self, tmp_path):
        # Same profile, same bytes -- required for the B4 determinism check.
        first, second = tmp_path / "a.json", tmp_path / "b.json"

        save_profile(a_profile(), first)
        save_profile(a_profile(), second)

        assert first.read_bytes() == second.read_bytes()

    def test_records_the_schema_version(self):
        assert to_dict(a_profile())["schema_version"] == SCHEMA_VERSION

    def test_refuses_an_unknown_schema_version(self):
        payload = to_dict(a_profile())
        payload["schema_version"] = SCHEMA_VERSION + 99

        with pytest.raises(ValueError, match="schema_version"):
            from_dict(payload)

    def test_refuses_a_version_older_than_anything_it_can_read(self):
        payload = to_dict(a_profile())
        payload["schema_version"] = 1

        with pytest.raises(ValueError, match="schema_version"):
            from_dict(payload)

    def test_reads_a_v3_profile_written_before_probes_existed(self):
        # v3 -> v4 added the `fragile` gap type and four ProbeRecord fields, all
        # optional. A v3 payload is therefore already a valid v4 profile, and
        # refusing it would throw away real analysis to no purpose.
        payload = to_dict(a_profile())
        payload["schema_version"] = 3

        profile = from_dict(payload)

        assert profile.probes == ()

    def test_an_upgraded_profile_is_stamped_with_the_current_version(self):
        # It is a v4 object in memory, so writing it back as v3 would claim a
        # shape it no longer has -- it can now carry probes.
        payload = to_dict(a_profile())
        payload["schema_version"] = 3

        assert from_dict(payload).schema_version == SCHEMA_VERSION


class TestProfileUpdates:
    def test_adding_findings_returns_a_new_profile(self):
        original = a_profile()

        updated = original.with_findings(())

        assert len(original.findings) == 1
        assert len(updated.findings) == 0

    def test_findings_can_be_filtered_by_section_for_ablation(self):
        # B3 ablation must be a filter, not a code branch.
        profile = a_profile()

        assert len(profile.without_section("S2").findings) == 0
        assert len(profile.without_section("S9").findings) == 1
