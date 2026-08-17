"""E31 — per-game agreement: what the reviewer noticed against what the swarm flagged.

The pre-registered instrument asks for a ranked top three per player. The
reviewer, twenty games into `bjagus`, did something more useful instead: wrote
down **every mistake they noticed, game by game**, with move numbers from game 8
onward. Their own reason is the strongest argument for it:

    "Comparing all noticed mistakes by the game I think should work better to get
    the overview of the system functioning while combining top 3 is just
    prioritization calculation."

That is right, and it separates two things the top-three test confounds:

    detection      did the swarm see this mistake at all?
    prioritisation did it choose to say it?

A top-three comparison can only ever measure the second, and it fails silently
when the first is the problem — which is exactly what happened on `bernes`,
where the pattern was detected, priced, and then discarded by the ranking
(ADR-0010).

Two annotation styles appear in the data and both are handled:

    "4. Instant moves."              a claim about the game
    "8. Loosing queen for knight move 31."   a claim about one move

The second is far stronger evidence, because it can be checked against a
specific ply rather than against a game-level rate. That is why the reviewer
started adding them, and why the pack should have asked for them from the start.

Usage:
    python compare.py --engine PATH [--cache CACHE] [--player bjagus]
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.analysis.labels import INACCURACY_WP  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.tactics import detect_motifs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"

# The reviewer counts full moves; the swarm counts plies. A note saying "move 31"
# may land on either colour's 31st move, and a human reading a board is easily a
# move out either way, so a window is allowed rather than an exact hit.
MOVE_WINDOW = 1

# Where the annotation block ends and the original form resumes.
FORM_RESUMES = "What is this player's MAIN weakness"


@dataclass(frozen=True)
class Note:
    game: int
    text: str
    move: int | None

    @property
    def is_move_level(self) -> bool:
        return self.move is not None


def parse_notes(path: Path) -> list[Note]:
    """Read "<game>. <text> [move <n>]" lines out of the filled form."""
    notes: list[Note] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if FORM_RESUMES in line:
            break
        # Anchored at column 0 on purpose: the form's own worked examples are
        # indented, and an earlier version of this counted them as data. Two
        # phantom notes and a phantom "instant moves" confirmation, from the
        # instructions telling the reviewer what a note looks like.
        match = re.match(r"(\d+)\.\s+(\S.*?)\s*$", line)
        if not match:
            continue
        game, text = int(match.group(1)), match.group(2)
        # "0." is the form's own how-many-games question, not a note.
        if game == 0:
            continue
        move = re.search(r"move\s+(\d+)", text, re.IGNORECASE)
        notes.append(
            Note(game=game, text=text, move=int(move.group(1)) if move else None)
        )
    return notes


# What each phrase the reviewer used would have to look like in the swarm's
# vocabulary. Deliberately written from THEIR words outward, not from the claim
# list inward -- the point is to find what has no mapping at all.
# Longest and most specific first: the first match wins, so "piece loosing"
# (a threat against them they did not see) must be tested before "piece" alone.
#
# Written by the agent AFTER reading the reviewer's notes, which makes it the
# weakest link in E31 and is stated as such in the note. It is a table rather
# than a model so it can be argued with line by line.
VOCABULARY: tuple[tuple[str, tuple[str, ...]], ...] = (
    # --- things with no detector at all -----------------------------------
    ("good bishop for a bad knight", ()),
    ("good piece for a bad one", ()),
    ("quitting the game", ()),          # resignation behaviour
    ("quitting a game", ()),
    ("developing a piece improperly", ()),
    ("an passant", ()),                 # en passant is not a tracked motif
    ("material saving defense", ()),    # defensive resources are not detected
    ("additional material loosng defense", ()),
    ("preventable checkmate", ("backRankMate",)),
    ("checkmate treath", ("backRankMate",)),
    ("checkmate", ("backRankMate",)),

    # --- threats against them that they did not see (ALLOWED) --------------
    ("piece loosing", ("hangingPiece", "trappedPiece")),
    ("pawn loosing", ("hangingPawn",)),
    ("loosing pawn motif", ("hangingPawn",)),
    ("a loosing pawn", ("hangingPawn",)),
    ("a loosing piece", ("hangingPiece", "trappedPiece")),
    ("placing a piece on the attacked square", ("hangingPiece",)),
    ("queen on the attacked square", ("hangingPiece",)),
    ("queen taking treath", ("hangingPiece",)),

    # --- their own chances they did not take (MISSED) ----------------------
    ("piece winning", ("hangingPiece", "trappedPiece")),
    ("material taking", ("hangingPiece",)),
    ("pawn taking", ("hangingPawn",)),
    ("not taking a pawn back", ("hangingPawn",)),
    ("not taking a pawn", ("hangingPawn",)),
    ("not taking queen", ("hangingPiece",)),
    ("not taking a piece", ("hangingPiece",)),
    ("not taking material", ("hangingPiece",)),
    ("queen taking opportunity", ("hangingPiece",)),
    ("hanging pawn", ("hangingPawn",)),
    ("pinned piece", ("pin",)),
    ("defense exchange", ("capturingDefender",)),

    # --- either direction, motif named outright ---------------------------
    ("fork", ("fork",)),
    ("pin", ("pin",)),
    ("skewer", ("skewer",)),
    ("discovered", ("discoveredAttack",)),

    # --- material, unspecified -------------------------------------------
    ("loosing a pawn", ("hangingPawn",)),
    ("loosing pawn", ("hangingPawn",)),
    ("loosing a queen", ("hangingPiece",)),
    ("loosing queen", ("hangingPiece",)),
    ("loosing a piece", ("hangingPiece", "trappedPiece")),
    ("loosing piece", ("hangingPiece", "trappedPiece")),
    ("loosing pieces", ("hangingPiece", "trappedPiece")),
    ("loosing material", ("hangingPiece", "trappedPiece")),

    # --- structure and squares -------------------------------------------
    ("great square for the opponent knight", ("allows_square:outpost",)),
    ("isolated pawn", ("concedes_weakness:isolated",)),
    ("messing up pawn structure", ("concedes_weakness",)),
    ("worsening pawn structure", ("concedes_weakness",)),
    ("pawn structure", ("concedes_weakness",)),

    # --- king safety and process -----------------------------------------
    ("king attack", ("allows_pressure",)),
    ("defending the king", ("allows_pressure",)),
    ("not defending properly", ("allows_pressure",)),
    ("greedy over material", ("allows_pressure",)),
    ("instant move", ("instant_move_error",)),
)


def expected_signals(text: str) -> tuple[str, ...] | None:
    """What the swarm would have to detect for this note to be matched."""
    lowered = text.lower()
    for phrase, signals in VOCABULARY:
        if phrase in lowered:
            return signals
    return None


@dataclass
class GameFacts:
    """Everything the swarm noticed in one game, keyed for lookup by move."""

    index: int
    game_id: str
    errors_by_move: dict[int, list[str]]
    motifs_by_move: dict[int, set[str]]
    instant_moves: int
    instant_errors: int
    # Every move's loss, labelled or not. The labelled ones are a subset, and
    # the gap between them is the finding: a move can cost real win probability
    # and carry no label, so no motif detector ever runs on it.
    loss_by_move: dict[int, float]

    def worst_loss_near(self, move: int, window: int = MOVE_WINDOW) -> float:
        return max(
            (self.loss_by_move.get(move + offset, 0.0)
             for offset in range(-window, window + 1)),
            default=0.0,
        )

    def signals_near(self, move: int, window: int = MOVE_WINDOW) -> set[str]:
        found: set[str] = set()
        for offset in range(-window, window + 1):
            found |= self.motifs_by_move.get(move + offset, set())
            if self.errors_by_move.get(move + offset):
                found.add("error")
        return found


def analyse(player: str, engine: str, cache: str | None, depth: int, limit: int):
    games = load_games(ROOT / "games" / f"{player}.pgn")[:limit]
    corpus = build_corpus(player, games)
    with engine_session(engine, depth, cache) as session:
        observations = analyse_corpus(corpus, games, session.analyser)

    by_game: dict[str, list] = {}
    for observation in observations:
        by_game.setdefault(observation.game_id, []).append(observation)

    facts = []
    for index, game in enumerate(games, start=1):
        own = [o for o in by_game.get(game.game_id, []) if o.mover == player]
        errors_by_move: dict[int, list[str]] = {}
        motifs_by_move: dict[int, set[str]] = {}
        instant = [o for o in own if (o.seconds_spent or 99) <= 2.0]

        loss_by_move: dict[int, float] = {}
        for o in own:
            move_no = o.ply // 2 + 1
            loss_by_move[move_no] = max(loss_by_move.get(move_no, 0.0), o.loss_wp)
            if o.label is not None:
                errors_by_move.setdefault(move_no, []).append(o.label.value)
                # What the opponent's best reply would have executed, and what
                # the player's own best move would have.
                motifs_by_move.setdefault(move_no, set())
                motifs_by_move[move_no] |= _motifs_at(o)

        facts.append(
            GameFacts(
                index=index,
                game_id=game.game_id,
                errors_by_move=errors_by_move,
                motifs_by_move=motifs_by_move,
                instant_moves=len(instant),
                instant_errors=sum(1 for o in instant if o.label is not None),
                loss_by_move=loss_by_move,
            )
        )
    return facts


def _motifs_at(observation) -> set[str]:
    """Motifs the engine's own best move would have executed at this position."""
    import chess

    if not observation.best_move:
        return set()
    board = chess.Board(observation.fen_before)
    move = chess.Move.from_uci(observation.best_move)
    if move not in board.legal_moves:
        return set()
    # `hangingPawn` is a real motif since E32; it used to be synthesised here
    # from the captured piece type, which is exactly the kind of analysis that
    # belongs in the product rather than in a comparison script.
    return set(detect_motifs(board, move))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", default=None)
    parser.add_argument("--player", default="bjagus")
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--games", type=int, default=20)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    notes = parse_notes(ROOT / "a-your-reading" / f"{args.player}.txt")
    print(f"{len(notes)} notes across {len({n.game for n in notes})} games")
    print(f"  of those, {sum(1 for n in notes if n.is_move_level)} carry a move number\n")

    facts = {f.index: f for f in analyse(args.player, args.engine, args.cache,
                                         args.depth, args.games)}

    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    say(f"{'game':>5}  {'move':>5}  {'reviewer noted':<44}{'loss':>6}  {'swarm':<20}verdict")
    say("-" * 104)
    losses: list[float] = []
    pawn_losses: list[float] = []

    tally = {
        "named": 0, "saw_only": 0, "missed": 0,
        "no_detector": 0, "unmapped": 0, "no_move": 0,
        "instant_hit": 0, "instant_miss": 0,
        "pawn_notes": 0, "pawn_unnamed": 0,
    }

    for note in sorted(notes, key=lambda n: (n.game, n.move or 0)):
        game = facts.get(note.game)
        expected = expected_signals(note.text)
        text = note.text[:46]

        if expected is None:
            say(f"{note.game:>5}  {'':>5}  {text:<48}{'?':<22}UNMAPPED")
            tally["unmapped"] += 1
            continue
        if not expected:
            say(f"{note.game:>5}  {'':>5}  {text:<48}{'-':<22}NO DETECTOR")
            tally["no_detector"] += 1
            continue
        if game is None:
            say(f"{note.game:>5}  {'':>5}  {text:<48}{'-':<22}GAME NOT ANALYSED")
            continue

        if note.move is None:
            # Game-level claim. "Instant moves" is checkable without a move
            # number; the rest are not, and saying so is better than guessing.
            if "instant_move_error" in expected:
                hit = game.instant_moves >= 5
                say(f"{note.game:>5}  {'':>5}  {text:<48}"
                    f"{f'{game.instant_moves} instant':<22}"
                    f"{'MATCHED' if hit else 'not seen'}")
                tally["instant_hit" if hit else "instant_miss"] += 1
            else:
                say(f"{note.game:>5}  {'':>5}  {text:<48}{'-':<22}NO MOVE GIVEN")
                tally["no_move"] += 1
            continue

        found = game.signals_near(note.move)
        named = any(signal in found for signal in expected)
        saw = "error" in found

        shown = ",".join(sorted(s for s in found if s != "error"))[:20] or (
            "error only" if saw else "nothing"
        )
        # Three outcomes, not two. Collapsing the middle one into "missed" is
        # what made the first run of this read 25 % when the detection figure
        # was 80 %, and it would have been a badly wrong thing to report.
        if named:
            verdict, key = "NAMED", "named"
        elif saw:
            verdict, key = "saw, did not name", "saw_only"
        else:
            verdict, key = "MISSED", "missed"

        loss = game.worst_loss_near(note.move)
        say(f"{note.game:>5}  {note.move:>5}  {text:<44}{loss:>6.1f}  {shown:<20}{verdict}")
        tally[key] += 1
        losses.append(loss)
        if "pawn" in note.text.lower():
            tally["pawn_notes"] += 1
            pawn_losses.append(loss)
            if not named:
                tally["pawn_unnamed"] += 1

    say()
    say("=" * 104)
    checkable = tally["named"] + tally["saw_only"] + tally["missed"]
    say("MOVE-LEVEL NOTES — the ones that can actually be checked")
    say(f"  notes carrying a move number        {checkable}")
    if checkable:
        detected = tally["named"] + tally["saw_only"]
        say(f"  the swarm flagged that same move   {detected:>3}  ({detected/checkable:.0%})"
            "   <- DETECTION")
        say(f"    ...and named the same pattern    {tally['named']:>3}  "
            f"({tally['named']/checkable:.0%})   <- NAMING")
        say(f"    ...but could not name it         {tally['saw_only']:>3}  "
            f"({tally['saw_only']/checkable:.0%})")
        say(f"  the swarm saw nothing there        {tally['missed']:>3}  "
            f"({tally['missed']/checkable:.0%})")
    say()
    say("PAWN MATERIAL")
    say(f"  notes mentioning a pawn             {tally['pawn_notes']}")
    say(f"  of those, unnamed by the swarm      {tally['pawn_unnamed']}")
    if pawn_losses:
        below = sum(1 for loss in pawn_losses if loss < INACCURACY_WP)
        say(f"  median loss at those moves          {statistics.median(pawn_losses):.1f} wp")
        say(f"  below the {INACCURACY_WP:.0f} wp label threshold      "
            f"{below}/{len(pawn_losses)}"
            "   <- no label means no motif ever runs")
    if losses:
        below_all = sum(1 for loss in losses if loss < INACCURACY_WP)
        say()
        say("ALL NOTED MOVES")
        say(f"  median loss where you saw a mistake {statistics.median(losses):.1f} wp")
        say(f"  below the label threshold           {below_all}/{len(losses)}")
    say()
    say("EVERYTHING ELSE")
    say(f"  game-level 'instant moves' notes     {tally['instant_hit']} confirmed, "
        f"{tally['instant_miss']} not")
    say(f"  no detector exists for              {tally['no_detector']}")
    say(f"  game-level, no move to check         {tally['no_move']}")
    say(f"  wording not mapped                  {tally['unmapped']}")

    (args.out / f"{args.player}-move-level.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(f"\nwritten {args.out / f'{args.player}-move-level.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
