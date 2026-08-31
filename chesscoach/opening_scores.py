"""Which of a player's openings they score worse in than the rest.

Spec: docs/notes/design.detectors-name-consequences.md § 1b, from the author:

    "Early error should be totally reformatted as opening error, meaning player
    knowing less number of an opening moves than peers and losing more often when
    playing some opening then another. Keep track that main openings of the
    players would be played much more often then other openings by the same
    player."

**The comparison is against the player's own repertoire, never a population.**
Scoring badly in the Caro-Kann relative to 1400-1800 players says something about
the Caro-Kann; scoring badly in it relative to everything else *you* play says
something about your preparation, and only the second is a thing to work on.

**The last sentence of the spec is the hard part.** Measured on the review twelve
([[experiments.e73-opening-scores]]): a median of **2 games per opening**, a
median of **17 openings per player**, and **46 % of openings played exactly
once**. A repertoire is two or three mainstays and a long tail, and a single loss
in a one-game opening is a 0 % score that will outrank everything real.

Two rules keep the tail out, and the second is what makes the first affordable:

- an opening must have `MIN_GAMES` before it may be compared at all, and so must
  the rest of the repertoire it is compared against;
- the two Wilson intervals must not overlap.

**NOT WIRED INTO ANY SECTION, and deliberately so.** This computes what the spec
asks for and it is correct; the *claim* built on it failed its screen
([[experiments.e73-opening-scores]]). Swept over windows of 15 to 60 games,
**four of the five players it names flip in and out**: bernes is named at 20
games, not at 25, 30, 35, 40 or 45, and again at 50. A claim whose named set
changes with the window is measuring the window, and R-13 forbids writing down an
association that has not reproduced.

Kept rather than deleted, on the same reasoning as the retired `advantage_error`:
the instability may be sample size rather than the idea -- the two survivors are
contiguous over the last three windows, which is what a claim looks like just
before it settles -- and the corpora on hand top out at 60 games per player. The
test that would settle it is deeper histories, which are free to fetch. Reviving
this means running `experiments/e73-opening-scores/depth.py` at 100+ and seeing
the flipping stop.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from chesscoach.openings import _family
from chesscoach.profile.models import wilson_interval

# Calibrated in E73 rather than assumed. The design note proposed 5 and said it
# should be settled by the distribution of per-opening game counts; the
# distribution on its own argues for 3 or 4, because 5 discards 47 % of games.
# What settles it is which floor admits a finding the claim can defend. At 3 the
# rule fires on three separations that are all **0 % over 3 games** -- Wilson
# says they separate and they are exactly the long-tail noise the author's
# caveat excludes. At 5 the survivors are 29 % over 19 games and 17 % over 6.
#
# So the proposed number was right and the stated method would not have found
# it: the distribution says what a floor costs, not what it buys.
MIN_GAMES = 5


@dataclass(frozen=True)
class WeakOpening:
    """One opening a player scores worse in than the rest of their repertoire."""

    family: str
    games: int
    score: float
    rest_games: int
    rest_score: float

    @property
    def shortfall(self) -> float:
        """Score points per game given up, against the player's own baseline."""
        return self.rest_score - self.score


def score_of(game, player: str) -> float | None:
    """1, 0.5 or 0 from the player's own side; None when there is no result.

    An unfinished or abandoned game returns None rather than 0. Scoring it as a
    loss would count a game nobody lost against the player, and the openings a
    player abandons games in are not random.
    """
    white = (getattr(game, "white", "") or "").lower() == player.lower()
    black = (getattr(game, "black", "") or "").lower() == player.lower()
    if not (white or black):
        return None
    result = getattr(game, "result", None)
    if result == "1/2-1/2":
        return 0.5
    if result == "1-0":
        return 1.0 if white else 0.0
    if result == "0-1":
        return 0.0 if white else 1.0
    return None


def family_of(game, book=None) -> str | None:
    """The opening family, from the game's own name or by walking the book.

    Grouped to the family because *"Caro-Kann Defense: Advance Variation"* and
    *"...: Panov Attack"* are one opening to a player deciding what to study --
    the same rule the guide library keys on.
    """
    named = getattr(game, "opening", None)
    if named:
        return _family(named)
    if book is None:
        return None
    walk = book.walk(getattr(game, "moves", ()))
    return _family(walk.opening.name) if walk.opening else None


def _halves(scores) -> tuple[int, int]:
    """Score as whole successes out of doubled games.

    Wilson needs integers and chess scores come in halves, so the scale is
    doubled. Rounding a draw into a win or a loss instead would move a 50 %
    score by a whole game.
    """
    return int(round(sum(scores) * 2)), len(scores) * 2


def by_family(games, player: str, book=None) -> dict[str, list[float]]:
    """Every decided game's score, grouped by opening family."""
    grouped: dict[str, list[float]] = defaultdict(list)
    for game in games:
        score = score_of(game, player)
        if score is None:
            continue
        family = family_of(game, book)
        if family is None:
            continue
        grouped[family].append(score)
    return dict(grouped)


def weak_openings(
    games, player: str, book=None, min_games: int = MIN_GAMES
) -> tuple[WeakOpening, ...]:
    """Openings this player scores worse in than their own other openings.

    **Only worse.** An opening a player scores *better* in is a strength, and a
    strength reported as a finding is the mistake `s1_tactical_gaps.NOT_ASSERTED`
    names for `executed_motif`: *"it is not a weakness and must not be reported
    as one"*. It is measured here and deliberately dropped.
    """
    grouped = by_family(games, player, book)
    found: list[WeakOpening] = []

    for family, scores in grouped.items():
        if len(scores) < min_games:
            continue
        # The opening is excluded from its own baseline. Left in, it drags the
        # baseline toward itself, and a player whose worst opening is also their
        # most played could never be told about it.
        rest = [s for other, ss in grouped.items() if other != family for s in ss]
        if len(rest) < min_games:
            continue

        _, high = wilson_interval(*_halves(scores))
        low_rest, _ = wilson_interval(*_halves(rest))
        if high >= low_rest:
            continue

        found.append(WeakOpening(
            family=family,
            games=len(scores),
            score=sum(scores) / len(scores),
            rest_games=len(rest),
            rest_score=sum(rest) / len(rest),
        ))

    return tuple(sorted(found, key=lambda w: (w.score, w.family)))
