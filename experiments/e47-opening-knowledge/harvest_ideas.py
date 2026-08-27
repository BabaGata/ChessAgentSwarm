"""E47c — the actual ideas text, for the openings these players actually play.

E47b measured whether a page *exists*. It did not read one. The open question it
left: *"coverage was measured on titles, not on whether the prose contains usable
plans rather than a move list."* Only a human can settle that, so this produces
the text to be judged rather than a number about it.

Ranked by **games played across the twelve**, because a well-covered rare line is
worth less than a thinly-covered common one.

Uses the MediaWiki API's `extracts` (`explaintext`), which returns the article as
plain prose — no HTML parsing, no scraping, and the same politeness as before.
Falls back up the tree to the deepest ancestor with an article, as E47b
established is necessary, and **records which depth the text came from**, because
ideas quoted from `1. e4 e5` are about a defence and ideas from six plies down are
about a variation, and a reader cannot tell them apart from the prose alone.

**Licence: CC BY-SA 4.0.** Every entry carries its source URL. Text is stored
**verbatim and never paraphrased** — paraphrase is where folklore re-enters (R-03).

Usage:
    python harvest_ideas.py [--window 20] [--top 15] [--chars 1200]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
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
AGENT = "ChessAgentSwarm/0.1 (thesis research)"
LICENCE = "CC BY-SA 4.0"
MIN_USEFUL_PLIES = 2
STUB_BYTES = 1500


def title_for(sans: list[str]) -> str:
    parts = [PREFIX]
    for index, san in enumerate(sans):
        number = index // 2 + 1
        parts.append(f"{number}. {san}" if index % 2 == 0 else f"{number}...{san}")
    return "/".join(parts)


def api(params: dict, attempts: int = 5) -> dict:
    """One API call, backing off when Wikimedia says to.

    A 429 is the server asking for less, not an error to retry immediately.
    Doubling the wait each time and starting from a full second keeps a
    fifteen-title harvest well inside what a shared resource should be asked for.
    """
    query = urllib.parse.urlencode({**params, "format": "json", "formatversion": "2"})
    request = urllib.request.Request(f"{API}?{query}", headers={"User-Agent": AGENT})
    delay = 1.0
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == attempts - 1:
                raise
            print(f"    rate limited, waiting {delay:.0f}s", flush=True)
            time.sleep(delay)
            delay *= 2
    return {}


def extracts(titles: list[str]) -> dict[str, str]:
    """Article text as plain prose, per title — one request each, deliberately.

    Two wrong turns worth recording, because both looked like "Wikibooks has no
    prose" and neither was:

    * `extracts` returns **one** extract per request unless `exintro` is set, so
      asking for twenty titles produced nineteen blanks;
    * and `exintro` returns **empty on these pages**, because they have no lead
      section — the content begins under a heading like `== 3. Bc4 · Italian
      game ==`. The intro is genuinely empty; the article is not.

    So: full extracts, one title per request. Fifteen requests for fifteen
    openings, in an outer loop that caches — which is affordable, and correct.
    """
    out: dict[str, str] = {}
    for index, title in enumerate(titles, start=1):
        payload = api({
            "action": "query", "prop": "extracts", "explaintext": "1",
            "exsectionformat": "plain", "titles": title,
        })
        for page in payload.get("query", {}).get("pages", []):
            if not page.get("missing"):
                out[page["title"]] = page.get("extract", "") or ""
        time.sleep(1.5)
        print(f"  fetched {index}/{len(titles)}", flush=True)
    return out


def lengths_of(titles: list[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for start in range(0, len(titles), 50):
        chunk = titles[start : start + 50]
        payload = api({"action": "query", "prop": "info", "titles": "|".join(chunk)})
        for page in payload.get("query", {}).get("pages", []):
            out[page["title"]] = 0 if page.get("missing") else page.get("length", 0)
        time.sleep(1.0)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--top", type=int, default=15)
    parser.add_argument("--chars", type=int, default=1200)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    book = OpeningBook.load()
    # opening name -> games, and the deepest title reached for it
    played: Counter = Counter()
    deepest_title: dict[str, tuple[int, str]] = {}
    who: dict[str, Counter] = {}

    for path in sorted(ROOT.glob("games/*.pgn")):
        player = path.stem
        for game in load_games(path)[: args.window]:
            walk = book.walk(list(game.moves))
            if walk.opening is None or not walk.plies_in_book:
                continue
            board, sans = chess.Board(), []
            for uci in list(game.moves)[: walk.plies_in_book]:
                move = chess.Move.from_uci(uci)
                if move not in board.legal_moves:
                    break
                sans.append(board.san(move))
                board.push(move)
            # Group by the family, not the exact subline: "Scandinavian Defense"
            # rather than five near-identical variation names.
            family = walk.opening.name.split(":")[0]
            played[family] += 1
            who.setdefault(family, Counter())[player] += 1
            best = deepest_title.get(family)
            if best is None or len(sans) > best[0]:
                deepest_title[family] = (len(sans), title_for(sans))

    top = played.most_common(args.top)
    print(f"{len(played)} opening families; harvesting the top {len(top)}\n")

    # Every ancestor of every top family's deepest title, so the fallback can run.
    candidates: list[str] = []
    for family, _ in top:
        _, title = deepest_title[family]
        parts = title.split("/")
        for cut in range(len(parts), MIN_USEFUL_PLIES, -1):
            candidates.append("/".join(parts[:cut]))
    candidates = sorted(set(candidates))
    sizes = lengths_of(candidates)

    chosen: dict[str, str] = {}
    for family, _ in top:
        _, title = deepest_title[family]
        parts = title.split("/")
        for cut in range(len(parts), MIN_USEFUL_PLIES, -1):
            candidate = "/".join(parts[:cut])
            if sizes.get(candidate, 0) >= STUB_BYTES:
                chosen[family] = candidate
                break

    text = extracts(sorted(set(chosen.values())))

    lines = [
        "IDEAS FOR THE OPENINGS THESE PLAYERS ACTUALLY PLAY",
        "=" * 78,
        "",
        f"Source: Wikibooks 'Chess Opening Theory', {LICENCE}. Text is quoted",
        "verbatim, never paraphrased, and every entry carries its URL.",
        "",
        "Ranked by games played across the twelve review players. 'depth' is how",
        "many plies deep the article is: at 2 it describes a defence, at 6 a named",
        "variation. The shallower it is, the less it is about what the player",
        "actually played.",
        "",
        "The question to answer while reading: does this contain a PLAN a 1500",
        "could act on, or is it a move list with commentary?",
        "",
    ]

    for family, games in top:
        title = chosen.get(family)
        lines += ["=" * 78, f"{family}  —  {games} games", ""]
        if title is None:
            lines += ["  NO ARTICLE at any depth.", ""]
            continue
        depth = len(title.split("/")) - 1
        url = "https://en.wikibooks.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))
        top_players = ", ".join(f"{p} ({n})" for p, n in who[family].most_common(3))
        lines += [
            f"  article depth : {depth} plies" + ("   <-- generic" if depth <= 2 else ""),
            f"  played by     : {top_players}",
            f"  source        : {url}",
            "",
        ]
        body = (text.get(title) or "").strip()
        if not body:
            lines += ["  (no extract returned)", ""]
            continue
        excerpt = body[: args.chars]
        if len(body) > args.chars:
            excerpt += " […]"
        lines += ["  " + line for line in excerpt.splitlines()]
        lines.append("")

    out = args.out / "opening-ideas.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
    print(f"\nwritten {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
