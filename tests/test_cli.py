"""CLI wiring: argument parsing, reporting and the observations dump."""

from __future__ import annotations

import json

import pytest

from chesscoach.analysis.labels import ErrorLabel
from chesscoach.analysis.observations import Observation
from chesscoach.cli import _report, _write_observations, build_parser


def an_observation(**overrides) -> Observation:
    defaults = dict(
        game_id="g1",
        ply=7,
        mover="alice",
        mover_is_white=True,
        fen_before="8/8/8/8/8/8/8/K6k w - - 0 1",
        move_played="a1a2",
        best_move="a1b1",
        score_cp_before=10,
        score_cp_after=-400,
        loss_wp=38.0,
        label=ErrorLabel.BLUNDER,
        phase="late_middlegame",
        played_best=False,
        clock_before=300.0,
        clock_after=291.5,
        engine="stub",
        depth=15,
    )
    return Observation(**{**defaults, **overrides})


class TestParser:
    def test_analyse_requires_the_essential_arguments(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args(["analyse", "--pgn", "x"])

    def test_parses_a_complete_analyse_invocation(self):
        args = build_parser().parse_args(
            ["analyse", "--pgn", "games", "--player", "alice", "--engine", "sf", "--out", "p.json"]
        )

        assert args.player == "alice"
        assert args.depth == 15  # E01's working setting is the default

    def test_a_command_is_required(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args([])


class TestReport:
    def test_reports_counts_and_the_error_rate(self, capsys):
        _report((an_observation(), an_observation(label=None, loss_wp=1.0)), cache=None)

        printed = capsys.readouterr().out
        assert "moves    2" in printed
        assert "50.0%" in printed

    def test_reports_the_phase_breakdown(self, capsys):
        _report((an_observation(phase="endgame"),), cache=None)

        assert "endgame 1" in capsys.readouterr().out


class TestObservationsDump:
    def test_writes_one_json_object_per_move(self, tmp_path):
        path = tmp_path / "moves.jsonl"

        _write_observations((an_observation(), an_observation(ply=9)), path)

        lines = path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2

    def test_serialises_the_label_as_a_plain_string(self, tmp_path):
        path = tmp_path / "moves.jsonl"

        _write_observations((an_observation(),), path)

        assert json.loads(path.read_text(encoding="utf-8"))["label"] == "blunder"

    def test_writes_null_when_a_move_was_not_an_error(self, tmp_path):
        path = tmp_path / "moves.jsonl"

        _write_observations((an_observation(label=None),), path)

        assert json.loads(path.read_text(encoding="utf-8"))["label"] is None
