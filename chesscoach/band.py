"""What a player's whole rating band loses points to.

Screen: docs/notes/experiments.e25-shared-weaknesses.md

Peer-relative severity is what stops the swarm telling 70 % of players the same
thing (E17), and it has one blind spot by construction: a weakness **everyone**
at the level shares has almost no excess over peers, so it sinks below everything
and is never said -- however expensive it is. `instant_move_error` costs the
median player 22.8 points of win probability a game, the most of any claim
measured in this project, and appears in no player's plan. (16.1 until
2026-08-20, on a smaller reference and before the increment correction --
experiments.e45-increment-correction.)

E25 screened which shared claims are worth saying anyway. Nearly every claim's
rate falls with rating (median r **-0.42**), and nearly all of that is simply
better players making fewer mistakes of every kind: dividing each rate by the
player's own overall error rate takes the median to **+0.15**. Five of
twenty-seven still fall afterwards, and those are the ones this band
demonstrably learns to fix rather than grows out of.

**This is not a diagnosis and must never be presented as one.** Three rules keep
it from being the generic level-appropriate advice that R-12 and anti-pattern D2
exist to prevent:

  * it never consumes the one or two personal priorities -- nothing here becomes
    a `Finding`, so the arbiter never sees it;
  * it is phrased as a statement about a **population**, because that is what was
    measured. "Players at your level lose about 16 points a game to moves played
    in under two seconds" is supported; "you play too fast" is not;
  * only screened claims appear -- **three of thirty-two**, re-screened on the
    full-size reference (2026-08-20). Two that used to appear no longer clear the
    bar: `early_error.black` fell to -0.13 and `allowed_motif.backRankMate` to
    -0.12, both against a cutoff of -0.2. Neither reads the clock, so neither
    moved because of the increment correction that prompted the re-screen -- they
    were stale from the 2026-08-19 corpus rebuild, and nobody had re-run E25
    against it.
"""

from __future__ import annotations

from dataclasses import dataclass

from chesscoach.profile.models import BandNote
from chesscoach.sections.base import SectionContext

# The same restraint as the arbiter's two-priority cap, for the same reason: a
# list long enough to be comprehensive is short enough to be ignored.
MAX_NOTES = 3


@dataclass(frozen=True)
class _Shared:
    """One screened band-wide weakness, and the evidence that admitted it."""

    key: str
    learnable_r: float
    """Correlation of the claim's rate with rating **after** the player's overall
    error rate is divided out (E25). Negative means the stronger players in the
    band commit it less, beyond simply being stronger."""
    wording: str
    """How to name the thing in a sentence about a population. Written out rather
    than reused from `phrasing`, whose templates address the player directly."""


SHARED_WEAKNESSES: tuple[_Shared, ...] = (
    _Shared(
        key="instant_move_error.instant_moves.own",
        learnable_r=-0.40,
        wording="moves played in under two seconds",
    ),
    _Shared(
        key="early_error.white.own",
        learnable_r=-0.24,
        wording="mistakes before move 15 with White",
    ),
    _Shared(
        key="missed_motif.hangingPiece.own",
        learnable_r=-0.31,
        wording="pieces left hanging by the opponent and not taken",
    ),
)


def notes_for(context: SectionContext) -> tuple[BandNote, ...]:
    """What this player's band loses most to, from the reference population.

    The cost is looked up live rather than stored with the screen, so it follows
    the reference -- including its per-speed mix-matching, since a blitz-heavy
    player's band is a blitz-heavy band.
    """
    priced = []
    for shared in SHARED_WEAKNESSES:
        cost = context.peer_cost_per_game(shared.key)
        if cost:
            priced.append(
                BandNote(
                    claim_key=shared.key,
                    cost_per_game=round(cost, 2),
                    learnable_r=shared.learnable_r,
                    wording=shared.wording,
                )
            )

    priced.sort(key=lambda note: (-note.cost_per_game, note.claim_key))
    return tuple(priced[:MAX_NOTES])
