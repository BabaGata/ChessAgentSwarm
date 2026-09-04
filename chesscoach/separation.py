"""Which claims may carry a comparison between players, and which may not.

Spec: docs/notes/design.claims-that-do-not-separate.md § D1

The peer comparison asserts *"you do this more than your peers"*. That sentence
needs players to actually differ. [[experiments.e83-spread-rescreen]] tested every
shipped claim for whether players differ by more than binomial sampling noise,
and found nine asserted claims on which they do not.

`allowed_motif.fork` sits at 3.3 % across 83 players with about 248 errors each.
If every player's true rate were exactly 3.3 %, measured rates would still
scatter roughly 2-5 % by chance. Somebody lands in the top decile, is told they
are fork-prone, and is average next month. That is the unfalsifiable coaching
V8 exists to prevent.

**Nothing here retires a detector.** These claims keep firing, keep costing win
probability, and keep citing the player's own games. What this register removes
is the comparison, and the rank the baseline fallback would hand it instead.

Absence from the register means *not screened*, which is not evidence of
anything -- `separates` therefore defaults to True. Muting on absence would
silence every claim E83 never reached.
"""

from __future__ import annotations

from dataclasses import dataclass

from chesscoach.peers import PeerReference

SOURCE = "experiments.e83-spread-rescreen"


@dataclass(frozen=True)
class Separation:
    """Why one claim cannot carry a comparison, with the numbers that say so."""

    dispersion: float
    p: float
    # The smallest between-player difference the screen could have detected, as
    # the ratio of a player one SD above the mean to one at the mean. A small
    # value with dispersion near 1.0 is a positive finding of flatness; a large
    # one means the screen was blind and the verdict is "not shown".
    smallest_visible: float
    players: int
    conclusive: bool
    source: str = SOURCE


# Measured on `peers-3af3206`, 83 players, at least 10 opportunities each.
# Dispersion is 1.0 when players are interchangeable. Every entry here failed at
# p >= 0.05 against a null that band-mixing already tilts toward *finding*
# separation, so these verdicts are conservative.
DOES_NOT_SEPARATE: dict[str, Separation] = {
    "concedes_weakness.isolated.own": Separation(1.02, 0.42, 1.12, 83, conclusive=True),
    "executed_motif.discoveredAttack.own": Separation(1.04, 0.38, 1.17, 64, conclusive=True),
    "slow_development.own": Separation(1.37, 0.094, 1.17, 28, conclusive=True),
    "allowed_motif.fork.own": Separation(1.15, 0.17, 1.18, 83, conclusive=True),
    "missed_motif.trappedPiece.own": Separation(1.10, 0.28, 1.18, 62, conclusive=True),
    "missed_motif.discoveredAttack.own": Separation(1.06, 0.34, 1.19, 64, conclusive=True),
    "allows_square.rook_seventh.own": Separation(1.25, 0.061, 1.21, 83, conclusive=True),
    "missed_motif.fork.own": Separation(0.94, 0.59, 1.25, 44, conclusive=True),
    # These two failed at a width that cannot distinguish "flat" from "too rare
    # to tell". They are withheld on the same rule, and marked so the next
    # rebuild knows to look again rather than treating the verdict as settled.
    "allowed_motif.skewer.own": Separation(0.83, 0.84, 1.35, 68, conclusive=False),
    "allowed_motif.backRankMate.own": Separation(0.60, 0.93, 1.64, 23, conclusive=False),
}


def why_not(claim_key: str) -> Separation | None:
    """The evidence against comparing this claim, or None if there is none."""
    return DOES_NOT_SEPARATE.get(PeerReference.canonical(claim_key))


def separates(claim_key: str) -> bool:
    """Whether players differ on this claim by more than sampling noise.

    Keys arrive both ways: sections pass `kind.subject`, the reference stores
    `kind.subject.own`. Canonicalising through `PeerReference` is what stops
    this repeating I-10, where exactly that mismatch muted four shipped claims.
    """
    return why_not(claim_key) is None
