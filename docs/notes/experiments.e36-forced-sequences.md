---
id: cas-exp-e36
title: 'E36 — Nine in ten material losses need calculation, and every player is the same'
desc: 'The reviewer’s direct-versus-sequence distinction is real and striking: 88.5 % of material lost goes to a sequence, not to a piece left en prise. It separates nobody, so no claim ships — and it corrects a measurement E35 refused on broken grounds.'
updated: 1787529600000
created: 1787529600000
---

# E36 — Material lost on the square, against material lost to a sequence

**Answers:** the reviewer's second correction · **Code:** `experiments/e36-forced-sequences/` ·
**Date:** 2026-08-17 · **Status:** done — **the fact is confirmed and striking; no claim ships**

## The objection

> "Piece losses in forced couple of moves are counted the same as direct losses. Those should be
> separated because players on this level miss those in couple of moves much often and the advice for
> those should be separated as well."

The advice really does differ. Losing a piece on the square you put it on is a **counting** failure —
attackers against defenders, visible without moving anything. Losing it to a three-move sequence is a
**calculation** failure, and "count the exchange" is no use when the loss was never on one square to
count.

## First: this corrects a measurement, not only a gap

[[experiments.e35-attacking-style]] screened `delayed_material_loss`, measured a 1.20× spread, and
refused it. **That measurement was broken.** It took the *minimum* material balance across the next
three of the player's turns, which dips whenever the **opponent** starts any ordinary exchange and
the player recaptures next move. It was firing on normal trades — 31.7 % of all moves — so of course
it separated nobody. The candidate was never actually tested.

Corrected by requiring the loss to be **sustained**: still down at the player's turn three moves
later, rather than down at any point in between.

## Result — the fact is confirmed, and it is large

12 players, depth 15.

| candidate | instances | chances | pooled | median | p90 | spread | engine faults it |
|---|--:|--:|--:|--:|--:|--:|--:|
| `lost_on_the_square` | 337 | 14,951 | 2.3 % | 2.1 % | 3.2 % | 1.53× | 60 % |
| `lost_to_a_sequence` | 2,590 | 12,902 | 20.1 % | 19.8 % | 27.3 % | 1.38× | 33 % |
| **`sequence_share`** | | | **88.5 %** | 89.2 % | 90.5 % | **1.02×** | |

**Nine in ten of the material these players lose goes to a sequence, not to a piece left en prise.**
The reviewer's claim that this level misses the multi-move losses "much often" is correct by a factor
of roughly eight.

## And it separates nobody

`sequence_share` runs from **81 % to 93 %** across a corpus spanning 862 rating points, for a spread
of **1.02×**. This is a property of chess at this level, not of any player in it. A claim on it
would tell all twelve the same thing, which is the failure L-024 exists to prevent.

The two absolute rates fail the other screen instead:

| | r with the overall error rate |
|---|--:|
| `lost_on_the_square` | **+0.751** |
| `lost_to_a_sequence` | **+0.838** |

Both past E10's +0.737 line. They are how often the player errs, counted a different way — the same
verdict `left_hanging` and `ignored_threat` got in E34, and for the same reason.

So `delayed_material_loss` ends up refused either way. What changed is the **grounds**: E35 refused
it for not separating players, on a measurement that was measuring trades; the corrected version
separates players a little better and is refused for restating the error rate. The conclusion held
by luck, which is not the same as holding.

**One genuine signal, pointing the wrong way for a weakness.** `sequence_share` correlates **+0.629**
with rating: stronger players lose a *higher* proportion of their material to sequences, because they
make fewer of the crude one-square blunders and what remains is proportionally more calculation. True,
explicable, and useless as a claim — improving at chess raises this number.

## Consequence — nothing ships, and one thing is worth saying out loud

No new claim. The distinction is real and the measurement is now correct; what it fails is
**personalisation**, and this project does not report facts about everybody as findings about
somebody (R-14, E25's condition 2).

**But it exposes an imbalance worth recording.** S7's material advice is currently
`moved_into_attack` and `miscounted_exchange` — both about the one-square case, which is **11.5 %**
of where material actually goes. The swarm's only causal material advice addresses the minority
failure mode. That is not wrong, and it is a long way from complete, and the reviewer's instinct that
the advice should be separated is right even though the measurement refuses to separate the players.

Closing that would need a claim about calculation *depth* rather than material — which is what S7
originally was, and what [[experiments.e10-calculation-candidates]] refused when it found the
quiet-versus-forcing contrast does not vary between players either. Two independent routes to the
same wall: **how far ahead a player sees is the hardest thing in this project to measure from games,
and both attempts have failed.** It is the strongest remaining argument for V9 — a probe can hand
someone a position and ask.

## Honest limitations

- **Twelve players**, and `sequence_share` rests on 337 direct losses against 2,590 sequence losses,
  so the ratio is well determined and the per-player spread is not.
- **Three moves is a convention**, chosen for the reviewer's "couple of moves". A longer horizon would
  attribute more to sequences and a shorter one less; the 88.5 % is not a constant of nature.
- **Material balance is not the same as material lost.** A player who is up a piece and gives back an
  exchange registers a loss here, correctly, but the game may be going fine.
- **No causal claim.** That material went during a sequence does not establish the player failed to
  calculate it; they may have seen it and had nothing better.
