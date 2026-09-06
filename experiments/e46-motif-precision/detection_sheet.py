"""One sheet listing everything the swarm detects, with examples to check.

The author, after finding the motifs wrong: *"I would like to get a test setup
where all that is detected is written out with 5 examples so that I can evaluate
if the examples are correct easily in the same form."*

**Everything**, not only the motifs. Every claim the system can make is here —
tactical motifs, phase errors, clock claims, structural concessions, material
claims — in one uniform shape, so judging them is one repeated action rather than
nine different ones.

This is possible because of `Measurement.instances_at`, added for D15: every claim
records the exact (game_id, ply) of every instance it counted, so a sheet can cite
real instances of any claim rather than only of the ones with sampled evidence.

**Both pools are included.** A claim that failed the confidence gate is still a
detection — it was measured, it fired on real moves, and whether those firings are
*correct* is exactly what this asks. Filtering to what reached a report would hide
the detectors that most need checking.

Usage:
    python detection_sheet.py --engine PATH --peers PEERS [--cache CACHE]
                              [--window 20] [--examples 5]
"""

from __future__ import annotations

import argparse
import hashlib
import random
import subprocess
import sys
from datetime import date
from collections import defaultdict
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.orchestrator import default_agents, diagnose  # noqa: E402
from chesscoach.peers import PeerReference  # noqa: E402
from chesscoach.phrasing import move_number, statement  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.motif_evidence import describe  # noqa: E402
from chesscoach.sections.base import SectionContext  # noqa: E402
from chesscoach.tactics import detect_motifs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"

HEADER = """WHAT THE SYSTEM DETECTS — a sheet for checking whether it is right
==============================================================================

Every claim the swarm can make, with {n} real examples each, in one shape.

For each example: open the link, look at the position, and mark the box.

    [y]  the claim is true of this move
    [n]  it is not
    [?]  cannot tell

You are judging the CLAIM, not the move. A move can be bad for other reasons
and still not be the thing named here — that is [n], and it is the single most
useful mark on this sheet.

The line reads:   player · move number · colour · the move · what it cost
The link opens the game at that move.

Claims are ordered by how often they fired, because a detector that fires often
and is wrong does the most damage. Anything marked NO INSTANCES fired nowhere in
these games, which is worth knowing too.

==============================================================================
"""


def provenance() -> str:
    """Which commit produced this sheet, so marks on it can be dated."""
    root = Path(__file__).resolve().parents[2]
    try:
        done = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root, capture_output=True, text=True, timeout=20, check=False,
        )
        commit = done.stdout.strip() if done.returncode == 0 else "unknown"
    except (OSError, subprocess.SubprocessError):
        commit = "unknown"
    return (
        f"GENERATED {date.today().isoformat()} from commit {commit}.\n"
        f"Marks on this sheet judge THAT code. If a detector changes afterwards its\n"
        f"marks stop being evidence about it -- record this line with them."
    )


def motif_line(claim_key: str, observation) -> str | None:
    """The move that executes the motif, and the pieces that make it true.

    Without this a reader judging *"is this a pin?"* has only the player's own
    move to look at -- and for an `allowed_motif` claim that move is **not the
    pin**: it is the mistake that allowed one, and the pin belongs to the
    opponent's reply. The author asked for the pieces to be marked so a wrong
    name can be told from a right one; this is that line.

    Derived rather than stored, so it cannot go stale against the detectors, and
    free: no engine call, both positions are already in the observation.
    """
    parts = claim_key.split(".")
    if len(parts) < 2 or parts[0] not in ("allowed_motif", "missed_motif", "executed_motif"):
        return None
    kind, motif = parts[0], parts[1]

    try:
        board = chess.Board(observation.fen_before)
    except ValueError:
        return None

    if kind == "allowed_motif":
        # The opponent is to move after the player's mistake, and theirs is the
        # move that executes the motif.
        try:
            played = chess.Move.from_uci(observation.move_played)
        except ValueError:
            return None
        if played not in board.legal_moves:
            return None
        board.push(played)
        candidates = list(board.legal_moves)
        label = "punished by"
    else:
        if not observation.best_move:
            return None
        try:
            candidates = [chess.Move.from_uci(observation.best_move)]
        except ValueError:
            return None
        label = "was available"

    for move in candidates:
        if move not in board.legal_moves:
            continue
        if motif not in {str(m) for m in detect_motifs(board, move)}:
            continue
        told = describe(board, move, motif)
        san = board.san(move)
        return f"{label} {san}" + (f" -- {told}" if told else "")
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--peers", required=True)
    parser.add_argument("--cache", default=None)
    parser.add_argument("--depth", type=int, default=15)
    # 60, not the 20 the rest of the review experiments use.
    #
    # **20 exists to match what a human read**: [[experiments.e39-review-window]]
    # found the swarm's leading finding changes 75 % of the time between a
    # 20-game window and the full corpus, so a ranked comparison against a
    # reviewer who read 20 games has to be built from those same 20 or it
    # measures the sample and not the diagnosis.
    #
    # **That argument does not reach this sheet.** Nothing here is ranked or
    # compared against a human's ordering: each box asks whether one claim is
    # true of one position, which does not depend on which games were read.
    # What the narrow window did instead was judge the swarm at what E39 itself
    # called "its weakest operating point" -- the system's own default is 60
    # (`cli.py --games`), every reviewed player has 60 games on disk, and E43
    # measured 15 claims blocked at 20 and none at 60.
    #
    # Measured here: **25 -> 36 claims with instances**, twelve of them silent
    # at 20 -- including `missed_motif.capturingDefender`, which goes from 1
    # instance in 6 opportunities to 8 in 24, crossing its peer rate. Two claims
    # stop firing and both sat *below* the peer rate at either window, so the
    # extra games confirmed the players are ordinary rather than hiding
    # anything. Marking cost rises only 125 -> 178 boxes, because `--examples`
    # caps the sample per claim however many instances there are.
    parser.add_argument("--window", type=int, default=60)
    parser.add_argument("--examples", type=int, default=5)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    peers = PeerReference.load(args.peers)
    # claim key -> {"say": sentence, "hits": [instance, ...], "players": {names}}
    claims: dict[str, dict] = defaultdict(
        lambda: {"say": "", "hits": [], "players": set()}
    )
    vocabulary: set[str] = set()

    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in sorted(ROOT.glob("games/*.pgn")):
            player = path.stem
            games = load_games(path)[: args.window]
            corpus = build_corpus(player, games)
            if corpus.n_games == 0:
                continue
            observations = analyse_corpus(corpus, games, session.analyser)
            context = SectionContext(
                observations, corpus, session.provenance(corpus.corpus_id),
                band="1400-1800", time_control="rapid", peers=peers,
            )
            agents = default_agents()
            result = diagnose(context, agents)
            at = {(o.game_id, o.ply): o for o in observations}

            # `measure` reports every condition a section looked at, whatever the
            # confidence policy then did with it, so the sheet can say what the
            # vocabulary *contains* and not only what happened to fire. Without
            # this a claim that never reached `watch` is invisible, and "it never
            # fires" is as much a defect as "it fires wrongly".
            for agent in agents:
                try:
                    for condition in agent.measure(context):
                        vocabulary.add(condition.claim_key)
                except Exception as error:  # a section may refuse to measure
                    print(f"    {agent.section}: measure unavailable ({error})",
                          flush=True)

            for finding in tuple(result.findings) + tuple(result.sub_threshold):
                entry = claims[finding.claim.key()]
                entry["say"] = statement(finding)
                entry["players"].add(player)
                for ref in finding.measurement.instances_at:
                    observation = at.get(ref)
                    if observation is not None:
                        entry["hits"].append((player, observation))
            print(f"  {player}: {len(result.findings)} asserted, "
                  f"{len(result.sub_threshold)} measured", flush=True)

    # Stamped so a mark can be dated against the code it judged. Without this
    # the twenty-three marks of 2026-08-23 could not be checked for staleness at
    # all -- the detectors were rebuilt the next day and nobody could say
    # whether the marks came before or after, which made them unusable rather
    # than merely old.
    lines = [HEADER.format(n=args.examples), provenance(), ""]
    ordered = sorted(claims.items(), key=lambda kv: (-len(kv[1]["hits"]), kv[0]))

    for key, entry in ordered:
        hits = entry["hits"]
        lines.append("")
        lines.append(f"{key}")
        lines.append(f"    claims: {entry['say']}")
        if not hits:
            lines.append("    NO INSTANCES in these games.")
            lines.append("-" * 78)
            continue
        lines.append(
            f"    {len(hits)} instances across {len(entry['players'])} players"
        )
        lines.append("-" * 78)

        digest = hashlib.sha256(key.encode("utf-8")).digest()
        rng = random.Random(int.from_bytes(digest[:8], "big"))
        pool = sorted(hits, key=lambda h: (h[0], h[1].game_id, h[1].ply))
        for player, o in sorted(
            rng.sample(pool, min(args.examples, len(pool))),
            key=lambda h: (h[0], h[1].ply),
        ):
            try:
                board = chess.Board(o.fen_before)
                move = chess.Move.from_uci(o.move_played)
                san = board.san(move) if move in board.legal_moves else o.move_played
            except (ValueError, IndexError):
                san = o.move_played
            colour = "White" if o.mover_is_white else "Black"
            lines.append(
                f"  [ ] {player:<21} move {move_number(o.ply):>3}  {colour:<5} "
                f"{san:<8} lost {o.loss_wp:>5.1f} wp"
            )
            lines.append(f"      lichess.org/{o.game_id}#{o.ply}")
            told = motif_line(key, o)
            if told:
                lines.append(f"      {told}")

    silent = sorted(vocabulary - set(claims))
    if silent:
        lines += [
            "",
            "=" * 78,
            "NEVER FIRED IN THESE GAMES",
            "",
            "The system can make these claims and did not, for any of the twelve.",
            "Nothing to check here — listed so the vocabulary is visible in full,",
            "because a detector that never fires is as much a defect as one that",
            "fires wrongly, and it cannot be seen from the sheet above.",
            "-" * 78,
        ]
        lines += [f"  {key}" for key in silent]

    lines += [
        "",
        "=" * 78,
        f"{len(ordered)} claims with instances, {len(silent)} that never fired, "
        f"{len(vocabulary | set(claims))} in the vocabulary.",
    ]

    out = args.out / "detection-sheet.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
    print(f"\n{len(ordered)} claims written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
