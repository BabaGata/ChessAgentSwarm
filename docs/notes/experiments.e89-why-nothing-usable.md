---
id: cas-exp-e89
title: 'E89 — Preparing the extraction agents: six defects between a good page and a stored definition'
desc: 'Re-drafting three concepts produced nothing at all, and none of it was the naming gate. The queries were never asked plainly, so the search returned the Turochamp article for undefended pawn; page markup reached the output as a definition; an existential There was read as a connective; and the scout took a random three of a varying result list.'
updated: 1788710400000
created: 1788710400000
---

# E89 — What stands between a good page and a stored definition

**Answers:** the *"prepare the agents"* half of the author's regeneration request ·
**Code:** `experiments/e89-why-nothing-usable/`, `chesscoach/knowledge_swarm.py` ·
**Date:** 2026-09-06 · **Status:** six defects fixed, two concepts still unresolved

## The starting point

With the gate fixed and the tactical half seeded ([[experiments.e87-seed-lichess-themes]]),
re-drafting `hangingPawn`, `allows_square` and `late_castling` produced **nothing at all** — and none
of it was the naming gate, which never saw a sentence. Everything died earlier.

## The six defects, in the order they bite

### 1. `hangingPawn` searched for a different concept

`TERMS["hangingPawn"]` was `("hanging pawns chess", "isolated pawn", "backward pawn")`. All three name
something else. The *plural* is Steinitz's structural term — two adjacent pawns on central half-open
files — and the other two are `concedes_weakness` subjects. The claim means what Lichess's
`hangingPiece` means, one rank down: **undefended and free to capture**.

That is why the stored entry was a passage about a bishop's advantage. **Correct behaviour on a query
for the wrong thing.** Now searches `undefended pawn chess`, `hanging pawn chess`, `en prise pawn`.

### 2. The plain phrase was never asked

```python
return [f"what is a {phrases[0]}", *phrases[1:3], f"why {phrases[0]} matters"]
```

**The best phrase only ever appeared wrapped.** Measured against the local search instance:

| asked | returns |
|---|---|
| `outpost chess` | **`en.wikipedia.org/wiki/Outpost_(chess)`** |
| `what is a outpost chess` | chessmetrics.com, missiveapp.com |
| `castling in chess` | **`chess.com/terms/castling-chess`**, **`wikipedia/Castling`** |
| `what is a castling in chess` | chessvariants, jewishencyclopedia |
| `undefended pawn chess` | `wikipedia/Chess_tactic` |
| `what is a undefended pawn chess` | **`wikipedia/Turochamp`** |

The wrapping also produced ungrammatical queries — *"what is a castling in chess"* — by prefixing an
article to a phrase that does not take one. **A search engine's ranking of the exact term is the best
signal available and it was being thrown away.** Also visible: `castle early opening` returned
**kew.org's garden opening hours**.

### 3. Page markup reached the output as a definition

Re-drafting `late_castling` produced, and would have offered the author:

> *Castling is permitted provided all of the following conditions are met: `"}},"i":0}}]}'>`*

Embedded JSON from the page's own scripts, surviving text extraction and every filter, because the
prefix reads as prose. Braces and angle brackets do not occur in chess writing, so `_MARKUP` refuses
them.

### 4. An existential *"There"* was read as a connective

`_CONNECTIVE` refused any sentence opening with `there`, so *"There are two kinds of pin: absolute,
against the king, and relative…"* was thrown away before any model saw it. *"There, White plays…"* is
a connective; *"There are two kinds of…"* is one of the commonest ways a definition opens. Now
narrowed with a lookahead for a following verb.

### 5. The scout took a random three of a varying list

The search instance returns a **different ordering on each call**. Asked twice for `late_castling`
within a minute it offered `wikipedia/Castling` once and `wikipedia/1904_in_chess` the next time, and
only `read_web = 3` pages are read — so a bad draw loses the concept. That is what produced *"0
source(s) read"* for a claim whose definition was already sitting in the fetch cache.

The skiplist already calls `mark_useful` on every page that helps, so **candidates are now ordered by
whether the domain has produced usable text before**. It invents no preference where there is no
history: without a match the engine's own ranking is kept.

### 6. My own fix had the bug it was fixing

`useful = self.skiplist.useful if self.skiplist else frozenset()` — and `SkipList.__len__` counts
entries, so **a skiplist that skips nothing is falsy** while still knowing which domains helped. The
test caught it immediately. Asking an object whether it exists by asking whether it is empty is the
same shape as everything else in this file's history.

## Where the three test concepts stand

| | before | after |
|---|---|---|
| `allows_square` | nothing | **correct** — *"In chess, an outpost is a square protected by a pawn (or rarely, two pawns)…"* |
| `late_castling` | nothing | **drafts, but weak** — *"When the two-square king move is completed, however, the player is committed to castling"* is a rule about commitment, not a definition |
| `hangingPawn` | nothing | **still nothing** (2 sources read) |

**Two of three now produce something and only one of those is good.** The remaining failures are a
different kind from the six above: the pipeline reaches good pages and offers the model good
sentences, and the model picks a mediocre one. That is the judge's capability, not a defect in the
plumbing.

## Not fixed, and recorded

- **A failed fetch is cached as an empty body, permanently.**
  ```python
  except Exception:
      body = ""
  self._cache[url] = body
  ```
  Every later run reads `""` and skips the page without retrying — *"we could not fetch"* stored as
  *"this page has no text"*, which is the L-046 shape again. **15 of 85 cached pages are empty**, one
  of them a Britannica article. The `chess.com` skiplist entry says reason `no-text` and may have the
  same origin, which would mean a good definition source is permanently banned by a transient
  failure.
- **`late_castling` may not be answerable.** It is this project's jargon; there is no concept called
  "late castling" to define, and the useful entry is about castling and king safety. E65 already found
  nine of fourteen keys are jargon.
- **Precision is unmeasured.** Nothing here says what share of drafted entries are *good*; it says
  that six specific things stood in the way and no longer do.
