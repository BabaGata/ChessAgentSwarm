---
id: cas-exp-e65
title: 'E65 — Asking the masters and the web what these things are actually called'
desc: 'Nine of fourteen claim keys were this project''s jargon. Each now carries several real phrases, discovered rather than asserted: the books corrected four guesses outright ("outpost" 0 uses, "hole" 50), the web supplied the modern terms the 1900s books cannot have, and book coverage for four claims went from nothing to plenty.'
updated: 1789084800000
created: 1789084800000
---

# E65 — What these things are actually called

**Answers:** the author's *"try to find on internet the actuall phrases for these concepts and for
every concept that is being detected add multiple key words that can be used for searching"* ·
**Code:** `chesscoach/knowledge_swarm.py` (`TERMS`), `experiments/e65-real-phrases/` ·
**Date:** 2026-08-31 · **Status:** done, and it moved four claims from no book coverage to plenty

## The problem it fixes

E64 found that **nine of fourteen claim keys are this project's own jargon**. Capablanca has a
chapter on *castling*; nobody has written a definition of *"late castling"*, because it is not a
term. The knowledge base had been asking the literature to define words the literature has never
used, and E63's nine refusals were that rather than a retrieval failure.

The author's fix is smaller than restructuring: **give each claim several real phrases.**

## Discovered, not asserted

Two independent checks, because the two sources fail in opposite places.

### The books corrected four guesses outright

1.4 MB of Capablanca, Edward Lasker and Staunton, counting how often each candidate phrase appears:

| I proposed | uses | what they actually write | uses |
|---|--:|---|--:|
| "outpost" | **0** | **"hole"** | **50** |
| "trapped" | **0** | "hemmed in" / "shut in" | 5 / 3 |
| "discovered attack" | **0** | **"discovered check"** | 8 |
| "undefended piece" | **0** | **"en prise"** | 8 |

Also confirmed: `pin` 115, `development` 169, `opposition` 85, `attack on the king` 16,
`premature advance` 5, `loss of time` 4 — the classical name for what this project calls a repeated
move.

**And one claim the classical literature has no word for at all:** `capturingDefender`. Every
candidate scored zero.

### The web supplied what the books cannot have

Scored by how many returned titles actually name chess, because a phrase returning twenty pages
about something else is worse than one returning three about the right thing:

| phrase | results | naming chess |
|---|--:|--:|
| fork chess tactic | 51 | **43** |
| skewer chess tactic | 44 | **37** |
| **deflection chess tactic** | 41 | **32** |
| x-ray attack chess | 30 | 28 |
| outpost chess | 21 | **21** |
| weak square chess | 19 | 17 |

**"Deflection" is the modern name for `capturingDefender`**, the claim the books had no word for.

**Two candidates were refused on the evidence rather than on taste**: *"undermining chess tactic"*
(12 results, 2 naming chess) and *"hole chess position"* (20/6). "Hole" is the books' word and the
web's word for something else, so it stays a book term and never becomes a query.

## What changed

`TOPICS` — one invented phrase per claim — became `TERMS`, several measured phrases per claim. The
Scout asks about each; the shelf is searched with the words from all of them.

**Book coverage, before and after:**

| claim | passages found | |
|---|--:|---|
| `allows_square` | 0 → **99** | "hole" |
| `endgame_error` | 1 → **99** | "opposition" |
| `moved_into_attack` | 13 → **52** | "en prise" |
| `trappedPiece` | 0 → **16** | "hemmed in", "shut in" |

Four claims went from nothing to plenty, and none of it came from new sources — the passages were
always there, under words I had not thought to ask for.

## Consequence

- **The vocabulary is now the literature's, not ours**, and every phrase in it has a count behind it.
- **The concept/claim restructure E64 proposed may not be needed.** Its evidence was that claims found
  nothing; the cause was the words, not the structure. Whether the drafts actually improve is the
  next measurement and is not made here.
- **`capturingDefender` is the one claim with no classical name**, so it depends entirely on the web
  and on the word "deflection".

## Honest limitations

- **The candidate lists are mine.** The books and the web could only confirm or refuse what I thought
  to propose, so a term nobody suggested is still missing — the method finds bad guesses, not gaps.
- **A phrase count is not a definition.** "Opposition" appearing 85 times means the books discuss it,
  not that a usable definition of endgame technique will come out.
- **No entry has been re-drafted with the new terms yet**, so the improvement is measured in passages
  reached rather than in entries produced.
