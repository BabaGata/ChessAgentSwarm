---
id: cas-adr-0005
title: 'ADR-0005 — Scope: 1400–1800 band, Lichess first, online-only'
desc: 'The three scope decisions that gate M2 and M3: target strength band, game source, and exclusion of over-the-board play.'
updated: 1785255300000
created: 1785255300000
---

# ADR-0005 — Scope: 1400–1800 band, Lichess first, online-only

**Date:** 2026-07-28 · **Status:** accepted (thesis author, taking the recommendations)

Resolves **B1**, **B2**, **B3** in [[open-questions]].

## B1 — Target strength band: 1400–1800

### Context
Coaching a 900 and coaching a 2100 are different problems ([[domain.chess-concepts]] § D). Building
for "all players" means building for none, and the evaluation set has to come from somewhere.

### Decision
The first end-to-end slice targets **1400–1800**.

### Why this band
- It is where sources agree losses stop being generic blunders and start being **individual
  recurring weaknesses** — which is precisely where personalised diagnosis beats generic advice, and
  therefore where this system's central claim is testable.
- Below ~1200 the honest advice is largely band-generic ("stop hanging pieces, check opponent
  threats"), which a static document could deliver; a swarm would be over-engineering.
- Above ~2000 useful coaching depends on deep opening preparation and specific structural knowledge,
  where a free system with no paid corpus (C7) cannot compete.
- Practical: this band is abundant on Lichess, so evaluation samples are easy to draw. The E01
  sample was drawn from it already (players rated 1489–1788).

### Consequences
- M2 orders sections by what binds *in this band*, not in general.
- The evaluation set is drawn from it, and claims are scoped to it in the thesis.
- Generalising to other bands becomes future work, not a hidden assumption.

## B2 — Game source: Lichess API first

### Decision
**Lichess API** as the primary source. PGN upload as a fallback. Chess.com later, if at all.

### Why
- Free, documented, and verified working ([[open-questions]] E1, `fetch_games.py`).
- Shares an ecosystem with the two CC0 assets we depend on — the puzzle database with motif themes
  and the `chess-openings` trap/opening data — so identifiers and conventions line up.
- Rate limits are documented and modest (back off a full minute on HTTP 429).

### Consequence, already measured
Lichess returns `evals`/`accuracy` **only for games a user chose to analyse**, which for ordinary
amateur games is rare. We therefore run our own engine for everything — affordable per
[[experiments.e01-engine-throughput]]. The API is a *game source*, not an analysis source.

## B3 — Over-the-board players: out of scope

### Decision
**Online play only.** Players without a digital game record are not supported.

### Why
Without game records the entire signal layer ([[domain.signals]]) is unavailable: no engine
analysis, no clock data, no repertoire statistics. What remains is the probe dialogue alone, which is
a different and much weaker system. Supporting both would double the design for a fraction of the
evidence.

### Consequence
A stated scope limitation in the thesis, not a silent gap. Recorded in [[vision]] non-goals.
Manual PGN upload (B2's fallback) partially covers serious tournament players who record their games.

## Related, not decided here

- **B4** (report vs. conversation) — M1 already answered *both*, since the probe dialogue is
  load-bearing (V9). The remaining question is which comes first; that is an M3 design call.
- **B5** (runtime language) — effectively settled by use: Python, with `python-chess` driving
  Stockfish, is what the E01 harness already runs on.

## Revisit when

- The 1400–1800 slice works and generalisation to an adjacent band becomes the next increment; or
- Lichess rate limits or API changes make it unworkable, promoting the PGN-upload path.
