"""Screen the candidate guides against the author's own three objections.

The author rejected the Wikibooks prose for three specific reasons, and those are
the criteria — not a general sense of quality:

  1. it explains **what happened** rather than what to focus on for the rest of
     the game;
  2. the sentences are not understandable at 1500;
  3. it draws conclusions from understanding the player does not have.

Each becomes something countable, so the reading afterwards starts from evidence
rather than from a first impression:

  PLAN     second-person, forward-looking language — "you should", "aim to",
           "the plan is", "break with". This is objection 1 inverted.
  JARGON   named concepts used as if already known — "Carlsbad structure",
           "IQP", "prophylaxis", "zugzwang", "compensation". Objection 3, and it
           is the one that killed the Caro-Kann entry.
  SELL     signup and course language. A page behind a funnel is not a guide.
  WORDS    article length. The Italian entry that failed was 33 words.

**A score is a shortlist, not a verdict.** Counting cannot tell whether the plans
are correct or the prose is clear; it can tell which pages are worth reading and
which are obviously stubs or storefronts.

Usage:
    python screen_guides.py [--families 10]
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e47-opening-knowledge"))

from candidates import CANDIDATES  # noqa: E402

from chesscoach.openings import OpeningBook  # noqa: E402
from chesscoach.pipeline import load_games  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"
TEXT_CACHE = Path(__file__).parent / "results" / "page-text.json"
AGENT = "ChessAgentSwarm/0.1 (thesis research; guide screening)"

PLAN = re.compile(
    r"\b(you should|you can|you want|your plan|the plan is|the idea is|aims? to|"
    r"aiming (?:for|to)|look to|try to|break with|pawn break|typical plan|"
    r"main plan|middlegame plan|where .{0,20}pieces? (?:go|belong)|"
    r"put your|develop your|castle)\b", re.I)

# Terms used across these pages as if the reader already knows them. The list is
# from the author's own complaint about the Caro-Kann entry plus the vocabulary
# that recurs in the same register.
JARGON = re.compile(
    r"\b(carlsbad|isolani|IQP|isolated queen'?s pawn|prophyla\w+|zugzwang|"
    r"zwischenzug|luft|minority attack|hypermodern|tabiya|transpos\w+|"
    r"compensation|initiative|tempo|outpost|fianchett\w+)\b", re.I)

SELL = re.compile(
    r"\b(free trial|sign up|subscribe|enroll|buy now|add to cart|\$\d|"
    r"our course|premium|membership)\b", re.I)


def article_text(body: str) -> str:
    body = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", body)
    body = re.sub(r"(?s)<[^>]+>", " ", body)
    return re.sub(r"\s+", " ", html.unescape(body)).strip()


def fetch(url: str, cache: dict) -> str:
    if url in cache:
        return cache[url]
    try:
        request = urllib.request.Request(url, headers={"User-Agent": AGENT})
        with urllib.request.urlopen(request, timeout=30) as response:
            text = article_text(response.read(400_000).decode("utf-8", "replace"))
    except Exception as error:
        text = f"__UNREADABLE__ {type(error).__name__}"
    cache[url] = text
    TEXT_CACHE.parent.mkdir(parents=True, exist_ok=True)
    TEXT_CACHE.write_text(json.dumps(cache), encoding="utf-8")
    time.sleep(1.5)
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--families", type=int, default=10)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()

    book = OpeningBook.load()
    played: Counter = Counter()
    for path in sorted(ROOT.glob("games/*.pgn")):
        for game in load_games(path)[:20]:
            walk = book.walk(list(game.moves))
            if walk.opening:
                played[walk.opening.name.split(":")[0]] += 1

    families = [f for f, _ in played.most_common() if f in CANDIDATES][: args.families]
    cache = json.loads(TEXT_CACHE.read_text(encoding="utf-8")) if TEXT_CACHE.exists() else {}

    lines = [
        "GUIDE SCREEN — the author's three objections, made countable",
        "=" * 92,
        "",
        "PLAN   forward-looking, second-person plan language (higher is better)",
        "JARGON concepts used as if already known (lower is better)",
        "SELL   signup/course language (lower is better)",
        "WORDS  article length",
        "",
        "Rates are per 1000 words so a long page is not rewarded for being long.",
        "A score is a shortlist, not a verdict.",
        "",
    ]
    rows = []
    for family in families:
        lines.append("-" * 92)
        lines.append(f"{family}  —  {played[family]} games")
        for title, url, publisher in CANDIDATES[family]:
            text = fetch(url, cache)
            if text.startswith("__UNREADABLE__"):
                lines.append(f"  {publisher:<20} UNREADABLE ({text.split()[1]})")
                continue
            words = len(text.split())
            per_k = (lambda n: 1000 * n / words if words else 0)
            plan = per_k(len(PLAN.findall(text)))
            jargon = per_k(len(JARGON.findall(text)))
            sell = len(SELL.findall(text))
            rows.append((family, publisher, url, words, plan, jargon, sell))
            flag = ""
            if words < 400:
                flag = "  <-- thin"
            elif sell >= 4:
                flag = "  <-- storefront?"
            elif plan >= 4 and jargon <= 6:
                flag = "  <-- promising"
            lines.append(
                f"  {publisher:<20}{words:>6}w  plan {plan:>5.1f}  "
                f"jargon {jargon:>5.1f}  sell {sell:>2}{flag}"
            )
        print(f"  {family}: done", flush=True)

    if rows:
        best = sorted(rows, key=lambda r: (-(r[4] - r[5] / 2), r[6]))[:12]
        lines += ["", "=" * 92, "SHORTLIST — most plan language, least assumed knowledge", ""]
        for family, publisher, url, words, plan, jargon, sell in best:
            lines.append(f"  {family:<26}{publisher:<22}plan {plan:>5.1f}  jargon {jargon:>5.1f}")
            lines.append(f"    {url}")

    out = args.out / "guide-screen.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
