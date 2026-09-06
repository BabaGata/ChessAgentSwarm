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

SCHEMA_VERSION = 3

# v1 carried rates only. It still loads, and simply has no costs to offer.
#
# v2 counted an `allowed_motif` instance only when the opponent's **single best**
# reply executed the motif. v3 counts any reply that executes it and was worth
# playing -- within an inaccuracy of their best -- which finds about 20 % more
# ([[design.punishment-validity]]). The rates therefore mean different things,
# and comparing a v3 player against a v2 population compares two definitions
# (L-046). Everything else in a v2 file is still exactly what it says, so the
# file loads and only the redefined claims are refused.
READABLE_SCHEMA_VERSIONS = frozenset({1, 2, SCHEMA_VERSION})

# The prefix whose instances changed in v3.
_REDEFINED_IN_V3 = "allowed_motif."
FIRST_WORTH_PLAYING_SCHEMA = 3

# Pseudo-observations of prior weight used when there are too few peers to
# estimate one. Deliberately substantial: with a thin population, an extreme
# observed rate is far more likely to be noise than to be real.
DEFAULT_PRIOR_STRENGTH = 50.0

# Fewer contributors than this and the spread of rates says nothing.
MIN_PEERS_FOR_PRIOR = 3

# What share of a directory's games must actually be the speed it is being filed
# under. See `declared_speed_is_wrong`.
STRATUM_PURITY = 0.9


# How far past a band's edge a player's median rating may sit before they are
# no longer that band's player. Ratings are continuous and a player at the
# boundary drifts across it, so a band edge cannot be a hard line -- but where it
# stops being drift is a judgement, not a measurement, and it belongs to the
# thesis author. Small relative to the 400-point band width, and to V1's own
# +/-103 error, so it never claims more precision than the band has.
BAND_EDGE_TOLERANCE = 50


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
    # The schema the cells were written under. Anything built in this process is
    # current by construction; only `load` can produce an older one.
    schema_version: int = SCHEMA_VERSION

    def prices(self, claim_key: str) -> bool:
        """Whether this reference's numbers still mean what a lookup would assume.

        A pre-v3 file's `allowed_motif` rates counted only the opponent's single
        best reply, so comparing a player measured the new way against them
        compares two different definitions (L-046). The rest of the file is
        unaffected and stays usable -- discarding it would cost every other claim
        its peer comparison to fix these.
        """
        if self.schema_version >= FIRST_WORTH_PLAYING_SCHEMA:
            return True
        return not PeerReference.canonical(claim_key).startswith(_REDEFINED_IN_V3)

    @staticmethod
    def canonical(claim_key: str) -> str:
        """One spelling for a claim, on the way in and on the way out.

        Every claim in the system is `kind.subject.own`. The six development
        claims were written into references as `kind.subject`, because they
        predate the convention, and commit 20b1cef then normalised the *section*
        side through `_key()`. From that point the lookup missed and
        `slow_development`, `late_castling`, `repeat_move` and `opening_pawn_error`
        produced **no findings for anybody** -- four shipped, screened claims,
        silent because their baseline was spelled differently.

        I-07 recorded this shape one pair of arms earlier and called it fixed
        because both sides went through one function. There was a third side:
        the artefact already written to disk. Canonicalising here repairs those
        files instead of requiring an hour of engine time to reissue them.
        """
        return claim_key if claim_key.endswith(".own") else f"{claim_key}.own"

    @staticmethod
    def key(band: str, time_control: str, claim_key: str) -> str:
        return f"{band}|{time_control}|{PeerReference.canonical(claim_key)}"

    def lookup(
        self, band: str, time_control: str, claim_key: str, excluding: str | None = None
    ) -> PeerStats | None:
        """Population statistics, optionally leaving one player out.

        None for a claim this reference can no longer price -- see `prices`.
        """
        if not self.prices(claim_key):
            return None
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

    def opportunities_per_game(
        self,
        band: str,
        time_control: str,
        claim_key: str,
        excluding: str | None = None,
    ) -> float | None:
        """How often a player at this level meets the condition at all, per game.

        The denominator of every rate in this project is **opportunities**, which
        makes each rate conditional -- how badly you play once you are in the
        condition. That is deliberate (S1's docstring: a per-move rate would
        mostly measure how tactical the opponents were), and it means the rate
        alone cannot distinguish *handling something badly* from *meeting it
        constantly*.

        This is the missing half. Six of the twelve review players had a claim
        costing more than the population's while their rate sat at or below it,
        and exposure was the cause in every one.
        """
        contributions = [
            c
            for c in self._contributions(band, time_control, claim_key, excluding)
            if c.games_with_data > 0
        ]
        if not contributions:
            return None

        games = sum(c.games_with_data for c in contributions)
        return sum(c.opportunities for c in contributions) / games if games else None

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
        # A merge is only as current as its oldest input. Rebuilding without
        # carrying the version through would let an older file's numbers be
        # presented as current, which is the hazard the version exists to catch.
        return PeerReference(
            depth=self.depth,
            cells=cells,
            schema_version=min(self.schema_version, other.schema_version),
        )

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

        # Cell keys are canonicalised on the way in, so a reference written
        # before the `.own` convention reaches the same cell as a lookup made
        # after it. Without this the four development claims stay mute against
        # every reference already on disk, and only an engine pass could fix
        # them.
        def canonical_cell(key: str) -> str:
            band, time_control, claim = key.split("|", 2)
            return PeerReference.key(band, time_control, claim)

        return cls(
            depth=payload["depth"],
            schema_version=version,
            cells={
                canonical_cell(key): tuple(
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


def declared_speed_is_wrong(games, declared: str) -> str | None:
    """Is `--time-control` a fair label for these games? Returns why not, or None.

    `build-peer-reference` applies one speed label to a whole directory instead
    of reading each game's own, which is fine when the directory was fetched one
    speed at a time and a silent disaster otherwise: a mixed directory built as
    `rapid` yields a reference with no blitz stratum, and every `_mixed` lookup
    for a blitz-heavy player then returns None. The peer comparison and the band
    notes disappear from a report that still renders and still looks complete.

    Near-purity is demanded rather than a bare majority, and the difference is
    not academic: the first corpus this was run against was 63 % rapid, passed a
    majority test, and still filed **51 blitz games** under `rapid`. A directory
    fetched one speed at a time is essentially pure, so anything short of that
    means the fetch was not stratified. The tolerance exists only because
    `speed_class` reimplements Lichess's boundary rule and may disagree with it
    on a handful of games near the edges.

    Games with no readable control abstain rather than vote: correspondence
    games have no speed, and should not outvote the games that do.
    """
    from collections import Counter

    from chesscoach.speed import speed_class

    speeds = Counter(
        speed for speed in (speed_class(getattr(g, "time_control", None)) for g in games) if speed
    )
    if not speeds:
        return None

    (dominant, count), = speeds.most_common(1)
    if dominant == declared and count >= STRATUM_PURITY * sum(speeds.values()):
        return None

    breakdown = ", ".join(f"{speed} {n}" for speed, n in speeds.most_common())
    strays = sum(n for speed, n in speeds.items() if speed != declared)

    # Two different mistakes, and telling someone the label is wrong when the
    # label is right sends them to fix the wrong thing.
    fault = (
        f"{strays} of these {sum(speeds.values())} games are not {declared}"
        if dominant == declared
        else f"these games are mostly {dominant}, not {declared}"
    )
    return (
        f"{fault} ({breakdown}). --time-control labels the whole directory rather "
        f"than reading each game, so those games would be filed as {declared} and "
        f"counted into the wrong population rate. Fetch one speed at a time "
        f"(fetch-corpus --speed {declared}) and add the other strata with --merge-with"
    )



def declared_band_is_wrong(games, player: str, declared: str) -> str | None:
    """Is `--band` a fair label for this player? Returns why not, or None.

    The sibling of `declared_speed_is_wrong`, and the reason it exists is that a
    peer lookup is keyed on **both** `band` and `time_control` and only one of
    them was ever checked against the games. I-03's recorded lesson was that a
    cross-cutting fix must be applied at every place that makes the comparison;
    it was applied to the speed arm alone, and the band arm kept the defect.

    What that allowed, measured on the twelve review players: six sit outside
    1400-1800 and all six were compared against it. The three strongest -- 1930,
    1988, 1988 -- came out with **no findings at all**, which the report renders
    as nothing being unusual about their play. It is not a statement about their
    play. It is the result of comparing them against players rated below them,
    and nothing in the output distinguishes the two.

    **The median decides, not a share.** Purity is right for a categorical label
    like speed and wrong for a continuous one: a player either played a blitz
    game or did not, but a rating wanders, and demanding that 90 % of games fall
    inside a band would refuse everyone near an edge. `BAND_EDGE_TOLERANCE`
    covers the drift; past it, the player is somebody else's peer.

    **The player's own rating is what is read.** Banding by whoever they happened
    to play would make a strong opponent enough to reband them, which is how a
    player who plays up ends up compared against a population they never joined.

    Games with no readable rating abstain rather than vote, and no readable
    ratings at all is not an accusation -- both the same rule the speed guard
    follows, for the same reason: nothing to check against is not a mismatch.
    """
    from statistics import median

    try:
        low_text, _, high_text = declared.partition("-")
        low, high = int(low_text), int(high_text)
    except ValueError:
        # An unparseable band cannot be compared against anything. Returning None
        # would say "this player is fine", which is the empty case answering
        # exactly like a populated one (L-046).
        return (
            f"--band {declared!r} is not a band. It must read LOW-HIGH, as in "
            f"1400-1800, because it is half the key every peer lookup is made on"
        )

    ratings = []
    for game in games:
        white = getattr(game, "white", "") or ""
        black = getattr(game, "black", "") or ""
        if white.lower() == player.lower():
            rating = getattr(game, "white_elo", None)
        elif black.lower() == player.lower():
            rating = getattr(game, "black_elo", None)
        else:
            continue
        if rating is not None:
            ratings.append(rating)

    if not ratings:
        return None

    typical = median(ratings)
    if low - BAND_EDGE_TOLERANCE <= typical <= high + BAND_EDGE_TOLERANCE:
        return None

    side = "above" if typical > high else "below"
    distance = typical - high if typical > high else low - typical
    return (
        f"{player} is rated about {typical:.0f}, which is {distance:.0f} points "
        f"{side} the {declared} band ({len(ratings)} games read). Every peer "
        f"comparison is keyed on the band, so this player would be measured "
        f"against a population they are not in -- and 'more often than players "
        f"at your level' would name the wrong level. Pass the --band they are "
        f"actually in, and build a reference for it"
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
