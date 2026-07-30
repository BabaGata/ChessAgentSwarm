"""S2 — decision process and clock behaviour, the first section agent.

Design: docs/notes/capacity.agents.s2-decision-process.md

The agent's contract is as important as its detections: it must stay silent when
the evidence does not support a finding, distinguish "no problem" from "not
enough data", and never present its self-baseline comparison as a peer one.
"""

from __future__ import annotations

import pytest

from chesscoach.analysis.labels import ErrorLabel
from chesscoach.analysis.observations import Observation
from chesscoach.ingest.corpus import Corpus
from chesscoach.peers import ConditionMeasurement, PeerReference, build_reference
from chesscoach.profile.models import Claim, ConfidenceTier, GapTypeHypothesis, Provenance
from chesscoach.sections.s2_decision_process import S2DecisionProcess, SectionContext

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-07-28")


def observation(
    game: int,
    ply: int,
    *,
    clock_after: float,
    seconds: float,
    error: bool,
    mover: str = "alice",
    score_cp_before: int = 0,
) -> Observation:
    return Observation(
        game_id=f"g{game:03d}",
        ply=ply,
        mover=mover,
        mover_is_white=True,
        fen_before="8/8/8/8/8/8/8/K6k w - - 0 1",
        move_played="a1a2",
        best_move="a1b1",
        score_cp_before=score_cp_before,
        score_cp_after=-300 if error else 0,
        loss_wp=40.0 if error else 0.0,
        label=ErrorLabel.BLUNDER if error else None,
        phase="late_middlegame",
        played_best=not error,
        clock_before=clock_after + seconds,
        clock_after=clock_after,
        engine="stub",
        depth=15,
    )


def a_context(observations, n_games: int = 30) -> SectionContext:
    corpus = Corpus(
        username="alice",
        corpus_id="c1",
        game_ids=tuple(f"g{n:03d}" for n in range(n_games)),
    )
    return SectionContext(observations=tuple(observations), corpus=corpus, provenance=PROVENANCE)


def player_with_time_trouble(n_games: int, errors_in_pressure: int) -> list[Observation]:
    """Clean at leisure, error-prone when the clock is low."""
    observations: list[Observation] = []
    for game in range(n_games):
        for ply in range(11, 31, 2):  # 10 comfortable moves
            observations.append(observation(game, ply, clock_after=400.0, seconds=10.0, error=False))
        for index, ply in enumerate(range(31, 41, 2)):  # 5 moves under pressure
            observations.append(
                observation(
                    game, ply, clock_after=20.0, seconds=3.0, error=index < errors_in_pressure
                )
            )
    return observations


class TestTimePressure:
    def test_finds_a_clear_time_pressure_weakness(self):
        agent = S2DecisionProcess()

        findings = agent.findings(a_context(player_with_time_trouble(30, errors_in_pressure=3)))

        time_findings = [f for f in findings if f.claim.kind == "time_pressure_error"]
        assert len(time_findings) == 1
        assert time_findings[0].confidence.tier in (ConfidenceTier.FOCUS, ConfidenceTier.PRIORITY)

    def test_says_nothing_about_a_player_who_is_fine_under_pressure(self):
        agent = S2DecisionProcess()

        findings = agent.findings(a_context(player_with_time_trouble(30, errors_in_pressure=0)))

        assert [f for f in findings if f.claim.kind == "time_pressure_error"] == []

    def test_stays_silent_when_there_is_too_little_data(self):
        agent = S2DecisionProcess()

        findings = agent.findings(a_context(player_with_time_trouble(4, errors_in_pressure=3), 4))

        assert findings == ()

    def test_reports_insufficient_data_separately_from_no_finding(self):
        agent = S2DecisionProcess()

        report = agent.report(a_context(player_with_time_trouble(4, errors_in_pressure=3), 4))

        assert report.insufficient_data is True
        assert report.findings == ()


class TestFindingContent:
    def test_carries_provenance_including_depth(self):
        agent = S2DecisionProcess()

        finding = agent.findings(a_context(player_with_time_trouble(30, 3)))[0]

        assert finding.provenance.depth == 15
        assert finding.provenance.corpus_id == "c1"

    def test_attaches_evidence(self):
        agent = S2DecisionProcess()

        finding = agent.findings(a_context(player_with_time_trouble(30, 3)))[0]

        assert len(finding.evidence) > 0
        assert all(e.game_id.startswith("g") for e in finding.evidence)

    def test_evidence_sampling_is_deterministic(self):
        observations = player_with_time_trouble(30, 3)

        first = S2DecisionProcess().findings(a_context(observations))[0]
        second = S2DecisionProcess().findings(a_context(observations))[0]

        assert first.evidence == second.evidence

    def test_records_the_baseline_it_compared_against(self):
        agent = S2DecisionProcess()

        finding = agent.findings(a_context(player_with_time_trouble(30, 3)))[0]

        assert finding.measurement.baseline_rate == 0.0
        assert finding.measurement.rate > 0

    def test_does_not_claim_a_peer_comparison_it_cannot_make(self):
        # No reference population exists yet, so peer_rate must stay empty
        # rather than being quietly filled with the self-baseline.
        agent = S2DecisionProcess()

        finding = agent.findings(a_context(player_with_time_trouble(30, 3)))[0]

        assert finding.measurement.peer_rate is None

    def test_hypothesises_a_process_gap_by_inference(self):
        agent = S2DecisionProcess()

        finding = agent.findings(a_context(player_with_time_trouble(30, 3)))[0]

        assert finding.gap_type.hypothesis is GapTypeHypothesis.PROCESS
        assert finding.gap_type.determined_by.value == "inferred"

    def test_belongs_to_section_s2(self):
        agent = S2DecisionProcess()

        assert all(f.section == "S2" for f in agent.findings(a_context(player_with_time_trouble(30, 3))))


class TestInstantMoves:
    def test_finds_a_player_who_blunders_when_moving_instantly(self):
        observations: list[Observation] = []
        for game in range(30):
            for ply in range(11, 31, 2):
                observations.append(
                    observation(game, ply, clock_after=400.0, seconds=12.0, error=False)
                )
            for index, ply in enumerate(range(31, 39, 2)):
                observations.append(
                    observation(game, ply, clock_after=380.0, seconds=1.0, error=index < 2)
                )

        findings = S2DecisionProcess().findings(a_context(observations))

        assert any(f.claim.kind == "instant_move_error" for f in findings)

    def test_ignores_the_opening_where_instant_moves_are_legitimate(self):
        observations = [
            observation(game, ply, clock_after=590.0, seconds=0.5, error=True)
            for game in range(30)
            for ply in range(1, 8)
        ]

        findings = S2DecisionProcess().findings(a_context(observations))

        assert findings == ()


def long_think_player() -> list[Observation]:
    observations: list[Observation] = []
    for game in range(30):
        for ply in range(11, 31, 2):
            observations.append(
                observation(game, ply, clock_after=400.0, seconds=10.0, error=False)
            )
        for index, ply in enumerate(range(31, 37, 2)):
            observations.append(
                observation(game, ply, clock_after=200.0, seconds=90.0, error=index < 2)
            )
    return observations


class TestLongThink:
    def test_measures_the_long_think_signature_but_withholds_it(self):
        # A long think happens *because* the position is hard, and hard
        # positions produce errors. Against the player's own baseline that is
        # indistinguishable from something every player does — confirmed in M5,
        # where four of six real players showed it at a similar magnitude.
        report = S2DecisionProcess().report(a_context(long_think_player()))

        assert [f.claim.kind for f in report.findings] == []
        assert any("long_think_error" in note for note in report.notes)

    def test_the_withheld_note_says_what_is_missing(self):
        report = S2DecisionProcess().report(a_context(long_think_player()))

        assert any("rating-peer baseline" in note for note in report.notes)


def peers_with(long_think_rate: float) -> PeerReference:
    """A reference population whose long-think error rate is `long_think_rate`."""
    key = Claim.of(kind="long_think_error", subject="long_think").key()
    return build_reference(
        [
            (name, (ConditionMeasurement(key, int(long_think_rate * 1000), 1000, 20, 40),))
            for name in ("peer1", "peer2", "peer3")
        ],
        band="1400-1800",
        time_control="rapid",
        depth=15,
    )


def with_peers(observations, peers: PeerReference) -> SectionContext:
    base = a_context(observations)
    return SectionContext(
        observations=base.observations,
        corpus=base.corpus,
        provenance=base.provenance,
        band="1400-1800",
        time_control="rapid",
        peers=peers,
    )


class TestPeerComparison:
    def test_stays_silent_when_peers_are_just_as_bad(self):
        # The M5 case: correct measurement, no diagnosis. The player's long-think
        # error rate is ~67%, and so is everyone else's.
        report = S2DecisionProcess().report(with_peers(long_think_player(), peers_with(0.67)))

        assert [f.claim.kind for f in report.findings] == []

    def test_speaks_when_the_player_is_worse_than_their_peers(self):
        report = S2DecisionProcess().report(with_peers(long_think_player(), peers_with(0.10)))

        assert [f.claim.kind for f in report.findings] == ["long_think_error"]

    def test_records_the_peer_rate_it_compared_against(self):
        report = S2DecisionProcess().report(with_peers(long_think_player(), peers_with(0.10)))

        assert report.findings[0].measurement.peer_rate == pytest.approx(0.10)
        assert report.findings[0].measurement.lift_vs_peer > 1

    def test_never_compares_a_player_against_a_population_containing_them(self):
        key = Claim.of(kind="long_think_error", subject="long_think").key()
        peers = build_reference(
            [
                ("alice", (ConditionMeasurement(key, 900, 1000, 20, 40),)),  # the subject
                ("peer1", (ConditionMeasurement(key, 100, 1000, 20, 40),)),
            ],
            band="1400-1800",
            time_control="rapid",
            depth=15,
        )

        report = S2DecisionProcess().report(with_peers(long_think_player(), peers))

        # Alice's own inflated contribution must not raise the bar she is judged against.
        assert report.findings[0].measurement.peer_rate == pytest.approx(0.10)


class TestMeasure:
    def test_reports_raw_rates_without_judgement(self):
        measurements = S2DecisionProcess().measure(a_context(player_with_time_trouble(30, 3)))

        by_key = {m.claim_key: m for m in measurements}
        pressure = by_key["time_pressure_error.clock.own"]
        assert pressure.opportunities == 150
        assert pressure.instances == 90

    def test_includes_conditions_that_would_never_be_asserted(self):
        # The peer builder needs the unremarkable numbers too.
        measurements = S2DecisionProcess().measure(a_context(player_with_time_trouble(30, 0)))

        assert any(m.instances == 0 and m.opportunities > 0 for m in measurements)

    def test_a_condition_that_never_arose_has_no_opportunities(self):
        measurements = S2DecisionProcess().measure(a_context(player_with_time_trouble(30, 3)))

        by_key = {m.claim_key: m for m in measurements}
        assert by_key["instant_move_error.instant_moves.own"].opportunities == 0


class TestDataGate:
    def test_gates_on_games_with_data_for_the_section_not_per_condition(self):
        # A condition that only arises in some games must still be assertable.
        # Gating each condition on its own frequency would make a rare but
        # severe weakness permanently unsayable, however badly it went.
        observations: list[Observation] = []
        for game in range(30):
            for ply in range(11, 31, 2):
                observations.append(
                    observation(game, ply, clock_after=400.0, seconds=10.0, error=False)
                )
            if game < 12:  # time trouble in only 12 of 30 games
                for index, ply in enumerate(range(31, 41, 2)):
                    observations.append(
                        observation(game, ply, clock_after=20.0, seconds=3.0, error=index < 3)
                    )

        findings = S2DecisionProcess().findings(a_context(observations))

        assert [f.claim.kind for f in findings] == ["time_pressure_error"]
        assert findings[0].measurement.games_with_data == 30

    def test_reports_insufficient_data_below_the_section_gate(self):
        report = S2DecisionProcess().report(a_context(player_with_time_trouble(9, 3), 9))

        assert report.insufficient_data is True
        assert "9 games" in " ".join(report.notes)


class TestDecidedPositions:
    def test_ignores_errors_made_in_already_lost_positions(self):
        # Win probability compresses at the extremes (L-009), so errors there
        # are cheap and uninformative -- and no coach diagnoses decision-making
        # from a position that was already lost.
        observations = [
            observation(
                game, ply, clock_after=20.0, seconds=1.0, error=True, score_cp_before=-1200
            )
            for game in range(30)
            for ply in range(11, 21, 2)
        ]

        assert S2DecisionProcess().findings(a_context(observations)) == ()

    def test_still_reports_when_the_game_was_competitive(self):
        observations = player_with_time_trouble(30, errors_in_pressure=3)

        assert S2DecisionProcess().findings(a_context(observations)) != ()


class TestContract:
    def test_returns_nothing_for_an_empty_corpus(self):
        assert S2DecisionProcess().findings(a_context([], 0)) == ()

    def test_ignores_moves_played_by_the_opponent(self):
        observations = player_with_time_trouble(30, 3)
        opponent = [
            observation(game, 12, clock_after=5.0, seconds=1.0, error=True, mover="bob")
            for game in range(30)
        ]

        findings = S2DecisionProcess().findings(a_context(observations + opponent))

        assert all("bob" not in (e.note or "") for f in findings for e in f.evidence)

    def test_findings_are_ordered_deterministically(self):
        observations = player_with_time_trouble(30, 3)

        first = S2DecisionProcess().findings(a_context(observations))
        second = S2DecisionProcess().findings(a_context(observations))

        assert [f.id for f in first] == [f.id for f in second]
