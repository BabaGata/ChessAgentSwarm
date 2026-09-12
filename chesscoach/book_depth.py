"""How much of a player's opening is played outside known theory.

Spec: docs/notes/design.detectors-name-consequences.md § 1a
Calibration: docs/notes/experiments.e76-leaving-theory.md

1a was held for a long time and then released by a chess ruling from the author,
asked whether a difference of a move and a half was worth telling anyone:

    "It is coaching to tell the player that they don't know the opening"

**The measure is a share, not a threshold.** "Did they leave theory before move
N" and "how much of the opening was outside theory" were both measured. The
threshold version is worse at every setting it was tried: its best split-half
reliability is **+0.65**, against **+0.83** for this one, because thresholding
discards how far out of theory the game went and keeps only whether it was.

Being a rate, it needs nothing new from the confidence policy: instances are
plies out of book, opportunities are games times the cap.

**Every game counts, not only the ones the player left first.** `BookWalk`
records `left_by_white` so that a player is not charged for an *opponent's*
sideline, and that concern was tested rather than assumed: restricting to the
player's own exits gives the **same** gap between strong players and peers (-24 %
against -23 %) at **+0.64** reliability instead of +0.83, because it halves the
games per player. The chess argument for counting every game -- that a player
prepared in an opening knows the answers to sidelines too -- is the author's to
confirm; the measurement says the choice costs nothing either way.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_NORMS = (Path(__file__).resolve().parent.parent
                 / "data" / "openings" / "book-depth-norms.json")

# The window the claim is about, in half-moves: the first five moves each side.
# Swept from 8 to 30 in E76. The gap between strong players and peers is widest
# here (-23 %) and reliability is at its maximum (+0.83); both fall away as the
# window widens, because a longer window is mostly middlegame and everybody is
# out of book by then.
EARLY_PLIES = 10


def own_plies_in_window(player_is_white: bool) -> tuple[int, ...]:
    """The plies inside the window that belong to this player.

    **One-based, because the rest of the project is**: `Observation.ply` is
    `index + 1` and `_is_theory` reads `ply <= plies_in_book`. A first version
    numbered from zero and the only symptom was silence -- the claim counted 52
    instances, found 0 of them in `{o.ply: o for o in game.mine}`, and was
    correctly refused for having no evidence. The refusal was right and it hid
    the cause, which is worth remembering about guards that fire early.

    So White moves on plies 1, 3, 5 ... and Black on 2, 4, 6 ...
    """
    start = 1 if player_is_white else 2
    return tuple(range(start, EARLY_PLIES + 1, 2))


def out_of_book_moves(walk, player_is_white: bool) -> int:
    """How many of the player's **own** early moves were outside theory.

    Counted as the player's moves rather than the game's plies, and that is not
    cosmetic. `Measurement` requires a claim to locate **every** instance it
    reports or none of them, and the only instances that can be located are moves
    the player made -- a game-level count of 105 with 19 citable moves is refused
    outright, which is how this definition was arrived at.

    A game deeper in book than the cap costs nothing: the question is the
    opening, and the cap is where this measure says the opening ends.
    """
    # `> plies_in_book`, matching `opening_development._is_theory`, which reads
    # `ply <= plies_in_book`. Two definitions of "still in theory" in one
    # codebase would be one too many.
    return sum(1 for ply in own_plies_in_window(player_is_white)
               if ply > walk.plies_in_book)


def moves_per_game() -> int:
    """The player's own moves inside the window: the per-game denominator."""
    return EARLY_PLIES // 2


def out_of_book_share(walks_and_colours) -> float | None:
    """Share of a player's own early moves played outside theory, or None.

    Takes `(walk, player_is_white)` pairs.

    **None for no games, never 0.0.** Zero is the score of a player who never
    leaves theory, and returning it for a player with no games is the empty case
    answering exactly like the best possible one (L-046).
    """
    pairs = list(walks_and_colours)
    if not pairs:
        return None
    out = sum(out_of_book_moves(walk, white) for walk, white in pairs)
    return out / (len(pairs) * moves_per_game())


@dataclass(frozen=True)
class BookDepthNorms:
    """What a population plays outside theory, per band and speed.

    Kept in its own file rather than in the peer reference because **book depth
    needs no engine**. Putting it in the reference would make a baseline that
    costs seconds depend on a pass that costs an hour. The development norms set
    the same precedent for the same reason.
    """

    shares: dict[str, float] = field(default_factory=dict)
    source: str = ""
    players: int = 0
    games: int = 0

    @staticmethod
    def key(band: str, time_control: str, family: str = "") -> str:
        base = f"{band}|{time_control}"
        return f"{base}|{family}" if family else base

    def share_for(
        self, band: str, time_control: str, family: str = ""
    ) -> float | None:
        """The population's share, or None where it was never measured.

        None rather than a default: a player compared against an invented
        baseline is judged against a number nobody measured, and a **blitz**
        player compared against a *rapid* baseline is I-03 over again.

        **`family` is not optional detail -- it is half of what the claim says.**
        `out_of_book.Hungarian Opening` reads *"you leave known theory sooner
        than players at your level **when you play the Hungarian Opening**"*,
        and the baseline was keyed on band and speed alone, so the second half
        of that sentence was not in the comparison. The book is not equally deep
        everywhere: measured over the rapid corpus, the share of the first ten
        plies outside theory runs from **22.4 % in the Italian Game to 79.5 % in
        the Van't Kruijs Opening** -- a 57-point spread against one pooled
        number of 43.5 %. Play the Italian and the claim can never fire; play
        1.g3 and it always does. That measures *which opening you play*, which
        is not a weakness, rather than *how well you know it*, which is.

        **A family the population has not played falls back to the pooled
        share** rather than to None. Silence would be worse: a rare opening is
        exactly where a player is most likely to be out of theory for real, and
        the pooled number is a measured number -- just a blunter one. The
        fallback is recorded here so a reader knows the comparison got coarser
        rather than assuming it got sharper.
        """
        if family:
            per_family = self.shares.get(self.key(band, time_control, family))
            if per_family is not None:
                return per_family
        return self.shares.get(self.key(band, time_control))

    def save(self, path: Path | str = DEFAULT_NORMS) -> None:
        payload = {
            "source": self.source,
            "players": self.players,
            "games": self.games,
            "early_plies": EARLY_PLIES,
            "note": ("share of the first ten half-moves played outside the CC0 "
                     "opening book, averaged over a population's games"),
            "shares": self.shares,
        }
        Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                              encoding="utf-8")

    @classmethod
    def load(cls, path: Path | str = DEFAULT_NORMS) -> BookDepthNorms:
        """Read the norms, or raise. A missing file is the caller's problem.

        Returning an empty object would silence every claim without saying so,
        and a silent claim is indistinguishable from a player with nothing wrong.
        """
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            shares={str(k): float(v) for k, v in raw.get("shares", {}).items()},
            source=str(raw.get("source", "")),
            players=int(raw.get("players", 0)),
            games=int(raw.get("games", 0)),
        )
