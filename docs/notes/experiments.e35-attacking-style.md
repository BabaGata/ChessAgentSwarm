---
id: cas-exp-e35
title: 'E35 — Splitting sacrifice from miscount, on the reviewer’s distinction'
desc: 'A chess distinction the first version of S7 collapsed. Separating material given up at the king from an exchange that did not add up raised the spread of both halves above the combined claim.'
updated: 1787443200000
created: 1787443200000
---

# E35 — Is "plays for the attack and pays for it" a measurable claim?

**Answers:** the reviewer's correction to E34 · **Code:** `experiments/e35-attacking-style/` ·
**Date:** 2026-08-17 · **Status:** done — **2 of 4, and the split improved what already shipped**

## The correction

E34 shipped one claim over every material-losing capture and named it
`miscounted_exchange`. The reviewer objected on chess grounds:

> "miscounted_exchange and sacrifices should be counted differently. A sacrifice is when a player
> deliberately gives a stronger piece for a weaker piece to make opening for attack which is usually
> on the king... something like taking a pawn with a bishop on the kings castle or rook for a
> defending knight. Those are usually direct material losses while miscalculated exchange can be
> usually seen after 2 or 3 moves. ... goydorak is a player who likes to attack and is willing to
> sacrifice material just to get an opportunity to attack. And because of forcing attacks that are
> not good he looses games often. Besides sacrificing, sometimes he does not take free pawn on the
> opposite side just to go with his pieces towards the king."

The objection matters because the **advice** differs completely. Telling an attacking player they
"miscount exchanges" prescribes counting to someone who counted and accepted the cost on purpose —
the same shape of error as telling a player to work on time pressure they already handle well
([[decisions.0010-three-priorities-and-the-cost-pool]] amendment).

Four candidates, all from the reviewer's own distinctions:

| candidate | |
|---|---|
| `sacrificed_for_attack` | material given up **on or within two squares of** the enemy king |
| `miscounted_away_from_king` | the same loss with no attacking idea behind it |
| `declined_material` | free material on offer, went for the king instead |
| `delayed_material_loss` | the swap looked fine and the material went within three moves |

## Result

12 players, depth 15.

| candidate | instances | chances | pooled | median | p90 | **spread** | r with error rate |
|---|--:|--:|--:|--:|--:|--:|--:|
| **`sacrificed_for_attack`** | 40 | 3,765 | 1.1 % | 0.9 % | 2.3 % | **2.71×** | **+0.208** |
| **`miscounted_away_from_king`** | 57 | 3,765 | 1.5 % | 1.3 % | 2.4 % | **1.84×** | **−0.060** |
| `declined_material` | 534 | 923 | 57.9 % | 57.6 % | 69.0 % | 1.20× | +0.337 |
| `delayed_material_loss` | 4,626 | 14,614 | 31.7 % | 31.7 % | 38.1 % | 1.20× | +0.604 |

**The split sharpened both halves.** The combined `miscounted_exchange` spread 1.75×; separated, the
two parts spread **2.71×** and **1.84×**, and `sacrificed_for_attack` is the widest spread measured
anywhere in this project. A domain distinction improving a measurement is not the usual direction —
usually the screen removes things.

`miscounted_away_from_king` at **−0.060** is also the cleanest independence figure yet recorded:
whatever it measures, it is not how often the player errs.

**`goydorak` tops both lists**, at 2.3 % sacrifices (second of twelve) and 2.8 % away-from-king
miscounts (first). The reviewer's reading of that player is confirmed twice over from different
directions.

## The two refusals

**`declined_material` fires on 57.9 % of the positions where free material is available.** Passing up
material is what players do most of the time, for every reason including good ones, and the spread of
1.20× sits below the zone where E09's candidates were refused. The reviewer's observation about
`goydorak` is real — they decline at 59.1 % — but almost everyone is between 50 % and 70 %, so it
cannot select anyone's priority (L-024).

**`delayed_material_loss` fires on a third of all quiet moves and separates nobody** (1.20×), while
drifting toward the error rate at +0.604. Losing material within three moves after a fine-looking
swap turns out to be an ordinary feature of amateur chess rather than a distinguishable habit. This
was the reviewer's *"can usually be seen after 2 or 3 moves"* made literal, and the literal version
does not survive.

## Consequence

S7 goes from two claims to three:

| claim | what it says |
|---|---|
| `moved_into_attack` | the piece you just moved can be won |
| `miscounted_exchange` | **now away-from-king only** — an exchange that did not add up |
| `sacrificed_for_attack` | material given up to get at the enemy king |

`miscounted_exchange` keeps its key and changes its meaning, so **its peer rates are not comparable
across the change** and the reference was rebuilt — the same rule E01 sets for depths.

**The sacrifice claim carries no verdict.** 57 % of these are moves the engine faults and 43 % are
not, so calling them mistakes would be wrong for two in five. The report states the rate and the
cost, and the cost line is what tells the player whether theirs are working. The planner likewise
refuses to say "stop sacrificing" — it asks the player to name the follow-up before committing the
material, on the grounds that an attack you cannot describe in one sentence is a hope rather than a
plan.

## What it actually says about `goydorak`

The player the correction came from, measured against the rebuilt reference:

| claim | rate | peers | CI95 lower | tier |
|---|--:|--:|--:|---|
| `miscounted_exchange` (away from king) | **2.85 %** | 1.59 % | 1.60 % | **focus** — asserted |
| `sacrificed_for_attack` | **2.33 %** | 1.69 % | **1.23 %** | `watch` — not asserted |
| `moved_into_attack` | 10.42 % | 11.19 % | — | silent, below the population |

**The sacrifice claim is real and cannot be asserted.** Nine sacrifices in 386 captures is 1.38× the
population and the Wilson interval reaches down to 1.23 %, below the peer rate, so the significance
test refuses it. It falls to `watch`, enters the cost pool, and is outranked there by three claims
with more evidence behind them. `goydorak`'s printed priorities are the away-from-king miscounts,
going wrong while already better, and conceding hanging pieces.

So the reviewer and the swarm disagree about `goydorak` in the same shape as they disagreed about
`bernes`: the reviewer reads **salience** — the sacrifices are what the games feel like — and the
swarm reads **measured excess and cost**, where nine events cannot outrank claims resting on fifty.
Recorded as a criterion-2 result, not tuned away.

Worth noting that the reviewer's fuller description — *"because of forcing attacks that are not good
he looses games often"* — may be showing up in the swarm's **second** priority rather than nowhere:
`advantage_error`, going wrong more often than most when already better, is what an unsound attack
from a good position looks like in the error record.

## Honest limitations

- **Thin.** 40 and 57 instances across twelve players, roughly 3–5 each. The confidence policy wants
  5 distinct games for `focus` and 8 for `priority`, so both will stay silent for most players and
  speak only for the ones who really do it — which is the correct behaviour and also means the
  spreads rest on very few events.
- **The radius is a convention.** Two squares from the king was chosen to cover a bishop on h7 and a
  rook taking a defender on f6, and it was not tuned. A different radius would move both rates.
- **Soundness is deliberately not asked**, so a player whose sacrifices all work scores the same as
  one whose never do. Conditioning on the engine faulting the move was measured and is worse: r rises
  from +0.125 to +0.682 (E34 follow-up), because "was it an error" is the error rate.
- **`declined_material` may be refused as formulated rather than as an idea.** Restricting it to
  material worth a piece or more, or to positions where the attack demonstrably went nowhere, might
  separate players where the blunt version cannot.
