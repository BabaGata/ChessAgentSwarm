---
id: cas-design-kb-reextraction
title: 'Design — Does re-extracting the knowledge base need the agents redesigned?'
desc: 'Mostly no. The fork/skewer failure is the documented case the naming gate was built to stop, and the stored data simply predates it: re-running rejects six of fourteen. Two things re-running will not fix — a gate that tests word presence rather than aboutness, and a shelf that does not contain the definitions being looked for.'
updated: 1788692400000
created: 1788692400000
---

# Design — Does re-extraction need an agent redesign?

**Answers:** the author's question after [[experiments.e86-detector-audit]] ·
**Status:** analysis, **no code changed**

## The short answer

**Mostly no — but re-running alone will not be enough, and for a reason that is not about the
agents.** Three separate things are tangled together in the fourteen bad entries.

## 1. The worst failure is already fixed. The data is just older than the fix.

Every entry in `data/knowledge.json` is stamped `checked_on: 2026-08-30`. The naming gate was
tightened **2026-09-01**. Re-running today's code against today's gate rejects **6 of the 14**,
including `fork`.

And the fork case is not merely fixed — it is **the case the gate was written for**. The comment
sitting directly above it in `knowledge_swarm.py`:

> *"**A definition of the wrong thing is not a definition.** A page about chess tactics defines
> several of them, and asked for `fork` the judge returned 'a skewer happens when a chess piece
> attacks an opponent's chessman, which hides a less important piece behind it' — a correct
> definition, verbatim, of a different tactic. The page was relevant and the sentence was a
> definition; only the subject was wrong, which no filter upstream of here can see."*

That is, verbatim, the entry now stored under `fork`. **No redesign is needed for this class**; the
artefact on disk is stale, and nothing was endorsed (`reviewed: False` throughout), so nothing wrong
ever reached a player.

| | |
|---|--:|
| entries | 14 |
| would be **rejected** by today's gate | **6** — `fork`, `allows_square`, `capturingDefender`, `repeat_move`, `slow_development`, `trappedPiece` |
| still pass | 8 |

## 2. What re-running will not fix: word presence is not aboutness

`_names(sentence, key)` asks whether the sentence contains any of the claim's distinctive vocabulary.
That is a real filter — it catches `fork` defined as a skewer, because the sentence contains neither
"fork" nor "forking" nor "double". But it is a **word-presence test**, and five of the eight
survivors pass on a single ordinary word:

| entry | passes on | what the quote actually is |
|---|---|---|
| `allows_pressure` | `king` | advancing the king in a pawn ending |
| `endgame_error` | `king` | the same passage again |
| `late_castling` | `king` | the rule about a player moving into check |
| `long_think_error` | `time` | a rule about complaining over an opponent's clock |
| `hangingPawn` | `pawn`, `pawns` | a passage about a bishop's advantage |

**This is the one place a design change is warranted, and it is small.** A discriminating test rather
than a presence test: reject a sentence that matches **another** concept's distinctive vocabulary
better than its own. The machinery exists — `all_terms` is already computed per key — so this is a
comparison across keys, not a new model and not a new agent.

It would have caught the fork case *without* relying on the word "fork" being absent, which is the
more robust version of the same guard.

**It would not have caught `allows_pressure`.** Nothing in the vocabulary of a pawn-ending passage
belongs to another claim either. That failure is the next point.

## 3. The real limit is the shelf, not the swarm

For several concepts **the definition is not in the corpus at all**, so no extractor can find it. The
module says so itself, in the `TERMS` table:

> *"tactics: the web knows these, the classical books mostly do not"*

and [[experiments.e64-chess-books]] measured `skewer` as appearing **zero times** across the shelf.
The books are public-domain classics — Capablanca, Edward Lasker, Staunton, Bird, Philidor, Young —
and they predate most of this vocabulary. Asked for a definition of "attack on the king" from a
corpus that has none, a well-behaved extractor returns the nearest passage containing the word
"king". **That is what happened, and it is the correct behaviour of a component pointed at the wrong
library.**

No amount of agent redesign fixes a missing source. This is a **C7 sourcing question**, not an
extraction question.

### And the source is already in hand

The audit that found this problem used one: **Lichess's own puzzle-theme definitions**, quoted
verbatim from [`puzzleTheme.xml`](https://raw.githubusercontent.com/lichess-org/lila/master/translation/source/puzzleTheme.xml)
(lichess-org/lila, AGPL — free, C7). They are precise, they define every tactical motif the project
detects, and they are authored by the project **whose keys `tactics.py` deliberately uses**.

For the nine tactical motifs, that is a better base than anything extraction will recover from
Philidor, and it needs no model at all — the definitions can be seeded directly, with the source
recorded, evidence class **expert-consensus**.

The positional concepts (`isolated`, `backward`, `doubled`, `outpost`) are the opposite case: the
classical shelf **does** discuss them, and Wikipedia's articles are precise and free. Those are the
ones extraction should keep.

## What this implies for the work

| | change needed | why |
|---|---|---|
| the fork/skewer class | **none** — re-run | already fixed 2026-09-01; the data predates it |
| the judge model | **none** | `phi4-mini:3.8b` was chosen after measuring that 3b models pick the example and it picks the definition; the recorded reason holds |
| the assessor / scout | **none found** | the audit surfaced no failure attributable to them |
| the naming gate | **small, targeted** | make it discriminating rather than presence-based: does this sentence match another concept better? |
| the tactical sources | **seed from Lichess** | the shelf does not contain these definitions; the right one is free and already used |
| empty entries | **small** | `moved_into_attack` exists with **no quote and zero sources** — an entry that reads as populated while holding nothing (L-046) |

**So: one small gate change, one sourcing decision, and a re-run.** Not a redesign of the agents.

## What this does not settle

- **Whether re-running actually produces good entries** for the eight that pass today. The prediction
  above is from reading, and the only test is running it and reading the output — which is the same
  instrument R-16 says is the only one that has ever caught this class of defect.
- **Whether the discriminating gate over-rejects.** A concept legitimately defined by contrast
  (*"a skewer is the inverse of a pin"*) names another concept on purpose. The gate must compare
  strength, not presence, and that threshold is unmeasured.
- **Endorsement is still the author's.** Nothing here changes that `reviewed: true` is set by a human,
  which is why fourteen wrong entries cost nothing but the time to find them.
