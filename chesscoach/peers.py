"""The rating-peer reference population.

Design: docs/notes/architecture.peer-reference.md

M5 showed why this has to exist. Four of six real players had an elevated error
rate after long thinks, at 2.1-2.9x their own baseline, and every measurement was
correct. None was a diagnosis: a long think happens where the position is hard,
and hard positions produce errors. A within-player baseline cannot separate
"you are bad at this" from "everyone is bad at this". Only a population can.

Per-player contributions are kept rather than only the pooled rate, so a player
can be excluded from their own reference. Comparing someone against a population
containing themselves is circular, and with a small reference it visibly distorts
their own deviation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from chesscoach.profile.models import wilson_interval

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ConditionMeasurement:
    """One condition's raw numbers for one player: no judgement applied.

    This is what a section agent produces *before* the confidence policy runs.
    The reference builder wants exactly this, including the unremarkable ones.
    """

    claim_key: str
    instances: int
    opportunities: int
    distinct_games: int
    games_with_data: int

    @property
    def rate(self) -> float | None:
        """None when the condition never arose — distinct from a rate of zero."""
        if self.opportunities == 0:
            return None
        return self.instances / self.opportunities


@dataclass(frozen=True)
class PeerStats:
    """How a population behaves under one condition."""

    rate: float
    n_players: int
    n_moves: int
    instances: int

    @property
    def ci95(self) -> tuple[float, float]:
        return wilson_interval(self.instances, self.n_moves)


@dataclass(frozen=True)
class _Contribution:
    """One player's share of one population cell."""

    player: str
    instances: int
    opportunities: int


@dataclass(frozen=True)
class PeerReference:
    """Population rates per (band, time control, claim), at a fixed depth."""

    depth: int
    cells: dict[str, tuple[_Contribution, ...]] = field(default_factory=dict)

    @staticmethod
    def key(band: str, time_control: str, claim_key: str) -> str:
        return f"{band}|{time_control}|{claim_key}"

    def lookup(
        self, band: str, time_control: str, claim_key: str, excluding: str | None = None
    ) -> PeerStats | None:
        """Population statistics, optionally leaving one player out."""
        contributions = self.cells.get(self.key(band, time_control, claim_key))
        if not contributions:
            return None

        if excluding is not None:
            wanted = excluding.lower()
            contributions = tuple(c for c in contributions if c.player.lower() != wanted)

        opportunities = sum(c.opportunities for c in contributions)
        if not contributions or opportunities == 0:
            return None

        instances = sum(c.instances for c in contributions)
        return PeerStats(
            rate=instances / opportunities,
            n_players=len(contributions),
            n_moves=opportunities,
            instances=instances,
        )

    def merged_with(self, other: PeerReference) -> PeerReference:
        """Combine two references, refusing to mix analysis depths."""
        if other.depth != self.depth:
            raise ValueError(
                f"cannot merge references built at different depths: {self.depth} and {other.depth}"
            )

        cells = {key: tuple(value) for key, value in self.cells.items()}
        for key, contributions in other.cells.items():
            cells[key] = cells.get(key, ()) + tuple(contributions)
        return PeerReference(depth=self.depth, cells=cells)

    def save(self, path: Path | str) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "depth": self.depth,
            "cells": {
                key: [
                    {"player": c.player, "instances": c.instances, "opportunities": c.opportunities}
                    for c in contributions
                ]
                for key, contributions in self.cells.items()
            },
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: Path | str) -> PeerReference:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        version = payload.get("schema_version")
        if version != SCHEMA_VERSION:
            raise ValueError(f"unsupported peer reference schema_version {version!r}")

        return cls(
            depth=payload["depth"],
            cells={
                key: tuple(
                    _Contribution(
                        player=c["player"], instances=c["instances"], opportunities=c["opportunities"]
                    )
                    for c in contributions
                )
                for key, contributions in payload["cells"].items()
            },
        )


def build_reference(
    players: list[tuple[str, tuple[ConditionMeasurement, ...]]],
    band: str,
    time_control: str,
    depth: int,
) -> PeerReference:
    """Pool per-player measurements into a population reference.

    Conditions that never arose for a player contribute nothing — an absent
    condition is not the same as a condition observed at zero.
    """
    cells: dict[str, tuple[_Contribution, ...]] = {}

    for player, measurements in players:
        for measurement in measurements:
            if measurement.opportunities == 0:
                continue
            key = PeerReference.key(band, time_control, measurement.claim_key)
            cells[key] = cells.get(key, ()) + (
                _Contribution(
                    player=player,
                    instances=measurement.instances,
                    opportunities=measurement.opportunities,
                ),
            )

    return PeerReference(depth=depth, cells=cells)
