"""The `coach` command: one session from a username to a readable report.

Spec: docs/notes/architecture.interaction.md § 1

Every stage was already tested individually; what is tested here is that they
are one thing, and the two decisions the wiring makes — that a missing peer
reference stops the session rather than producing an unfounded one, and that a
probed gap type is reported **with its provenance** rather than as a fact.
"""

from __future__ import annotations

import argparse

import pytest

from chesscoach.explainer import render
from chesscoach.ingest.lichess import LichessUnavailable, fetch_games_pgn
from chesscoach.profile.models import (
    Claim,
    ClassifierStatus,
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
    ProbeRecord,
    Provenance,
)

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-08-06")


def a_finding(gap_type: GapType | None = None) -> Finding:
    return Finding(
        section="S1",
        claim=Claim.of(kind="missed_motif", subject="pin"),
        measurement=Measurement(
            instances=9, distinct_games=8, games_with_data=24, rate=0.30, peer_rate=0.12
        ),
        provenance=PROVENANCE,
        confidence=Confidence(tier=ConfidenceTier.PRIORITY, replicated=True),
        gap_type=gap_type
        or GapType(hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED),
        evidence=(Evidence(game_id="g1", ply=20, fen="8/8/8/8/8/8/8/K6k w - - 0 1"),),
    )


def a_probe(finding_id: str, status: str) -> ProbeRecord:
    return ProbeRecord(
        id="probe.1",
        finding_id=finding_id,
        fen="8/8/8/8/8/8/8/K6k w - - 0 1",
        asks="What would you play here, and why?",
        player_move="Bb5",
        player_reason="it pins the knight",
        move_correct=True,
        reason_matched=True,
        classifier="ollama/test",
        classifier_status=status,
    )


def a_profile(*findings: Finding, probes: tuple[ProbeRecord, ...] = ()) -> PlayerProfile:
    from chesscoach.arbiter import select_priorities
    from chesscoach.planner import build_plan

    plan = build_plan(select_priorities(findings).priorities, created="2026-08-06")
    return PlayerProfile(
        player=PlayerRef(source="lichess", username="alice", band="1400-1800"),
        corpus=CorpusRef(corpus_id="c1", n_games=24),
        findings=findings,
        probes=probes,
        plan=plan,
    )


class TestProbedGapTypesCarryTheirProvenance:
    """D10 is unresolved, so a probed gap type is better evidence than an
    inference and still thin. The report says so rather than asserting it."""

    def probed(self, hypothesis: GapTypeHypothesis) -> PlayerProfile:
        gap = GapType(hypothesis=hypothesis, determined_by=DeterminedBy.PROBED)
        finding = a_finding(gap_type=gap)
        return a_profile(
            finding, probes=(a_probe(finding.id, ClassifierStatus.ANSWERED.value),)
        )

    def test_the_meaning_is_stated(self):
        report = render(self.probed(GapTypeHypothesis.SKILL))

        assert "spotting it during a game" in report

    def test_and_so_is_where_it_came_from(self):
        report = render(self.probed(GapTypeHypothesis.SKILL))

        assert "From 1 question you answered" in report
        assert "three times in four" in report

    def test_an_unread_reason_is_described_differently(self):
        # The move was checked deterministically; the reason never reached a
        # model. Claiming a classifier read it would be false.
        gap = GapType(hypothesis=GapTypeHypothesis.KNOWLEDGE, determined_by=DeterminedBy.PROBED)
        finding = a_finding(gap_type=gap)
        profile = a_profile(
            finding, probes=(a_probe(finding.id, ClassifierStatus.UNAVAILABLE.value),)
        )

        report = render(profile)

        assert "the reason was not read" in report

    def test_an_inferred_gap_type_says_nothing_at_all(self):
        report = render(a_profile(a_finding()))

        assert "From 1 question" not in report
        assert "worth learning" not in report


class TestFetching:
    def test_a_missing_user_is_reported_as_such(self, monkeypatch):
        # Patched at `urlopen`, not at `_get` — `_get` is what turns these into
        # LichessUnavailable, so replacing it would test nothing.
        import urllib.error
        import urllib.request

        def refuse(request, timeout=0):
            raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, None)

        monkeypatch.setattr(urllib.request, "urlopen", refuse)

        with pytest.raises(LichessUnavailable, match="no such user"):
            fetch_games_pgn("nobody", 10)

    def test_an_unreachable_api_does_not_look_like_an_empty_account(self, monkeypatch):
        import urllib.error
        import urllib.request

        def unreachable(request, timeout=0):
            raise urllib.error.URLError("connection refused")

        monkeypatch.setattr(urllib.request, "urlopen", unreachable)

        with pytest.raises(LichessUnavailable, match="could not reach"):
            fetch_games_pgn("alice", 10)

    def test_a_rate_limit_is_not_confused_with_a_missing_user(self, monkeypatch):
        import urllib.error
        import urllib.request

        def throttle(request, timeout=0):
            raise urllib.error.HTTPError(request.full_url, 429, "Too Many", {}, None)

        monkeypatch.setattr(urllib.request, "urlopen", throttle)
        monkeypatch.setattr("chesscoach.ingest.lichess.RATE_LIMIT_BACKOFF_S", 0)

        with pytest.raises(LichessUnavailable, match="HTTP 429"):
            fetch_games_pgn("alice", 10)

    def test_it_asks_only_for_the_time_controls_the_swarm_can_compare(self, monkeypatch):
        # Mixing bullet into a profile measures the clock, not the player
        # (E01, domain.signals).
        seen = {}

        def capture(url, accept="application/json"):
            seen["url"] = url
            return b""

        monkeypatch.setattr("chesscoach.ingest.lichess._get", capture)
        fetch_games_pgn("alice", 25)

        assert "perfType=rapid,classical" in seen["url"]
        assert "max=25" in seen["url"]
        assert "clocks=true" in seen["url"]


class TestTheCommandRefusesToGuess:
    def test_without_a_reference_population_it_stops(self, capsys):
        from chesscoach.cli import _load_peers

        args = argparse.Namespace(peers=None, depth=15)

        assert _load_peers(args) is None
        assert "nothing can be called unusual" in capsys.readouterr().out

    def test_a_reference_from_another_depth_is_refused(self, tmp_path, capsys):
        from chesscoach.cli import _load_peers
        from chesscoach.peers import ConditionMeasurement, build_reference

        reference = build_reference(
            [("peer", (ConditionMeasurement("k", 1, 10, 2, 5),))],
            band="1400-1800",
            time_control="rapid",
            depth=12,
        )
        path = tmp_path / "peers.json"
        reference.save(path)

        assert _load_peers(argparse.Namespace(peers=str(path), depth=15)) is None
        assert "not comparable across depths" in capsys.readouterr().out
