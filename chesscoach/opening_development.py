"""Counting a player's opening development, as claims the peer machinery accepts.

Design: docs/notes/design.opening-development-signals.md
Evidence: docs/notes/experiments.e59-strong-player-expectation.md

Three claims survived the screen, and the numbers they survived at are worth
carrying here because they govern how loudly each may speak:

| claim | standardised gap | openings | verdict |
|---|--:|--:|---|
| `slow_development` | +10.6 pp | 32/36 | headline |
| `late_castling` | +9.8 pp | 30/36 | ships beside it, r = 0.68 |
| `repeat_move` | +2.0 pp | 26/36 | **half** the strength first measured |

A fourth, pawn moves, was dropped: no within-opening effect once the opening mix
was held fixed.

**The two bases are separate claim keys, never merged.** Judged against the
strong-player norm, the claim says *you are late by this opening's standard*.
Judged against the player's own median -- the fallback for openings nobody strong
plays -- it can only say *you are later here than in your own other openings*.
Blurring them would put two kinds of evidence behind one sentence.

Games are rebuilt from the observations rather than taken from PGN: every ply
gets an observation, so grouping by game and ordering by ply reproduces the move
list exactly, and no section needs a second source of games.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import chess

from chesscoach.analysis.observations import Observation
from chesscoach.development import HOME_SQUARES, Development, measure_development
from chesscoach.book_depth import moves_per_game, own_plies_in_window
from chesscoach.development_norms import DevelopmentNorms
from chesscoach.openings import OpeningBook, _family

SLOW_DEVELOPMENT = "slow_development"
LATE_CASTLING = "late_castling"
REPEAT_MOVE = "repeat_move"
# Not "how often do you push pawns" -- E59 measured that and 1600s push as many
# as 2600s in the same opening. This is "when you push one instead of
# developing, how often does it go wrong", which is what E61's cost finding
# actually pointed at: same number of pawn moves, worse ones.
PAWN_ERROR = "pawn_error"
# "You leave known theory earlier than players at your level."
# design.detectors-name-consequences § 1a, released by the author's ruling:
# "It is coaching to tell the player that they don't know the opening".
OUT_OF_BOOK = "out_of_book"
ANY_OPENING = "any"

# The basis a claim was judged on, and part of its key so the two can never be
# pooled into one number.
BY_BOOK = "book"
BY_SELF = "own"


@dataclass(frozen=True)
class GameDevelopment:
    """One game, ready to be judged, with the moves that can be cited."""

    game_id: str
    family: str
    colour: chess.Color
    development: Development
    # How deep this game stayed in named theory. Moves inside it are not the
    # player's own choices and are never charged to them -- see `_is_theory`.
    plies_in_book: int = 0
    # The player's own observations, by ply. Carried because **V8 requires every
    # claim to cite the player's own games**, and a claim about a game needs a
    # move to point at.
    mine: tuple[Observation, ...] = ()

    def at_ply(self, ply: int | None) -> Observation | None:
        """The move that decided this claim, or the last one if it never came.

        A player who never castled is cited by their last opening move, which is
        the honest evidence: *"and here the king was still in the centre"*.
        """
        if not self.mine:
            return None
        if ply is not None:
            for observation in self.mine:
                if observation.ply == ply:
                    return observation
        return self.mine[-1]


def games_from(observations: tuple[Observation, ...], username: str):
    """Rebuild (game_id, moves, colour) from per-ply observations.

    A game is skipped when the player never moved in it, which cannot happen in
    a real corpus and does happen in fixtures.
    """
    by_game: dict[str, list[Observation]] = defaultdict(list)
    for observation in observations:
        by_game[observation.game_id].append(observation)

    for game_id, rows in sorted(by_game.items()):
        rows.sort(key=lambda o: o.ply)
        mine = [o for o in rows if o.mover.lower() == username.lower()]
        if not mine:
            continue
        colour = chess.WHITE if mine[0].mover_is_white else chess.BLACK
        try:
            moves = [chess.Move.from_uci(o.move_played) for o in rows]
        except ValueError:
            continue  # a malformed game is not a measurement
        yield game_id, moves, colour


def developments(
    observations: tuple[Observation, ...],
    username: str,
    book: OpeningBook,
) -> tuple[GameDevelopment, ...]:
    """Every game the player played, measured and named by its opening."""
    found = []
    mine_by_game: dict[str, list[Observation]] = defaultdict(list)
    for observation in observations:
        if observation.mover.lower() == username.lower():
            mine_by_game[observation.game_id].append(observation)

    for game_id, moves, colour in games_from(observations, username):
        if len(moves) < 8:
            continue
        walk = book.walk([m.uci() for m in moves])
        if walk.opening is None:
            continue
        found.append(
            GameDevelopment(
                game_id=game_id,
                family=_family(walk.opening.name),
                colour=colour,
                development=measure_development(moves, colour),
                mine=tuple(sorted(mine_by_game[game_id], key=lambda o: o.ply)),
                plies_in_book=walk.plies_in_book,
            )
        )
    return tuple(found)


@dataclass
class Tally:
    instances: int = 0
    opportunities: int = 0
    games: set[str] = None  # type: ignore[assignment]
    # One citable move per instance. **A claim with no examples is refused
    # downstream**, which is correct behaviour (V8) and is exactly why these
    # claims first reached a report saying nothing at all: right numbers,
    # nothing to point at, silence.
    examples: list[Observation] = None  # type: ignore[assignment]
    # Win probability lost on the moves this habit names, summed across the
    # opening. The arbiter's own cost model, so it is comparable with every
    # other claim rather than a second currency.
    cost_wp: float = 0.0

    def __post_init__(self) -> None:
        if self.games is None:
            self.games = set()
        if self.examples is None:
            self.examples = []

    def add(self, hit: bool, game_id: str, example: Observation | None = None) -> None:
        self.opportunities += 1
        if hit:
            self.instances += 1
            self.games.add(game_id)
            if example is not None:
                self.examples.append(example)


def engine_wanted_development(observation: Observation) -> bool:
    """Did the engine want a piece developed, or the king castled, right here?

    **The condition that makes the claim's NAME true**, added after reading the
    positions rather than the counts. Across the review corpus the engine wanted
    another *pawn* move on 40 % of the moves `pawn_error` charged, 28 % of
    `repeat_move`'s and 31 % of the castling claim's -- and wanted castling on
    only 26 % of the moves the castling claim was built from.

    Those instances are real errors. They are simply not errors *of this habit*:
    "you pushed the wrong pawn" is not "you pushed a pawn instead of
    developing", and a plan built on the second would send the player to fix the
    wrong thing. The statistics were sound and the sentence they would produce
    was not, which no count could have revealed.

    Deliberately broader than "the engine wanted exactly this": a plan to castle
    is a slow preference, and the engine rarely insists on it at one specific
    ply. Wanting *development or castling* is the habit's own claim.
    """
    if not observation.best_move:
        return False
    board = chess.Board(observation.fen_before)
    try:
        move = chess.Move.from_uci(observation.best_move)
    except ValueError:
        return False
    if board.is_castling(move):
        return True
    piece = board.piece_at(move.from_square)
    if piece is None or piece.piece_type not in (chess.KNIGHT, chess.BISHOP):
        return False
    # **From its home square.** A bishop already on b4 playing Bxc3 moves a
    # minor without developing one, and counting it would let the claim say
    # "you should have developed" about a capture. Found by reading the first
    # sampled position, after the counts had already been believed once.
    return move.from_square in HOME_SQUARES[piece.color]


def _is_theory(game: GameDevelopment, ply: int) -> bool:
    """Was this move still inside named theory?

    The author, on gambits:

    > *"For gambits, signature gambit move that looses cost should not be counted
    > with the rest since giving a pawn or 2 for a quick development is a nature
    > of the gambits."*

    Exactly right, and the general form is broader than gambits: **a move the
    book still names is not the player's mistake.** The engine at depth 15
    dislikes the King's Gambit and the Englund, and charging their signature
    move to the player would penalise them for playing their opening correctly
    -- and would do it hardest to the players who actually know a line.

    The same guard covers sharp sidelines the engine underrates at this depth,
    which is the same error wearing different clothes.
    """
    return ply <= game.plies_in_book


def habit_costs(game: GameDevelopment) -> dict[str, float]:
    """What each habit cost in this game, in win probability.

    The author's method, and their reason for it:

    > *"In the games of weaker players they don't have to eventually end opening
    > worse because their opponent also plays badly."*

    Two weak players' errors cancel, so where the opening ENDS says nothing about
    how it was played. Summing what the habit's own moves lost never touches the
    opponent.

    **The three overlap** -- a pawn move while a minor is home and castling is
    available is an instance of two of them -- so the headline takes the
    **union** of the flags. Adding them would count the same lost move twice and
    inflate the claim that competes for the plan slot.
    """
    by_ply = {o.ply: o for o in game.mine}
    castle = repeat = union = pawn = 0.0
    for window_move in game.development.window_moves:
        observation = by_ply.get(window_move.ply)
        if observation is None or _is_theory(game, window_move.ply):
            continue
        if not engine_wanted_development(observation):
            continue
        loss = observation.loss_wp
        if window_move.pawn_instead_of_developing:
            pawn += loss
        if window_move.declined_available_castle:
            castle += loss
        if window_move.repeat_instead_of_developing:
            repeat += loss
        if (window_move.declined_available_castle
                or window_move.repeat_instead_of_developing
                or window_move.pawn_instead_of_developing):
            union += loss
    return {LATE_CASTLING: castle, REPEAT_MOVE: repeat,
            SLOW_DEVELOPMENT: union, PAWN_ERROR: pawn}


def count(
    observations: tuple[Observation, ...],
    username: str,
    book: OpeningBook,
    norms: DevelopmentNorms,
) -> dict[str, Tally]:
    """Tally the three development claims, both bases kept apart.

    Two passes, and the order matters. The player's **own** median is taken from
    their games in openings that DO have a strong-player norm -- their
    established habit. Taking it from every game including the unusual ones would
    let a single strange opening set the baseline it is then judged against.
    """
    played = developments(observations, username, book)
    tallies: dict[str, Tally] = defaultdict(Tally)

    covered, uncovered = [], []
    for game in played:
        verdict = norms.judge(game.family, game.colour, game.development)
        if verdict.basis == "strong":
            covered.append(game)
            _record(tallies, BY_BOOK, game, verdict)
        else:
            uncovered.append(game)

    habit = [g.development for g in covered]
    for game in uncovered:
        verdict = norms.judge_against_self(habit, game.development)
        if verdict.basis == "own":
            _record(tallies, BY_SELF, game, verdict)

    # Repeat moves need no expectation: it is a rate over the player's own
    # opening moves, compared directly with peers. Every game contributes,
    # covered or not, because nothing here depends on knowing the opening.
    # "When you push a pawn instead of developing, how often does it go wrong?"
    # The denominator is those pawn moves, not every move: the question is about
    # the quality of a choice the player made, not how often they made it.
    pawns = tallies[f"{PAWN_ERROR}.any"]
    for game in played:
        by_ply = {o.ply: o for o in game.mine}
        for window_move in game.development.window_moves:
            if not window_move.pawn_instead_of_developing:
                continue
            if _is_theory(game, window_move.ply):
                continue
            observation = by_ply.get(window_move.ply)
            if observation is None:
                continue
            pawns.opportunities += 1
            if observation.is_error and engine_wanted_development(observation):
                pawns.instances += 1
                pawns.games.add(game.game_id)
                pawns.examples.append(observation)
        pawns.cost_wp += habit_costs(game)[PAWN_ERROR]

    repeats = tallies[f"{REPEAT_MOVE}.any"]
    for game in played:
        repeats.opportunities += game.development.moves_in_window
        repeats.instances += game.development.repeat_moves
        if game.development.repeat_moves:
            repeats.games.add(game.game_id)
            example = game.at_ply(game.development.ready_at)
            if example is not None:
                repeats.examples.append(example)
        repeats.cost_wp += habit_costs(game)[REPEAT_MOVE]

    # How much of the opening was played outside known theory. The walk has
    # already happened for every game above, so this costs nothing.
    #
    # **Deliberately unpriced.** Leaving theory is a state, not a mistake -- the
    # same reasoning that makes `concedes_weakness` unpriceable -- and charging
    # it the win probability lost in those plies would double-count whatever
    # `early_error` already counts there. It reaches a player by being unusual
    # for their level or not at all, which E72 gives the vocabulary for.
    # **Per opening as well as in total.** "You leave theory early" is not
    # something anyone can study; *which* opening they leave early is. The
    # family is already on the game, so the split costs nothing to compute, and
    # it is the shape `endgame_error` already uses -- split by a body of
    # knowledge a player can own or lack, which is what varies between players
    # of equal strength ([[design.better-claims]]).
    #
    # The total stays. Thirty games across eight families is four games each and
    # the confidence policy will refuse them, so the per-family claims fire only
    # where a player has a real repertoire and the total is the safety net.
    out_of_book = tallies[f"{OUT_OF_BOOK}.{ANY_OPENING}"]
    for game in played:
        white = game.colour == chess.WHITE
        by_ply = {o.ply: o for o in game.mine}
        per_family = tallies[f"{OUT_OF_BOOK}.{game.family}"] if game.family else None
        out_of_book.opportunities += moves_per_game()
        if per_family is not None:
            per_family.opportunities += moves_per_game()
        for ply in own_plies_in_window(white):
            if _is_theory(game, ply):
                continue
            out_of_book.instances += 1
            out_of_book.games.add(game.game_id)
            if per_family is not None:
                per_family.instances += 1
                per_family.games.add(game.game_id)
            # Every instance is cited, because `Measurement` refuses a claim
            # that reports more instances than it can point at -- which is how
            # this came to be counted in the player's own moves rather than the
            # game's plies.
            observation = by_ply.get(ply)
            if observation is not None:
                out_of_book.examples.append(observation)
                if per_family is not None:
                    per_family.examples.append(observation)

    return dict(tallies)


def _record(tallies: dict[str, Tally], basis: str, game: GameDevelopment, verdict) -> None:
    """Each claim cites the move that decided it, and carries what it cost."""
    costs = habit_costs(game)
    if verdict.slow_development is not None:
        tally = tallies[f"{SLOW_DEVELOPMENT}.{basis}"]
        tally.add(verdict.slow_development, game.game_id,
                  game.at_ply(game.development.ready_at))
        tally.cost_wp += costs[SLOW_DEVELOPMENT]
    if verdict.late_castling is not None:
        tally = tallies[f"{LATE_CASTLING}.{basis}"]
        tally.add(verdict.late_castling, game.game_id,
                  game.at_ply(game.development.castled_at))
        tally.cost_wp += costs[LATE_CASTLING]
