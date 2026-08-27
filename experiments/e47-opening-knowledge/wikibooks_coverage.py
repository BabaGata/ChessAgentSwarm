"""E47b — do the positions these players reach have Wikibooks pages worth quoting?

Layer 2's pre-check, from [[design.informative-claims]]: *"Wikibooks is uneven.
Before building on it, measure what fraction of the positions the twelve review
players actually reach have a real page. At 20 % it is decoration; at 80 % it
carries the claim."*

Wikibooks *Chess Opening Theory* titles **are** the move sequence —
`Chess Opening Theory/1. e4/1...e5/2. Nf3/2...Nc6/3. Bc4` — so a position maps to
a title with no search step. White's move is `N. SAN`, Black's is `N...SAN`.

**Queried through the MediaWiki API rather than by fetching pages**, 50 titles per
request: it is one request per fifty instead of one per title, it returns
`missing` explicitly rather than by guessing at a 404 page, and `length` comes
back with it so a stub can be told from an article. Politer and more accurate at
once.

The position asked about is the **deepest one still in theory** — the named
opening the player actually reached, which is where the ideas belong.

Usage:
    python wikibooks_coverage.py [--window 20] [--stub-bytes 1500]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.openings import OpeningBook  # noqa: E402
from chesscoach.pipeline import load_games  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"
API = "https://en.wikibooks.org/w/api.php"
PREFIX = "Chess Opening Theory"
# Wikimedia asks for a descriptive agent naming the project and a contact.
AGENT = "ChessAgentSwarm/0.1 (thesis research; https://github.com/lichess-org/chess-openings)"
BATCH = 50


def title_for(sans: list[str]) -> str:
    """The Wikibooks title for a move sequence, in their own convention."""
    parts = [PREFIX]
    for index, san in enumerate(sans):
        move_no = index // 2 + 1
        parts.append(f"{move_no}. {san}" if index % 2 == 0 else f"{move_no}...{san}")
    return "/".join(parts)


def page_info(titles: list[str]) -> dict[str, int | None]:
    """Length in bytes per title, or None where the page does not exist."""
    found: dict[str, int | None] = {}
    for start in range(0, len(titles), BATCH):
        chunk = titles[start : start + BATCH]
        query = urllib.parse.urlencode({
            "action": "query", "prop": "info", "format": "json",
            "formatversion": "2", "titles": "|".join(chunk),
        })
        request = urllib.request.Request(f"{API}?{query}", headers={"User-Agent": AGENT})
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        for page in payload.get("query", {}).get("pages", []):
            found[page["title"]] = None if page.get("missing") else page.get("length", 0)
        # Normalisation can rename a title; anything unreturned is treated as absent.
        for title in chunk:
            found.setdefault(title, None)
        print(f"  queried {min(start + BATCH, len(titles))}/{len(titles)}", flush=True)
        time.sleep(0.5)
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--stub-bytes", type=int, default=1500)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    book = OpeningBook.load()
    wanted: dict[str, dict] = {}

    for path in sorted(ROOT.glob("games/*.pgn")):
        player = path.stem
        for game in load_games(path)[: args.window]:
            walk = book.walk(list(game.moves))
            if not walk.plies_in_book:
                continue
            board, sans = chess.Board(), []
            for uci in list(game.moves)[: walk.plies_in_book]:
                move = chess.Move.from_uci(uci)
                if move not in board.legal_moves:
                    break
                sans.append(board.san(move))
                board.push(move)
            title = title_for(sans)
            entry = wanted.setdefault(title, {
                "plies": len(sans), "games": 0,
                "opening": walk.opening.name if walk.opening else "-",
            })
            entry["games"] += 1

    titles = sorted(wanted)
    print(f"{len(titles)} distinct positions reached across the twelve players\n")
    lengths = page_info(titles)

    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    real = [t for t in titles if (lengths.get(t) or 0) >= args.stub_bytes]
    stub = [t for t in titles if lengths.get(t) is not None
            and (lengths.get(t) or 0) < args.stub_bytes]
    missing = [t for t in titles if lengths.get(t) is None]

    total_games = sum(e["games"] for e in wanted.values())
    games_real = sum(wanted[t]["games"] for t in real)
    games_stub = sum(wanted[t]["games"] for t in stub)

    say("WIKIBOOKS COVERAGE OF THE POSITIONS THESE PLAYERS REACH")
    say()
    say(f"{'':<26}{'positions':>11}{'games':>8}")
    say("-" * 46)
    say(f"{'article (>= ' + str(args.stub_bytes) + ' bytes)':<26}"
        f"{len(real):>11}{games_real:>8}")
    say(f"{'stub':<26}{len(stub):>11}{games_stub:>8}")
    say(f"{'no page':<26}{len(missing):>11}"
        f"{total_games - games_real - games_stub:>8}")
    say(f"{'TOTAL':<26}{len(titles):>11}{total_games:>8}")
    say()
    say(f"  by position: {len(real)/len(titles):.0%} have an article")
    say(f"  by GAME:     {games_real/total_games:.0%} of games land on one")
    say("  (games is the number that matters — a common opening covered well is")
    say("   worth more than a rare one covered badly)")

    say()
    say("COVERAGE BY DEPTH — where does it thin out?")
    say(f"{'plies':>6}{'positions':>11}{'with article':>14}")
    say("-" * 33)
    by_depth: dict[int, list[str]] = {}
    for title in titles:
        by_depth.setdefault(wanted[title]["plies"], []).append(title)
    for plies in sorted(by_depth):
        group = by_depth[plies]
        hit = sum(1 for t in group if (lengths.get(t) or 0) >= args.stub_bytes)
        say(f"{plies:>6}{len(group):>11}{hit:>9} ({hit/len(group):>3.0%})")

    # --- the rescue: back off up the tree -----------------------------------
    # The deepest position rarely has a page, but its ANCESTORS do: the ideas of
    # "the Scandinavian" still apply to a player four plies into a Scandinavian
    # subline. Generic-but-relevant beats silent, up to a point -- 1. e4 on its
    # own says nothing worth saying, so a floor of 2 plies is imposed.
    MIN_USEFUL_PLIES = 2
    ancestors: set[str] = set()
    for title in titles:
        parts = title.split("/")
        for cut in range(len(parts), MIN_USEFUL_PLIES, -1):
            ancestors.add("/".join(parts[:cut]))
    unknown = sorted(ancestors - set(lengths))
    if unknown:
        print(f"checking {len(unknown)} ancestor positions", flush=True)
        lengths.update(page_info(unknown))

    best_depth: list[int] = []
    rescued_games = 0
    for title in titles:
        parts = title.split("/")
        for cut in range(len(parts), MIN_USEFUL_PLIES, -1):
            candidate = "/".join(parts[:cut])
            if (lengths.get(candidate) or 0) >= args.stub_bytes:
                best_depth.append(cut - 1)
                rescued_games += wanted[title]["games"]
                break

    say()
    say("WITH FALLBACK TO THE DEEPEST ANCESTOR THAT HAS AN ARTICLE")
    say(f"  positions with usable ideas: {len(best_depth)}/{len(titles)} "
        f"({len(best_depth)/len(titles):.0%})")
    say(f"  GAMES with usable ideas:     {rescued_games}/{total_games} "
        f"({rescued_games/total_games:.0%})")
    if best_depth:
        say(f"  depth of the article used: median {statistics.median(best_depth):.0f} plies, "
            f"i.e. around move {statistics.median(best_depth)/2:.1f}")
        say(f"  distribution: {dict(sorted(Counter(best_depth).items()))}")
    say("  The deeper the article, the more specific the ideas. A page at 2 plies")
    say("  names a defence; one at 6 names a variation.")

    if real:
        sizes = sorted((lengths[t] or 0) for t in real)
        say()
        say(f"  article size: median {statistics.median(sizes):,.0f} bytes, "
            f"max {sizes[-1]:,.0f}")
        say()
        say("  most-reached positions that DO have an article:")
        for title in sorted(real, key=lambda t: -wanted[t]["games"])[:8]:
            say(f"    {wanted[title]['games']:>3} games  {wanted[title]['opening'][:40]:<42}"
                f" {title.replace(PREFIX + '/', '')[:44]}")
        say()
        say("  most-reached positions with NO article:")
        for title in sorted(missing, key=lambda t: -wanted[t]["games"])[:8]:
            say(f"    {wanted[title]['games']:>3} games  {wanted[title]['opening'][:40]:<42}"
                f" {title.replace(PREFIX + '/', '')[:44]}")

    (args.out / "wikibooks-coverage.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {args.out / 'wikibooks-coverage.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
