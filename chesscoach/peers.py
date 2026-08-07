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
import statistics
from dataclasses import dataclass, field
from pathlib import Path

from chesscoach.profile.models import wilson_interval
from chesscoach.shrinkage import posterior

SCHEMA_VERSION = 2

# v1 carried rates only. It still loads, and simply has no costs to offer.
READABLE_SCHEMA_VERSIONS = frozenset({1, SCHEMA_VERSION})

# Pseudo-observations of prior weight used when there are too few peers to
# estimate one. Deliberately substantial: with a thin population, an extreme
# observed rate is far more likely to be noise than to be real.
DEFAULT_PRIOR_STRENGTH = 50.0

# Fewer contributors than this and the spread of rates says nothing.
MIN_PEERS_FOR_PRIOR = 3


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
    # Win probability given away on this claim's instances. **None where the
    # instances are not mistakes** -- conceding a structure is a choice, not a
    # move that lost anything measurable. Populated so the population can be
    # asked what a claim costs *everyone*, which is what turns a raw cost into
    # a recoverable one (step 3).
    cost_wp: float | None = None

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
    # Both None for a claim that cannot price itself, and for every reference
    # written before schema 2.
    cost_wp: float | None = None
    games_with_data: int = 0


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

    def cost_per_game(
        self,
        band: str,
        time_control: str,
        claim_key: str,
        excluding: str | None = None,
    ) -> float | None:
        """What this claim costs a player at this level, per game.

        The denominator counts **only players who could price the claim**.
        Treating a missing cost as zero would understate the population and
        inflate every player's excess against it — the arithmetic version of
        assuming everyone else is fine.
        """
        contributions = [
            c
            for c in self._contributions(band, time_control, claim_key, excluding)
            if c.cost_wp is not None and c.games_with_data > 0
        ]
        if not contributions:
            return None

        games = sum(c.games_with_data for c in contributions)
        return sum(c.cost_wp for c in contributions) / games if games else None

    def prior_for(
        self,
        band: str,
        time_control: str,
        claim_key: str,
        excluding: str | None = None,
    ) -> tuple[float, float] | None:
        """The population rate and how hard it should pull, or None if unknown.

        The two numbers a posterior needs. Returned together because using one
        without the other -- a population rate with a guessed strength -- is how
        a shrinkage estimate quietly becomes an opinion.
        """
        contributions = self._contributions(band, time_control, claim_key, excluding)
        if not contributions:
            return None
        opportunities = sum(c.opportunities for c in contributions)
        if opportunities == 0:
            return None
        rate = sum(c.instances for c in contributions) / opportunities
        return rate, prior_strength(contributions)

    def expected_rate(
        self,
        band: str,
        time_control: str,
        claim_key: str,
        instances: int,
        opportunities: int,
        excluding: str | None = None,
    ) -> float | None:
        """What this player's rate really is, allowing for how little data there is.

        An empirical-Bayes estimate: the observed rate pulled toward the
        population, by an amount the population itself determines. This is the
        answer to E05 -- a finding is selected for being extreme, and extremes
        regress, so the selected value is a biased estimate of the truth and must
        not be what a prediction is measured from.

        Also the honest prediction for "nothing changes": if the player carries
        on as they are, this is roughly where the next measurement lands.
        """
        if opportunities <= 0:
            return None

        found = self.prior_for(band, time_control, claim_key, excluding)
        if found is None:
            return None

        population, strength = found
        # One shrinkage formula in the system rather than two. `chesscoach.
        # shrinkage` holds the distribution this is the mean of, so a caller who
        # needs the uncertainty as well as the estimate gets a consistent answer.
        return posterior(instances, opportunities, population, strength).mean

    def _contributions(
        self, band: str, time_control: str, claim_key: str, excluding: str | None
    ) -> tuple[_Contribution, ...]:
        contributions = self.cells.get(self.key(band, time_control, claim_key), ())
        if excluding is None:
            return contributions
        wanted = excluding.lower()
        return tuple(c for c in contributions if c.player.lower() != wanted)

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
                    {
                        "player": c.player,
                        "instances": c.instances,
                        "opportunities": c.opportunities,
                        "cost_wp": c.cost_wp,
                        "games_with_data": c.games_with_data,
                    }
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
        if version not in READABLE_SCHEMA_VERSIONS:
            raise ValueError(
                f"unsupported peer reference schema_version {version!r}, "
                f"readable: {sorted(READABLE_SCHEMA_VERSIONS)}"
            )

        return cls(
            depth=payload["depth"],
            cells={
                key: tuple(
                    _Contribution(
                        player=c["player"],
                        instances=c["instances"],
                        opportunities=c["opportunities"],
                        # Absent in v1, where costs were not recorded at all. An
                        # honest None, never a zero that would read as "free".
                        cost_wp=c.get("cost_wp"),
                        games_with_data=c.get("games_with_data", 0),
                    )
                    for c in contributions
                )
                for key, contributions in payload["cells"].items()
            },
        )


def prior_strength(contributions: tuple[_Contribution, ...]) -> float:
    """How much the population should outweigh one player's observation.

    Estimated by method of moments on a beta-binomial: if peers' rates differ
    widely, most of the spread is real and an individual's observation is
    informative, so shrink little. If they are all alike, most of the spread in
    any one measurement is sampling noise, so shrink hard.

    This is the "how much" that E05 showed cannot be guessed -- it is a property
    of the population, and the population is already stored.
    """
    usable = [c for c in contributions if c.opportunities > 0]
    if len(usable) < MIN_PEERS_FOR_PRIOR:
        return DEFAULT_PRIOR_STRENGTH

    rates = [c.instances / c.opportunities for c in usable]
    mean_rate = sum(c.instances for c in usable) / sum(c.opportunities for c in usable)
    if mean_rate <= 0 or mean_rate >= 1:
        return DEFAULT_PRIOR_STRENGTH

    observed_variance = statistics.pvariance(rates)
    # Part of that spread is just sampling noise, and only the remainder is real
    # variation between players.
    sampling_variance = statistics.mean(
        mean_rate * (1 - mean_rate) / c.opportunities for c in usable
    )
    between = observed_variance - sampling_variance
    if between <= 0:
        return DEFAULT_PRIOR_STRENGTH

    strength = mean_rate * (1 - mean_rate) / between - 1
    return max(strength, 1.0)


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
                    cost_wp=measurement.cost_wp,
                    games_with_data=measurement.games_with_data,
                ),
            )

    return PeerReference(depth=depth, cells=cells)
