"""The contract every section agent obeys.

From docs/notes/architecture.orchestration.md. Section agents run in parallel and
in isolation, communicating only through the player profile. Two rules here are
the ones most likely to be violated under pressure to make a demo look good:

  * an agent **may return zero findings**, and must when the evidence does not
    support one — "always produce something" is how filler is born;
  * an agent **never calls a language model**. Diagnosis is deterministic; the
    language layer runs later, on the profile.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Iterable, Protocol

from chesscoach.analysis.observations import Observation
from chesscoach.ingest.corpus import Corpus
from chesscoach.separation import separates
from chesscoach.peers import ConditionMeasurement, PeerReference
from chesscoach.profile.models import ConfidenceTier, Finding, Provenance


# Which moves are worth diagnosing at all. Shared by every section so the answer
# cannot drift between them.
#
# Book moves carry little information and structures have not formed, so the
# opening is skipped. And beyond DECIDED_CP the game is effectively over: win
# probability compresses at the extremes (L-009), making errors there both cheap
# to commit and nearly invisible to measure -- and no coach diagnoses a player
# from an already-lost position.
OPENING_GRACE_PLIES = 8
DECIDED_CP = 500


def diagnosable(observations: tuple[Observation, ...]) -> tuple[Observation, ...]:
    """Post-opening moves played while the game was still competitive."""
    return tuple(
        o
        for o in observations
        if o.ply > OPENING_GRACE_PLIES and abs(o.score_cp_before) <= DECIDED_CP
    )


# The pooled subject a section uses when it needs a denominator big enough to
# clear the confidence gate at all (L-022).
POOLED_SUBJECT = "any"


def drop_redundant_aggregates(findings: tuple[Finding, ...]) -> tuple[Finding, ...]:
    """Keep the specific claim when both it and its pooled parent survive.

    A section carrying an aggregate plus subdivisions can assert both for one
    player, and "you go wrong early" next to "you go wrong early as Black" has
    said one thing twice. The arbiter prefers diversity **across** claim kinds
    and cannot see inside one.

    The specific claim wins because it is strictly more useful: it names the
    same problem and says where to look. Measured in E08 on real players --
    2 of 16 advised players were getting the pair.
    """
    subdivided = {
        f.claim.kind for f in findings if f.claim.subject != POOLED_SUBJECT
    }
    return tuple(
        f
        for f in findings
        if not (f.claim.subject == POOLED_SUBJECT and f.claim.kind in subdivided)
    )



def worth_citing(
    examples: Iterable[Observation], size: int, seed: str
) -> tuple[Observation, ...]:
    """Which instances to show, preferring ones that cost the player something.

    The author rejected rows across **four** detectors for one reason, and 37 of
    163 cited rows on the sheet cost **0.0 wp**:

    > *"this exact move did not had any significant wp loss and should not be
    > counted"* — `late_castling`

    > *"The move didn't had any significant wp loss after all"* —
    > `miscounted_exchange`

    **It is a citation problem, not a counting one, and the counting is left
    alone.** `late_castling` and `slow_development` are habit claims measured
    over opportunities rather than over errors, so a move that cost nothing can
    honestly be an instance of the habit. What misleads is showing it as the
    evidence: a reader takes *"here is the move"* to mean *"the system says this
    move was a mistake"*, and the claim is not saying that. The measurement is
    right and the pointing was wrong.

    **Stratified, not ranked.** Costly instances are preferred, and *within*
    them the choice stays random. Ranking by cost would make every claim
    illustrate itself with its own worst moment, and a reader inferring typical
    severity from four citations would be misled -- which is what `Evidence`'s
    *"never cherry-picked"* was written against. This keeps that guarantee for
    what it was protecting and drops it for the part that was hurting.

    **A claim short of costly instances is topped up, never truncated.** Showing
    two citations because only two cost anything would make a claim look thinner
    than its evidence, and a habit claim may legitimately have none at all.
    """
    ordered = sorted(examples, key=lambda o: (o.game_id, o.ply))
    if not ordered:
        return ()

    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))

    costly = [o for o in ordered if o.loss_wp]
    free = [o for o in ordered if not o.loss_wp]

    chosen = rng.sample(costly, min(size, len(costly)))
    if len(chosen) < size and free:
        chosen += rng.sample(free, min(size - len(chosen), len(free)))
    return tuple(sorted(chosen, key=lambda o: (o.game_id, o.ply)))


def instance_moves(observations: Iterable[Observation]) -> tuple[tuple[str, int], ...]:
    """Identify a claim's instances by the moves they actually were.

    Sections measure in isolation and cannot see that they are describing the
    same mistakes from different angles. Carrying the moves lets the arbiter find
    that out by measurement rather than by a hand-written table of which claim
    contains which -- which would be invented pedagogy, and wrong the first time
    a section changed what it counts.
    """
    return tuple((o.game_id, o.ply) for o in observations)


@dataclass(frozen=True)
class SectionContext:
    """Everything a section agent is given. Read-only.

    `band`, `time_control` and `peers` are optional because a reference
    population may not exist yet. An agent that needs one to speak honestly must
    stay silent without it rather than fall back to a weaker comparison.
    """

    observations: tuple[Observation, ...]
    corpus: Corpus
    provenance: Provenance
    band: str | None = None
    time_control: str | None = None
    peers: PeerReference | None = None

    def player_observations(self) -> tuple[Observation, ...]:
        """Only the moves the player made. Their opponents' errors are not theirs."""
        username = self.corpus.username.lower()
        return tuple(o for o in self.observations if o.mover.lower() == username)

    def _strata(self) -> tuple[tuple[str, float], ...]:
        """The speeds to compare against, and how much each counts.

        The player's own mix where their games say what it is, and the stated
        time control otherwise -- which is every hand-built fixture, and the
        behaviour before speeds were pooled.
        """
        if self.corpus.speed_mix:
            return self.corpus.speed_mix
        return ((self.time_control, 1.0),) if self.time_control else ()

    def _mixed(self, lookup) -> float | None:
        """Combine a per-speed population figure over this player's speed mix.

        Direct standardisation. Pooling a blitz-heavy player's games into one
        rate and comparing it against a rapid population would measure the clock
        rather than the player (E01); rebuilding the baseline for **the mix they
        actually play** compares like with like while still using every game.

        Speeds the population has never played are skipped and their weight
        redistributed, so one unfamiliar game does not silence a claim.
        """
        if self.peers is None or self.band is None:
            return None

        total = 0.0
        weighted = 0.0
        for speed, share in self._strata():
            value = lookup(speed)
            if value is None:
                continue
            weighted += share * value
            total += share
        return weighted / total if total else None

    def peer_rate(self, claim_key: str) -> float | None:
        """Population rate for a claim, with this player left out of it.

        **None for a claim players do not differ on.** A peer rate exists for
        every claim the reference covers, but comparing against it only says
        something when the underlying rates actually vary between players; where
        they do not, the player's position in the ranking is sampling noise
        (E83). Returning None here removes the comparison at its single source
        -- every consumer already handles a missing peer rate by falling back to
        cost and the player's own baseline.
        """
        if not separates(claim_key):
            return None

        def at(speed: str) -> float | None:
            stats = self.peers.lookup(
                self.band, speed, claim_key, excluding=self.corpus.username
            )
            return stats.rate if stats else None

        return self._mixed(at)

    def peer_opportunities_per_game(self, claim_key: str) -> float | None:
        """How much of this condition a player at their level meets, per game.

        Mix-matched like every other peer figure, so a blitz-heavy player is
        compared against how often a blitz-heavy peer meets it.
        """
        return self._mixed(
            lambda speed: self.peers.opportunities_per_game(
                self.band, speed, claim_key, excluding=self.corpus.username
            )
        )

    def peer_cost_per_game(self, claim_key: str) -> float | None:
        """What this claim costs the population per game, this player excluded.

        The other half of the peer comparison: knowing a claim is *costly* is
        not knowing it is costly **for this player in particular**, and ranking
        on the first named one weakness to 70 % of players (E17).
        """
        return self._mixed(
            lambda speed: self.peers.cost_per_game(
                self.band, speed, claim_key, excluding=self.corpus.username
            )
        )


@dataclass(frozen=True)
class SectionReport:
    """What an agent returns.

    `insufficient_data` is separate from an empty finding list on purpose:
    "we could not assess this" and "we assessed this and it is fine" are
    different statements, and collapsing them tells the player their endgames
    are fine when four of their games reached one.

    `sub_threshold` carries the claims that were measured and are **not unusual
    enough to assert** -- `watch` tier. They were previously discarded inside
    each agent, and the first expert review found what that costs: for one player
    the single most expensive pattern in their games, conceding undefended pieces
    at 7.3 win-probability points a game across 10 of 53 games, was measured,
    landed at 1.29x the population, failed the interval test, and vanished. The
    reviewer named it as the player's main weakness.

    They are kept rather than asserted. Nothing here is a claim that the player
    is unusual -- the gate was right to refuse that -- only that the cost is real
    and was paid. What may be done with them is the arbiter's decision.
    """

    section: str
    findings: tuple[Finding, ...] = ()
    insufficient_data: bool = False
    notes: tuple[str, ...] = ()
    sub_threshold: tuple[Finding, ...] = ()


def split_by_tier(candidates: Iterable[Finding | None]) -> tuple[tuple[Finding, ...], ...]:
    """Separate what may be asserted from what was merely measured.

    Shared so the boundary cannot drift between seven agents, each of which used
    to apply it inline by returning None.
    """
    kept = [finding for finding in candidates if finding is not None]
    assertable = tuple(
        f for f in kept if f.confidence.tier in (ConfidenceTier.FOCUS, ConfidenceTier.PRIORITY)
    )
    watched = tuple(f for f in kept if f.confidence.tier is ConfidenceTier.WATCH)
    return assertable, watched


class SectionAgent(Protocol):
    """A diagnostic agent for one section of coaching knowledge.

    Measuring and asserting are separate methods on purpose. `measure` returns
    raw rates with no judgement applied, which is what building a peer reference
    needs — every player's numbers, including the unremarkable ones. `report`
    is `measure` plus the confidence policy.
    """

    section: str

    def measure(self, context: SectionContext) -> tuple[ConditionMeasurement, ...]: ...

    def report(self, context: SectionContext) -> SectionReport: ...

    def findings(self, context: SectionContext) -> tuple[Finding, ...]: ...
