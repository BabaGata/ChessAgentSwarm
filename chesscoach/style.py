"""How a player plays, as distinct from how well.

Capability: V3 · Screen: docs/notes/experiments.e14-style-dimensions.md
Operational definition: docs/notes/domain.coaching.md § 6

That note is directive and sceptical in equal measure: style is **measured
tendencies plus measured performance, not a personality label**. E14 screened six
candidate tendencies against 84 players and applied two bars — a dimension must
vary between players, *and* be uncorrelated with rating, because a tendency that
rises with strength is strength wearing a friendlier name.

**Four of six were strength in disguise.** Captures, checks, game length and
material kept on all correlate with rating at 0.47-0.56: weaker players capture
and check more. A style profiler without that second bar would have told them
"you are an aggressive player" while measuring "you are weaker".

**One survives and is used here:** how much of a player's game is spent with the
queens off — spread 1.40, correlation with rating **-0.069**. A real preference,
independent of strength.

**And the performance half does not survive at all.** Whether the preference
*suits* them would be the useful claim; E14 measured it and found every player
errs about 20 % less with queens off, differing by a spread of 1.27. So this
module says what a player tends to do and refuses to say whether it is working
for them, because nothing here can tell.
"""

from __future__ import annotations

from dataclasses import dataclass

import chess

from chesscoach.analysis.observations import Observation
from chesscoach.peers import ConditionMeasurement
from chesscoach.profile.models import Claim
from chesscoach.sections.base import SectionContext, SectionReport, diagnosable

SECTION = "S10"

TENDENCY = "plays_queenless"

# Below this the share is too thin to describe a preference rather than a run of
# luck in a handful of games.
MIN_MOVES = 200

# How far from the population a share must sit before it is worth mentioning at
# all. Lower than the confidence policy's margin because this is not a claim
# about a weakness -- nothing is being prescribed, so the cost of mentioning a
# mild preference is a sentence rather than a wasted training block.
NOTABLE_RATIO = 1.2


@dataclass(frozen=True)
class Tendency:
    """One measured way this player differs, with no judgement attached."""

    name: str
    share: float
    peer_share: float
    moves: int

    @property
    def ratio(self) -> float:
        return self.share / self.peer_share if self.peer_share else 1.0

    @property
    def notable(self) -> bool:
        return self.ratio >= NOTABLE_RATIO or self.ratio <= 1 / NOTABLE_RATIO

    @property
    def direction(self) -> str:
        return "more" if self.ratio > 1 else "less"


def queens_off(fen: str) -> bool:
    board = chess.Board(fen)
    return not board.pieces(chess.QUEEN, chess.WHITE) and not board.pieces(
        chess.QUEEN, chess.BLACK
    )


class S10StyleTendencies:
    """Measures how a player plays. **Never emits a finding.**

    A tendency is not a weakness, and routing it through the findings machinery
    would put it in front of the arbiter competing for one of a player's two
    priorities — which is exactly the wrong shape for "this is how you play".
    The measurements still go into the peer reference, because a tendency means
    nothing without a population to be unusual against.
    """

    section = SECTION

    def measure(self, context: SectionContext) -> tuple[ConditionMeasurement, ...]:
        moves = diagnosable(context.player_observations())
        if not moves:
            return ()
        return (
            ConditionMeasurement(
                claim_key=_key(),
                instances=sum(1 for o in moves if queens_off(o.fen_before)),
                opportunities=len(moves),
                distinct_games=len({o.game_id for o in moves}),
                games_with_data=len({o.game_id for o in moves}),
            ),
        )

    def report(self, context: SectionContext) -> SectionReport:
        return SectionReport(section=SECTION)

    def findings(self, context: SectionContext) -> tuple:
        return ()


def _key() -> str:
    return Claim.of(kind=TENDENCY, subject="any").key()


def describe(
    observations: tuple[Observation, ...],
    username: str,
    peers,
    band: str,
    time_control: str,
    speed_mix: tuple[tuple[str, float], ...] = (),
) -> Tendency | None:
    """The player's tendency against the population, or None if unmeasurable.

    `speed_mix` is the share of the player's games at each speed. Supplying it
    rebuilds the comparison for the speeds they actually play, exactly as
    `SectionContext` does for findings.

    Found by running a live session: a player whose recent games were **entirely
    blitz** had their queenless share compared against the *rapid* population,
    because this function looked up one stated time control rather than the mix.
    Style does not go through `SectionContext`, so step 5 fixed the findings and
    left this behind.
    """
    mine = diagnosable(
        tuple(o for o in observations if o.mover.lower() == username.lower())
    )
    if len(mine) < MIN_MOVES or peers is None:
        return None

    peer_share = _population_share(peers, band, time_control, speed_mix, username)
    if not peer_share:
        return None

    return Tendency(
        name=TENDENCY,
        share=sum(1 for o in mine if queens_off(o.fen_before)) / len(mine),
        peer_share=peer_share,
        moves=len(mine),
    )


def _population_share(peers, band: str, time_control: str, speed_mix, username: str):
    """The population's share, weighted over the speeds this player plays.

    Speeds the population has never played are skipped and their weight
    redistributed, so one unfamiliar game does not silence the tendency.
    """
    strata = speed_mix or ((time_control, 1.0),)

    weighted = 0.0
    total = 0.0
    for speed, share in strata:
        stats = peers.lookup(band, speed, _key(), excluding=username)
        if stats is None or not stats.rate:
            continue
        weighted += share * stats.rate
        total += share
    return weighted / total if total else None
