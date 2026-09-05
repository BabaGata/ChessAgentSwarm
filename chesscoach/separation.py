"""Which claims may carry a comparison between players, and which may not.

Spec: docs/notes/design.claims-that-do-not-separate.md § D1

The peer comparison asserts *"you do this more than your peers"*. That sentence
needs players to actually differ. [[experiments.e84-band-references]] tested every shipped claim for whether
players **within one rating band** differ by more than binomial sampling noise,
and found sixteen asserted claims on which they do not.

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

SOURCE = "experiments.e84-band-references"


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


# Screened **within band**, on `peers-e84`: three bands, two speeds, and the
# denominator restored after E84 reverted D2.
#
# E83 screened a pool mixing players from 720 to 2006. A pooled null over
# genuinely different rates **inflates** dispersion, and splitting the pool moved
# twelve verdicts -- every one of them from separating to flat, with no
# recoveries. Within band is the test that matches the claim: a peer lookup is
# keyed on `(band, speed, claim)`, so "more than your peers" is a statement about
# the player's own band and has to hold there.
#
# Regenerate with `python experiments/e84-band-references/register.py`. Typed by
# hand this would be opinion; generated it stays evidence.
DOES_NOT_SEPARATE: dict[str, Separation] = {
    "executed_motif.hangingPiece.own": Separation(1.29, 0.0826, 1.04, 50, conclusive=True),  # 1400-1800|blitz
    "concedes_weakness.any.own": Separation(1.07, 0.35, 1.12, 50, conclusive=True),  # 1400-1800|blitz
    "executed_motif.pin.own": Separation(1.28, 0.0885, 1.14, 50, conclusive=True),  # 1400-1800|blitz
    "concedes_weakness.isolated.own": Separation(1.08, 0.332, 1.16, 50, conclusive=True),  # 1400-1800|blitz
    "allowed_motif.capturingDefender.own": Separation(1.31, 0.0688, 1.17, 50, conclusive=True),  # 1400-1800|blitz
    "allows_square.any.own": Separation(1.10, 0.289, 1.18, 50, conclusive=True),  # 1400-1800|blitz
    "allowed_motif.pin.own": Separation(1.25, 0.113, 1.20, 50, conclusive=True),  # 1400-1800|blitz
    "concedes_weakness.backward.own": Separation(1.06, 0.353, 1.23, 50, conclusive=True),  # 1400-1800|blitz
    "allowed_motif.fork.own": Separation(1.21, 0.153, 1.25, 49, conclusive=True),  # 1400-1800|blitz
    "executed_motif.discoveredAttack.own": Separation(1.23, 0.214, 1.25, 22, conclusive=True),  # 1400-1800|rapid
    "missed_motif.trappedPiece.own": Separation(0.63, 0.915, 1.26, 24, conclusive=True),  # 1400-1800|blitz
    "executed_motif.trappedPiece.own": Separation(1.09, 0.347, 1.27, 24, conclusive=True),  # 1400-1800|blitz
    "missed_motif.hangingPiece.own": Separation(1.24, 0.125, 1.27, 50, conclusive=True),  # 1400-1800|blitz
    "allowed_motif.discoveredAttack.own": Separation(1.24, 0.125, 1.28, 49, conclusive=True),  # 1400-1800|blitz
    "missed_motif.discoveredAttack.own": Separation(1.20, 0.238, 1.29, 22, conclusive=True),  # 1400-1800|rapid
    "executed_motif.fork.own": Separation(1.47, 0.133, 1.30, 12, conclusive=True),  # 1400-1800|blitz
    "allows_square.rook_seventh.own": Separation(0.79, 0.858, 1.33, 50, conclusive=True),  # 1400-1800|blitz
    "missed_motif.fork.own": Separation(0.93, 0.513, 1.36, 12, conclusive=False),  # 1400-1800|blitz
    "sacrificed_for_attack.own_move.own": Separation(1.24, 0.123, 1.39, 50, conclusive=False),  # 1400-1800|blitz
    "allowed_motif.skewer.own": Separation(0.72, 0.893, 1.49, 38, conclusive=False),  # 1400-1800|blitz
    "allowed_motif.backRankMate.own": Separation(0.25, 0.993, 1.82, 12, conclusive=False),  # 1400-1800|blitz
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
