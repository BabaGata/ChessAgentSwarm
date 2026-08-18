---
id: cas-exp-e34
title: 'E34 — Two of four causes of material loss survive, and S7 reopens'
desc: 'Why a player loses material, not what won it. Two candidates pass; two are the overall error rate under a better name, failing exactly where E10 closed S7.'
updated: 1787356800000
created: 1787356800000
---

# E34 — Do the causes of material loss earn a place in the report?

**Answers:** open question D13 · **Code:** `experiments/e34-material-causes/` ·
**Date:** 2026-08-17 · **Status:** done — **2 of 4 ship, and S7 reopens**

## The objection

The expert reviewer, mid-review:

> "Does the system evaluate the reason for why the player is losing pawns/pieces — leaving many
> undefended regularly, does the player move them to the attacked spot, does he calculate the
> exchange badly, doesn't see defending moves? This kind of information seems more valuable for the
> advice than just saying that the player is losing the material."

The swarm names **mechanism** — a fork, a pin, a hanging piece — and the author had already ruled
that mechanism beats material outcome, because *"you dropped a pawn"* names a symptom the player
watched happen ([[experiments.e33-error-threshold]]). These four candidates sit one level **below**
mechanism: not what won the material, but what the player did that made it winnable.

Each maps to a different habit, which is the entire point of preferring them to an outcome:

| candidate | the habit it names |
|---|---|
| `moved_into_attack` | check the destination square before releasing the piece |
| `miscounted_exchange` | count attackers and defenders before starting one |
| `left_hanging` | scan your own loose pieces |
| `ignored_threat` | when something is attacked, find the defence first |

`chesscoach/material.py` implements all four over **the move the player actually played** — the
first detectors in the project to read it, closing the structural gap E33 named. Static exchange
evaluation, no engine call, 1.5 ms per move: **37 seconds for the entire 12-player corpus.**

## Result — it fires and it separates players

12 players, depth 15. Spread is p90 ÷ median, the E09/E11 screen.

| candidate | instances | chances | pooled | median | p90 | **spread** |
|---|--:|--:|--:|--:|--:|--:|
| `moved_into_attack` | 1,691 | 14,951 | 11.3 % | 10.9 % | 14.8 % | **1.36×** |
| `miscounted_exchange` | 97 | 3,765 | 2.6 % | 2.3 % | 4.0 % | **1.75×** |
| `left_hanging` | 2,007 | 14,951 | 13.4 % | 12.9 % | 20.7 % | 1.61× |
| `ignored_threat` | 1,238 | 5,290 | 23.4 % | 22.1 % | 31.8 % | 1.44× |

All four clear the bar that removed E09's and E11's failures (~1.27–1.31), and sit alongside claims
already shipping — `fork` at 1.40×, `hangingPiece` at 1.56×.

**On that evidence all four would have shipped.** They do not, because of the next table.

## Result — and two of them are the error rate under another name

[[experiments.e10-calculation-candidates]] closed S7 by this test. `missed_quiet` had a respectable
1.56 spread and was refused because it correlated **+0.737** with `missed_forcing`: the players who
went wrong on quiet moves were the players who went wrong on forcing moves, so a claim built on it
restated the overall error rate more flatteringly (L-014).

| candidate | r with the player's overall error rate | |
|---|--:|---|
| `moved_into_attack` | **+0.225** | independent — ships |
| `miscounted_exchange` | **+0.123** | independent — ships |
| `left_hanging` | **+0.917** | refused |
| `ignored_threat` | **+0.914** | refused |

The refusals are obvious in hindsight and were not obvious in advance: a player who errs more often
has more loose pieces standing around and more threats left unanswered **as a consequence of erring**.
Those two rates measure error-proneness with extra steps. Both had good spreads, and one of them —
`ignored_threat`, at 23.4 % pooled with a visible rating gradient — is the most tempting number in
the whole experiment.

The rating gradient makes the point sharply. Raw correlations with rating look decisive:

| candidate | raw r with rating | after dividing out general skill |
|---|--:|--:|
| `moved_into_attack` | −0.38 | +0.51 |
| `miscounted_exchange` | −0.25 | +0.15 |
| `left_hanging` | **−0.72** | −0.16 |
| `ignored_threat` | **−0.75** | +0.15 |

−0.72 and −0.75 are the strongest rating correlations measured anywhere in this project, and they
survive dividing out general skill in no case. That is L-025 in a single table: nearly every claim
falls with rating, and nearly all of it is better players making fewer mistakes of every kind.

## What the survivors buy

3,653 labelled errors across the twelve players:

| | | |
|---|--:|--:|
| carrying a tactical **motif** (today) | 1,741 | 48 % |
| carrying any of the four **causes** | 1,172 | 32 % |
| — motif only | 900 | 25 % |
| — cause only, newly explained | 331 | 9 % |
| — both | 841 | 23 % |
| — still anonymous | 1,581 | 43 % |

**Anonymous errors fall 52 % → 43 %** with all four. With only the two survivors it is **52 % → 49 %**:
they explain 488 errors, of which 124 had no motif at all.

That is a modest coverage gain and it is not the point. For those 488 moves the report can now say
*what the player did*, which is what D13 asked for and what no motif can supply.

**One figure in the results file is worthless and is labelled so**: "of errors that cost material,
a cause explains 100 %". "Cost material" was defined as a losing exchange or material won on the
reply, which is close to the union of the cause definitions. It cannot fail and is not evidence.

## Consequence — S7 reopens

The section slot E10 emptied, refilled on a different question: not *how deeply do you calculate*
but *did you check*. `chesscoach/sections/s7_material_safety.py`, registered in `default_agents`.

Two properties are unusual and both are deliberate:

- **It reads the played move**, alone among the sections.
- **It refuses to speak without a population.** There is no within-player baseline for "was that
  square safe" — no other kind of square to compare against — so without peers the claim would be
  comparing the player against nothing. `_assess` returns None rather than falling back.

Neither claim is conditioned on the move being an error. *"You put the piece you just moved where it
can be won, on 11 % of your moves"* is a statement about a habit; conditioning it on having been
punished would make it a statement about the player's opponents. The **cost** is error-conditioned,
because a move that lost nothing cost nothing.

## Honest limitations

- **`moved_into_attack` has the weakest spread of the four, 1.36×**, close to the zone where E09's
  candidates were refused. It ships on the strength of its independence, not its separation.
- **`miscounted_exchange` is thin: 97 instances across twelve players**, about eight each. The
  confidence policy needs 5 distinct games for `focus` and 8 for `priority`, so it will rarely clear
  for a real player however well it screens.
- **Twelve players.** E25 used 84 and called 12 thin; every correlation here carries a wide interval
  and the rating figures especially should not be quoted as measurements.
- **The refusals are not permanent.** `left_hanging` and `ignored_threat` are real behaviours and
  might survive a formulation that is not a near-restatement of erring — conditioning on
  opportunities where the threat was *cheap* to answer, for instance. Refused as formulated, not as
  ideas.
- **Nothing here shows the advice works.** These name a habit and a remedy; whether the remedy
  changes the habit is D8's question and needs a coached cohort.
