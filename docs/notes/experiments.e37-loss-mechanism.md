---
id: cas-exp-e37
title: 'E37 — Inside the sequence bucket: pins beat forks, and pure forcing attacks are rare'
desc: 'Splitting E36’s 88.5 % by mechanism. Tactics take 54.7 %, exchanges 31.9 %, pure forcing sequences only 2.8 %. Pins outrank forks by 1.6 to 1. No claim survives both screens.'
updated: 1787616000000
created: 1787616000000
---

# E37 — What actually wins the material, inside the sequence bucket?

**Answers:** the reviewer's third material question · **Code:** `experiments/e37-loss-mechanism/` ·
**Date:** 2026-08-18 · **Status:** done — **the answer is descriptive; no claim ships**

## The question

[[experiments.e36-forced-sequences]] established that **88.5 %** of the material these players lose
goes to a sequence rather than to a piece left en prise, and that every player sits between 81 % and
93 %. It left the bucket undifferentiated. The reviewer:

> "I also want differentiation between the material lost in a sequence due the forks and pins, if it
> combined is all together now, due the exchange miscalculation and just pure sequence of forced
> attacks."

Three mechanisms, wanting three different kinds of training: **pattern** work, **counting** work,
**calculation** work.

Attribution is ordered — `tactic > exchange > forcing > unattributed` — because a move is often
several things. A fork delivered with check is a fork: the pattern explains it better than the check
does. *"Pure sequence of forced attacks"* is therefore the residual, forcing moves that no named
pattern accounts for, which is what the reviewer means by **pure**.

`hangingPiece` and `hangingPawn` are deliberately **not** counted as tactics here. Collecting
something already loose partway through a sequence is the sequence finishing, not a pattern the
player failed to foresee.

## Result — the composition

2,590 sequence losses, twelve players.

| mechanism | instances | share | median | p90 | spread |
|---|--:|--:|--:|--:|--:|
| **tactic** | 1,417 | **54.7 %** | 54.2 % | 62.2 % | 1.15× |
| **exchange** | 825 | **31.9 %** | 33.5 % | 38.4 % | 1.15× |
| **forcing** (pure) | 72 | **2.8 %** | 2.8 % | 5.0 % | 1.78× |
| unattributed | 276 | 10.7 % | 10.1 % | 14.0 % | 1.39× |

And inside the tactic half:

| | | |
|---|--:|--:|
| **pin** | 644 | **30.7 %** |
| capturing the defender | 508 | 24.2 % |
| **fork** | 390 | **18.6 %** |
| discovered attack | 316 | 15.0 % |
| trapped piece | 144 | 6.9 % |
| skewer | 98 | 4.7 % |

**Pins outrank forks by roughly 1.6 to 1**, which is not the order most puzzle training implies, and
**capturing the defender** — removing the guard — is second and rarely taught as a named theme at
this level.

**Pure forcing sequences are rare: 2.8 %.** The reviewer's third category is real and it is the
smallest of the three by an order of magnitude. Most material that goes "in a couple of moves" goes
to a pattern with a name, not to an unnamed cascade of checks.

## Screens — nothing survives both

As per-move rates, the shape a claim would take:

| candidate | pooled | spread | r with the overall error rate |
|---|--:|--:|--:|
| tactic | 9.5 % | **1.68×** | **+0.910** — restates it |
| exchange | 5.5 % | 1.17× | −0.372 |
| forcing | 0.5 % | **1.76×** | +0.307 |
| unattributed | 1.8 % | 1.52× | +0.410 |

- **`tactic` separates players well and is the error rate again** (+0.910), joining `left_hanging`
  and `ignored_threat` in E34 and both of E36's candidates. A player who errs more gets punished by
  tactics more, as a consequence.
- **`exchange` is cleanly independent (−0.372) and separates nobody** (1.17×, below the zone where
  E09's candidates were refused). Everyone loses about a third of their sequence material to
  exchanges resolving badly.
- **`forcing` passes both screens** — 1.76× spread, +0.307 independence — and is **too thin to
  assert**: 72 instances across twelve players, six each, on which no Wilson interval will ever clear
  a peer rate. Shipping it would add a claim that can never fire.
- The composition shares fare no better: the two large buckets sit at **1.15×**, meaning players
  differ in *how much* material they lose far more than in *what takes it*.

## Consequence

**No new claim.** The distinction is real, the numbers are now known, and what fails is
personalisation — the same verdict as E36 and for a related reason.

**But most of the largest bucket is already reported.** S1's `allowed_motif` claims already say *"when
you go wrong, it is often a pin that punishes you"*, and the 54.7 % tactic share is largely those
same events seen over a wider window. The reviewer's question therefore has a reassuring answer: the
biggest mechanism inside the sequence bucket is **not** a blind spot, it is the part the swarm has
been naming since S1 shipped.

What is genuinely unreported is the **31.9 % exchange** share — material lost through captures
resolving badly across several moves, which `miscounted_exchange` cannot see because that claim reads
the immediate swap on one square. It is unreportable for now: independent, but identical across
players.

## Honest limitations

- **Attribution is ordered, and the order is a judgement.** Counting a checking fork as *forcing*
  rather than *tactic* would move perhaps a fifth of the tactic bucket. The order is stated so it can
  be argued with, not because it is derived.
- **The window is three of the player's moves**, inherited from E36. A longer window would attribute
  more to tactics simply by including more opponent moves.
- **`unattributed` at 10.7 % is a real gap, not a rounding error.** Material went, no pattern fired,
  no square saw a repeat capture, no check was given. Some of that is positional loss — a piece
  trapped slowly, a fortress collapsing — that none of these detectors represent.
- **Twelve players**, and the per-player composition rests on 105–335 losses each, so the shares are
  well determined and the spreads across players are not.
