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
from chesscoach.tactics import detect_motifs

SLOW_DEVELOPMENT = "slow_development"
LATE_CASTLING = "late_castling"
REPEAT_MOVE = "repeat_move"
# Not "how often do you push pawns" -- E59 measured that and 1600s push as many
# as 2600s in the same opening. This is "when you push one instead of
# developing, how often does it go wrong", which is what E61's cost finding
# actually pointed at: same number of pawn moves, worse ones.
OPENING_PAWN_ERROR = "opening_pawn_error"

# The subject holding this claim's comparison arm. Never asserted -- S4 reads it
# as a baseline and `_is_comparison_arm` keeps it out of the candidate list.
OTHER_OPENING_MOVES = "__other_opening_moves"
# "You leave known theory earlier than players at your level."
# design.detectors-name-consequences § 1a, released by the author's ruling:
# "It is coaching to tell the player that they don't know the opening".
OUT_OF_BOOK = "out_of_book"
ANY_OPENING = "any"

# **`out_of_book.any` is not asserted.** It scored **0 of 3** on the author's
# marked sheet -- the worst result of the round and the only detector to score
# nothing -- and they asked for the claim to be replaced rather than repaired:
#
# > *"This out of book any is not so informative, there should be concrete
# > opening detected."*
#
# The reading behind that is right. Pooling every opening into one rate says
# *"you leave theory early"* about a player who may know one repertoire well and
# have no theory at all in another, and there is nothing to do about the pooled
# number. The per-family claims -- `out_of_book.Sicilian Defense` and the rest --
# name a body of knowledge a player can go and learn, which is what
# [[design.better-claims]] asks a claim to do.
#
# **A thin repertoire now produces no claim, and that is the honest answer.**
# The confidence policy already refuses a family with too few games, so the
# pooled claim was acting as a safety net that fired *because* it pooled. A
# player who plays eight different openings twice each has not shown a pattern
# and should be told nothing.
#
# **Neither of the two causes underneath is fixed by this**, and both are still
# live: the book is thin on offbeat lines (*"this is a variant of the
# accelerated london system"*), and the deviation is recorded one ply late when
# the book holds an opponent's odd move but not the natural reply, which moves
# the blame across the board (*"out of book was white in the move 3"*).
# `left_book_themselves` catches the clean half of that and not this half.
#
# The tally stays and is still counted, on the same reasoning as
# `s4_opening_outcomes.EARLY_ERROR_RETIRED`: it is a cheap way to ask later
# whether the per-family claims cover the games the pooled one used to.
OUT_OF_BOOK_ANY_RETIRED = True

# The basis a claim was judged on, and part of its key so the two can never be
# pooled into one number.
BY_BOOK = "book"
BY_SELF = "own"

# How far a **citation** may reach when the deciding move never happened.
#
# `at_ply` used `EARLY_PLIES` for this, which E76 calibrated for `out_of_book`
# and which ends at **move 5 for both colours**. So every fallback citation was
# move 5, whatever the claim -- and `late_castling` and `slow_development` are
# about moves 10 to 22. All five of the author's rejections on those two claims
# were this one line:
#
# > *"this exact move did not had any significant wp loss and should not be
# > counted"*
#
# > *"There were some unnecessary movements of the pawns instead of developing
# > pieces and allowing the king to castle but d5 was not one of them"*
#
# Right about the move, which was never the move the claim rested on. Thirty
# plies is move 15, the same figure `s4_opening_outcomes.OPENING_END_PLY` uses
# for the end of the opening, and it is a **bound on the citation only** -- no
# claim is measured over it. The bound exists at all because the fallback once
# reached the end of the game and cited `Rf7#` on move 36 as evidence of slow
# development.
CITABLE_OPENING_PLIES = 30


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
    # The ply that left the book, and whose it was. **Once any move leaves the
    # tree no later position is in it**, so after an opponent's deviation the
    # player is out of theory by construction rather than by choice.
    left_at_ply: int | None = None
    # The player's own observations, by ply. Carried because **V8 requires every
    # claim to cite the player's own games**, and a claim about a game needs a
    # move to point at.
    mine: tuple[Observation, ...] = ()

    def at_ply(self, ply: int | None) -> Observation | None:
        """The move that decided this claim, or the last one if it never came.

        A player who never castled is cited by their last opening move, which is
        the honest evidence: *"and here the king was still in the centre"*.

        **The last opening move, not the last move of the game.** `mine` holds
        every move the player made, so this fell through to whatever they played
        last -- and the author caught it citing `Rf7#`, checkmate on move 36, as
        evidence of slow development:

        > *"The rook was developed before ... Rooks usually are moved from the
        > first/last rank in the late middle game or endgame."*

        Their reading of the cause was a different one; the mechanism is that
        `ready_at` is None whenever the player never castled, so the claim fell
        straight through to the end of the game. A move thirty plies past the
        opening cannot be evidence about the opening, and citing mate as a
        development failure is the kind of thing that makes a whole report
        untrustworthy.
        """
        if not self.mine:
            return None
        if ply is not None:
            for observation in self.mine:
                if observation.ply == ply:
                    return observation

        # The end of the **opening**, not the end of the out-of-book window --
        # see `CITABLE_OPENING_PLIES`. Where the game says when its own opening
        # finished, that is better still: it is this player's opening rather
        # than a constant.
        until = self.development.phase_over_at or CITABLE_OPENING_PLIES
        inside = [o for o in self.mine if o.ply <= until]
        return inside[-1] if inside else self.mine[0]


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
                left_at_ply=walk.left_at_ply,
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
    another *pawn* move on 40 % of the moves `opening_pawn_error` charged, 28 % of
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
            SLOW_DEVELOPMENT: union, OPENING_PAWN_ERROR: pawn}


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
    # The comparison arm, and the reason this claim survives without peers.
    #
    # The author kept the claim after the register withdrew its peer comparison:
    #
    # > *"opening_pawn_error should stay and it gives good information for
    # > players that push pawns unnecessarily instead of developing, if it
    # > doesn't reach players it doesn't mean that some other players this
    # > wouldn't reach."*
    #
    # They are right that 0 of 12 is a fact about twelve players, not about the
    # claim -- but S4 returns None without a baseline, so the claim was not
    # merely unreached, it was **unreachable**. This is the within-player
    # baseline S4's own comment said did not exist for these claims, and for this
    # one it does: *how often a pawn push instead of developing goes wrong,
    # against how often the player's other opening moves do.* Both arms come from
    # the same observations, so it needs no engine and no peer reference.
    others = tallies[f"{OPENING_PAWN_ERROR}.{OTHER_OPENING_MOVES}"]
    pawns = tallies[f"{OPENING_PAWN_ERROR}.any"]
    for game in played:
        by_ply = {o.ply: o for o in game.mine}
        for window_move in game.development.window_moves:
            if _is_theory(game, window_move.ply):
                continue
            if not window_move.pawn_instead_of_developing:
                # The other arm: everything else the player did in the window,
                # on the same terms -- out of book, and not a move some motif
                # already explains.
                other = by_ply.get(window_move.ply)
                if other is not None and not _explained_by_a_motif(other):
                    others.opportunities += 1
                    others.instances += bool(other.is_error)
                continue
            observation = by_ply.get(window_move.ply)
            if observation is None:
                continue
            # An error a motif detector already names is charged to that motif.
            # The author's rule, and the same one `drift_before` follows:
            #
            # > *"they shouldnt be counted when the issue is missing some motif
            # > that was triggered by other detector"*
            #
            # "You pushed a pawn instead of developing" and "you missed a fork"
            # are different lessons, and a plan built on the first when the
            # second is true sends the player to fix the wrong thing.
            if _explained_by_a_motif(observation):
                continue
            pawns.opportunities += 1
            if observation.is_error and engine_wanted_development(observation):
                pawns.instances += 1
                pawns.games.add(game.game_id)
                pawns.examples.append(observation)
        pawns.cost_wp += habit_costs(game)[OPENING_PAWN_ERROR]

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
        if not left_book_themselves(game):
            # Not an opportunity either: the player was never in a position to
            # stay in theory, so counting the game and scoring zero would dilute
            # the rate rather than measure it.
            continue
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


# "Repeated bad moves" is the author's bar for when castling late is a fault at
# all, and repeated is at least two. Named rather than buried so moving it is
# visible; [[design.castling-under-drift]] records that two is a reading of their
# words and not a calibrated number.
DRIFT_MOVES = 2


def drift_before_castling(game: GameDevelopment) -> tuple[int, float]:
    """Unexplained errors between leaving book and castling."""
    return drift_before(game, game.development.castled_at)


# One is enough: the author's two rejections measured **zero** against three,
# five and seven for the three they accepted, so nothing here is fitted to a
# boundary.
WANTED_DEVELOPMENT_MOVES = 1


def declined_development(game: GameDevelopment) -> int:
    """Window moves before the pieces were out where the engine wanted them out.

    The author asked for *"similar check for the slow development as it is for
    late casteling"*, and gave the reason:

    > *"There are detected some slow development moves that are product of the
    > other moves like out of the book incorrect move, forced exchanges and
    > defenses and other moves that were better in those positions than the
    > development moves."*

    **The drift test was tried first and does not separate their marks** -- one
    accepted game has zero drift and both rejected ones have one, so no threshold
    works. Their reason is not drift: *"There was not really a possibility to
    develop this bishop before without loosing material or advantage."* That is
    development not being what the position wanted, and
    `engine_wanted_development` already answers it -- it gates the habit costs and
    `opening_pawn_error` and was simply never applied to this claim's instances.

    On the five marked games it separates cleanly: **0 and 0** for the two
    rejected, **3, 5 and 7** for the three accepted.
    """
    by_ply = {o.ply: o for o in game.mine}
    until = game.development.developed_at
    declined = 0
    for window_move in game.development.window_moves:
        if _is_theory(game, window_move.ply):
            continue
        # After the pieces are out, nothing says anything about why they were
        # late; a player who never got them out declined for the whole window.
        if until is not None and window_move.ply >= until:
            continue
        observation = by_ply.get(window_move.ply)
        if observation is not None and engine_wanted_development(observation):
            declined += 1
    return declined


def drift_before(game: GameDevelopment, until: int | None) -> tuple[int, float]:
    """The player's unexplained errors between leaving book and castling.

    Design: [[design.castling-under-drift]]. The author, rejecting a firing where
    White castled on move 13 and was better for it:

    > *"This should be taken in the account only when there are repeated bad
    > moves before having the opportunity to castle."*

    and on how to measure that:

    > *"count together all the imprecise moves before castling and after out of
    > the book move ... only errors that have not been detected by some motif
    > detector."*

    Three boundaries, each with a reason:

    * **after the book move** -- moves inside named theory are not the player's
      own choices, the line `plies_in_book` already draws for the other claims;
    * **before castling** -- the question is what they were doing *instead* of
      castling, so errors after the king is safe say nothing;
    * **no motif explains it** -- an error the vocabulary already names is
      charged to that motif, and charging it here too counts one mistake twice
      (`chesscoach/overlap.py`). What is left is the residue with no tactic to
      point at, which is what *"just played badly"* means.

    Returns the count and what it cost in win probability. **No engine call**:
    every observation was analysed once already.
    """
    count, cost = 0, 0.0

    for observation in game.mine:
        if observation.label is None:
            continue
        if observation.ply <= game.plies_in_book:
            continue
        # A player who never got there drifted for the whole window rather than
        # for none of it -- reading "no ply" as an empty window would excuse
        # exactly the games where the king never reached safety, or the pieces
        # never came out.
        if until is not None and observation.ply >= until:
            continue
        if _explained_by_a_motif(observation):
            continue
        count += 1
        cost += observation.loss_wp
    return count, cost


def _explained_by_a_motif(observation: Observation) -> bool:
    """Does a named tactic already account for this error?

    Two sides, because the vocabulary has two: a **punishment** the opponent
    could have played (`allowed_motif`), and a motif the engine's own move would
    have executed (`missed_motif`). Either one means the mistake has a name and
    an owner, so it is not part of the residue.
    """
    if observation.punishments:
        return True
    if observation.best_move is None:
        return False
    board = chess.Board(observation.fen_before)
    try:
        best = chess.Move.from_uci(observation.best_move)
    except ValueError:
        return False
    if best not in board.legal_moves:
        return False
    return bool(detect_motifs(board, best))


def left_book_themselves(game: GameDevelopment) -> bool:
    """Was it the player who left known theory, or their opponent?

    > *"There are plenty of the opening detections that are just a product of not
    > having the proper variants in the downloaded books."*

    The author's reading, and the measurement is worse than it sounds: across the
    reviewed games the book ran out in 658 of them, and in **377 (57 %) the
    opponent left first** -- carrying **53 % of every instance the claim
    charged**. `1.e4 d5 2.exd5 Nf6 3.c3` is one of theirs: White plays an offbeat
    third move and *Black* is charged for the recapture, and for every move after
    it.

    A book walk stops at the first move outside the tree, so once anyone leaves
    it **no later position is in it**. After an opponent's deviation the player
    is out of theory by construction, and *"you are out of known opening theory
    sooner than players at your level"* is not a true sentence about them.

    This does not fix the coverage problem underneath -- the book is thin on
    offbeat lines and a natural recapture can still fall outside it. It removes
    the half of the claim that was never about the player at all.
    """
    if game.left_at_ply is None:
        return False
    played_by_white = game.left_at_ply % 2 == 1
    return played_by_white == (game.colour == chess.WHITE)


def _record(tallies: dict[str, Tally], basis: str, game: GameDevelopment, verdict) -> None:
    """Each claim cites the move that decided it, and carries what it cost."""
    costs = habit_costs(game)
    if verdict.slow_development is not None:
        # Late only counts as a fault if development was actually on offer and
        # declined. Same purpose as `late_castling`'s gate, different test --
        # see `declined_development` for why drift does not work here.
        slow = (verdict.slow_development
                and declined_development(game) >= WANTED_DEVELOPMENT_MOVES)
        tally = tallies[f"{SLOW_DEVELOPMENT}.{basis}"]
        tally.add(slow, game.game_id, game.at_ply(game.development.ready_at))
        tally.cost_wp += costs[SLOW_DEVELOPMENT] if slow else 0.0
    if verdict.late_castling is not None:
        # **Late is only a fault if they were drifting while they were late.**
        # Castling on move 13 having seized the initiative and castling on move
        # 13 having drifted are the same number and opposite diagnoses, and the
        # advice that follows -- castle sooner -- would have made the first
        # player's game worse.
        drifted, _ = drift_before_castling(game)
        late = verdict.late_castling and drifted >= DRIFT_MOVES
        tally = tallies[f"{LATE_CASTLING}.{basis}"]
        tally.add(late, game.game_id, game.at_ply(game.development.castled_at))
        tally.cost_wp += costs[LATE_CASTLING] if late else 0.0
