---
id: cas-exp-e15
title: 'E15 — Ranking by what a weakness costs'
desc: 'E03 asked whether a feature predicts errors and failed. Asking instead what the known errors cost changed the advice for 33 of 84 players without collapsing it.'
updated: 1786492800000
created: 1786492800000
---

# E15 — Ranking by what a weakness costs

**Answers:** [[state]]'s P1 (D5 expected-gain reasoning) · **Date:** 2026-08-06 · **Status:** done —
**built, with a stated ceiling**

## Question

The arbiter chose priorities by how *unusual* a weakness was. *"You do this 1.8× more than your
peers"* is a reason to find something interesting; it is not a reason to spend a month on it. V5 asks
for prioritisation by **expected gain**, and that was the last structural gap in it.

## Why this is not E03 again

[[experiments.e03-relevance-weighting]] asked a **predictive** question — *does feature X predict
errors?* — and did not find the link. The obvious reading was that expected gain is out of reach.

That reading confuses two questions:

| | question | needs |
|---|---|---|
| E03 | will this feature *predict* mistakes? | a model that generalises |
| **E15** | for instances **already identified** as mistakes, how much was given away *on those moves*? | a sum |

The second is **accounting, not prediction.** Every diagnosable observation already carries
`loss_wp`, the win probability the move gave away. A claim's cost is the sum of that over its own
instances. Nothing is forecast, and the answer is arithmetic over evidence the profile already holds.

## Method

`Measurement.cost_wp` — total win probability given away on this claim's instances (schema v9) —
with `cost_per_game = cost_wp / games_with_data`.

**Populated only where the instances are mistakes.** S1 (missed and allowed motifs), S2 (all three
conditions), S3 (all), and S4's `early_error`. Left `None` in S5, S6, S8 and S4's
`opening_disadvantage`: conceding an isolated pawn, letting a rook reach the seventh, or emerging
from the opening worse are *choices and outcomes*, not moves that lost a measurable amount. Putting a
number on them would invent the very cost E03 failed to find.

The arbiter's ordering became: **confidence → can it state a cost → the cost → how unusual → games**.
So a claim that can price itself outranks one that cannot, and the unpriced claims still rank among
themselves by deviation.

Measured by rebuilding all 84 deep profiles and diffing the advice against the pre-D5 run.

## Result — it changes the advice

| | |
|---|---|
| players compared | 84 |
| **advice changed** | **33 (39 %)** |
| newly advised | 0 |
| no longer advised | 0 |
| median cost of an advised finding | **8.8 wp/game** (range 1.3 – 37.3) |
| advised findings with no priceable cost | 20 of 93 |

Coverage is untouched — this reorders what players hear, it does not change whether they hear
anything.

## Result — it did not collapse the swarm

A cost is a sum, so the claim with the widest net accumulates the most. The failure mode was that
every player ends up hearing about the same thing.

| | before | after |
|---|:--:|:--:|
| distinct claim kinds advised | 11 | **11** |
| sections reaching a player | 7 | **7** |
| most common single advice | 27 % of players | **30 %** |
| distinct claim *keys* (E08 D1) | 27 | **26** |
| mean pairwise overlap (E08 D1) | 0.05 | **0.06** |
| groundedness (E08 D4) | 113/113 | **113/113** |
| priorities per player (E08 D3) | never > 2 | never > 2 |

**It concentrates the advice slightly** — one claim key fewer and overlap up a hundredth. That is the
price of ranking by a quantity many claims share, and it is small enough to pay; it is recorded
because a metric that only moved favourably would not be measuring anything.

The movements are the intended ones:

| claim kind | before | after | |
|---|:--:|:--:|---|
| `S3 advantage_error` | 1 | **9** | throwing away winning positions is the most expensive thing a player does, and it was nearly invisible under deviation ranking |
| `S4 early_error` | 15 | 21 | |
| `S2 long_think_error` | 4 | 8 | |
| `S4 opening_disadvantage` | 11 | **4** | it counts outcomes, not mistakes — it cannot price itself and lost slots to claims that can |
| `S1 missed_motif` | 15 | 9 | |
| `S3 endgame_error` | 19 | 14 | |

`advantage_error` rising and `opening_disadvantage` falling is the whole change in miniature: the
first is a mistake with a measurable price, the second is a result.

## Honest limitations

- **It is a ceiling, not a forecast.** The report says *"the most you could get back by stopping
  them"* because nobody stops making all of their mistakes. Nothing here estimates what a player
  *will* gain.
- **Costs are not additive across claims.** One blunder under time pressure in a rook endgame is an
  instance of an S2 claim *and* an S3 one. Ranking claims against each other is valid; adding their
  costs is not, and the system never does.
- **A game can register more than 100 points.** Win probability is given away repeatedly and handed
  back by the opponent, so the figure is a total of give-aways, not a share of one result.
- **No causal claim.** Nothing shows that a player who fixes the priciest weakness gains more rating
  than one who fixes another. That is the progress check's territory ([[experiments.e06-progress-power]])
  and it is untested. This is expected gain in the accounting sense only.
- **Unpriced claims are ranked below priced ones by policy, not by measurement.** It is a defensible
  policy — S5's design note argued for it before it was measurable — but it is a choice, and it costs
  the positional sections slots they previously won.
- **The engine's win probability is the unit of value**, at depth 15, and everything inherits
  whatever that model gets wrong.
