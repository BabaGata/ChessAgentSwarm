"""Which replies count as punishing a mistake, and which one gets named.

Design: docs/notes/design.punishment-validity.md — Option 3 + severity ordering

`allowed_motif` used to fire only when the opponent's **single best** reply
executed the motif. That is too strict in one direction and, in the form that
replaced it, too loose in the other:

- a fork that is excellent but second-best was missed, as was a fork that is
  merely good when mate was also on the board;
- counting *availability* alone would have counted forks that lose for the
  opponent, which the player is not at fault for allowing.

The middle idea is **not best, good enough**, which is the ε-optimal action set
of decision theory and Simon's aspiration level under two other names — see the
design note for the sources. A reply is a punishment when

1. **it executes the motif** — and the detectors only report a motif that wins
   material, so *"it actually punishes"* is already enforced statically, for
   free, by `tactics` and `material`. Nothing here re-checks it.
2. **it was worth playing** — within `INACCURACY_WP` of the opponent's best.
   The threshold is *reused, not chosen*: a punishment counts if playing it
   would not itself have been an inaccuracy, by the same standard this project
   uses to judge the player. One constant, one owner.

**A second condition was designed and dropped**, because it could not fire. It
asked that a punishment gain at least δ over the position *as it stands* — but a
position's evaluation already assumes best play, so `wp(stand)` and `wp(best)`
are the same number. Measured over 800 positions: median gap **8 cp**, against
**264 cp** for an arbitrary other move. The condition would have required a
candidate to beat the best move, which nothing can do.

## Severity

When several punishments qualify, the one that gets **named** is the one reaching
the highest win probability; the rest are still recorded. Mate wins
automatically, because mate *is* the maximum — so *"checkmate should be
prioritised"* falls out of arithmetic rather than out of a table of which motif
outranks which. **No chess judgement is encoded here, so none needs a source**
(R-03).

This also settles where the **cost** goes. One blunder can leave a fork, a pin
and a skewer all available; charging its win-probability loss to each would
treble it, and the arbiter ranks on cost. One mistake pays once, to the
punishment that gets named.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import chess

from chesscoach.analysis.labels import INACCURACY_WP
from chesscoach.tactics import detect_motifs

# How far below the best reply a punishment may sit and still count. Reused from
# the error threshold rather than chosen: see the module docstring.
WORTH_PLAYING_WP = INACCURACY_WP


@dataclass(frozen=True)
class Candidate:
    """One reply that executes a motif, with the win probability it reaches.

    `wp` is from the **replying side's** point of view — the opponent of the
    player being coached — so higher is worse for the player.
    """

    motif: str
    uci: str
    wp: float


@dataclass(frozen=True)
class Punishment:
    """A candidate that was worth playing, and by how much it trailed the best."""

    motif: str
    uci: str
    wp: float
    # Win probability given up against the opponent's best reply. Zero when this
    # *is* the best reply. Kept so a report can say how close it was.
    behind_best_wp: float


def qualifying(
    candidates: tuple[Candidate, ...], best_wp: float, threshold: float = WORTH_PLAYING_WP
) -> tuple[Punishment, ...]:
    """The candidates worth playing, in the order given.

    An empty input answers empty rather than passing — the failure mode this
    codebase keeps meeting (L-046).
    """
    punishments = []
    for candidate in candidates:
        behind = best_wp - candidate.wp
        if behind <= threshold:
            punishments.append(
                Punishment(
                    motif=candidate.motif,
                    uci=candidate.uci,
                    wp=candidate.wp,
                    behind_best_wp=max(0.0, behind),
                )
            )
    return tuple(punishments)


def primary(punishments: tuple[Punishment, ...]) -> Punishment | None:
    """The one to name: highest win probability, ties broken deterministically.

    Determinism matters at runtime, not only in tests — the same games must
    produce the same report, and two punishments reaching the same evaluation is
    ordinary rather than exotic.
    """
    if not punishments:
        return None
    return max(punishments, key=lambda p: (p.wp, p.motif, p.uci))


def candidates_in(
    board: chess.Board,
    evaluate: Callable[[chess.Board], float],
    best: chess.Move | None = None,
    best_wp: float | None = None,
) -> tuple[Candidate, ...]:
    """Every legal reply that executes a motif, with the win probability it reaches.

    `evaluate` returns the **replying side's** win probability for a position, so
    this module needs no engine and no analyser type of its own.

    Three things keep the engine bill down, and E85 measured all three:

    1. **Only moves executing a motif are evaluated.** `detect_motifs` removes
       93 % of replies for free, because a move reaches it only by passing the
       material checks in `tactics` and `material`.
    2. **The best reply is never evaluated.** Its win probability is the
       position's own, which the caller already has.
    3. **A move whose motifs the best reply already executes is skipped.** If the
       best reply forks, a second forking move cannot add a motif, cannot beat it
       on win probability -- nothing exceeds the best -- and so cannot change
       either the instances or which punishment is named.

    Without 2 and 3 this evaluated about 3.5 positions per error against the 1.52
    E85 predicted; the gap was the free ones being paid for.
    """
    covered: frozenset[str] = frozenset()
    found: list[Candidate] = []

    if best is not None and best_wp is not None and best in board.legal_moves:
        covered = frozenset(sorted(str(m) for m in detect_motifs(board, best)))
        for motif in sorted(covered):
            found.append(Candidate(motif=motif, uci=best.uci(), wp=best_wp))

    for move in board.legal_moves:
        if move == best:
            continue
        motifs = frozenset(sorted(str(m) for m in detect_motifs(board, move)))
        if not motifs or motifs <= covered:
            continue
        after = board.copy(stack=False)
        after.push(move)
        wp = evaluate(after)
        for motif in sorted(motifs):
            found.append(Candidate(motif=motif, uci=move.uci(), wp=wp))
    return tuple(found)
