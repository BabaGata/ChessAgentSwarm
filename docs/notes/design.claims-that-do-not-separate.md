---
id: cas-design-separation
title: 'Design — What to do with a claim that does not separate players'
desc: 'Two changes. A claim that cannot distinguish players stops carrying a peer comparison and is ranked on cost alone; and allowed_motif gets a motif-specific denominator instead of dividing every motif by the same total-error count.'
updated: 1788577200000
created: 1788577200000
---

# Design — Claims that do not separate players

**Serves:** V8 (no unfalsifiable coaching), C1 (free) · **Answers:** the P1 opened by
[[experiments.e83-spread-rescreen]] · **Status:** design, being built

## The problem

[[experiments.e83-spread-rescreen]] found **nine asserted claims where players are statistically
interchangeable**, and showed the finding is real rather than underpowered: eight would have revealed
a difference as small as **1.12–1.25×** and revealed none.

The peer comparison asserts *"you do this more than your peers"*. That sentence needs players to
actually differ. `allowed_motif.fork` sits at 3.3 % across 83 players with ~248 errors each; if every
player's true rate were exactly 3.3 %, measured rates would still scatter roughly 2–5 % by chance
alone. Somebody lands in the top decile, gets told they are fork-prone, and is average next month.

**The author's instruction is that nothing is retired.** These detectors keep running and keep
producing evidence. What changes is what may be *said* about the result.

## D1 — A claim that cannot distinguish players makes no comparison between them

`sections/base.peer_rate()` is the single chokepoint: every downstream site — arbiter, planner,
explainer, cli — already branches on `peer_rate is not None` and falls back. Returning `None` there
for a non-separating claim removes the comparative sentence without touching detection.

The arbiter's own docstring already says a missing peer rate *"is not evidence of being better than
average, so it passes"*, so **the claim is still ranked, on cost**. That is exactly the wanted
behaviour: *"a fork cost you 47 wp across these three games"* is falsifiable from the player's own
games (V8) and needs no separation to be true.

**One catch.** `arbiter._unusualness` falls back to `lift_vs_baseline` when `lift_vs_peer` is absent,
and its docstring already warns this *"overstates by however much the behaviour is universal
(L-012)"*. For these claims the behaviour **is** universal, so the fallback would hand them unearned
rank. They therefore get unusualness **1.0 — neutral**, and compete on cost only.

`lift_vs_baseline` is a *within-player* comparison (this motif against that player's other motifs)
and E83 says nothing against it, so it is not removed from the report — only from ranking, where it
would be doing the job the peer comparison is no longer allowed to do.

### Done when

- `separation.separates(claim_key)` answers for every claim, from stored E83 evidence, and
  canonicalises keys the way `PeerReference` does.
- `peer_rate()` returns `None` for the nine, with the reference untouched.
- `_unusualness()` returns 1.0 for them.
- No report sentence compares one of them to peers. Tests cover all three.

## D2 — `allowed_motif` gets a motif-specific denominator

The asymmetry is in `s1_tactical_gaps` today:

| claim | denominator |
|---|---|
| `missed_motif.X`, `executed_motif.X` | positions where **X** was available |
| `allowed_motif.X` | **the player's total errors**, identical for every X |

The existing comment defends dividing by errors rather than by *moves*, and that argument is right —
it stops weak players lighting up for every motif at once. But it does not go far enough: every motif
still shares one denominator, so a player who never reaches back-rank-vulnerable structures is scored
against the same base as one who lives in them. The claim currently reads *"what share of your
mistakes this motif punishes"*, which is largely a property of the positions and the opponent.

**New denominator: errors in positions where the motif was available to the opponent** — that is,
where *some* legal reply executes it. The numerator is unchanged: the opponent's *best* reply
executed it. The claim becomes *"when a fork was on the board after your error, how often did it
actually punish you"*, which is sharper, coachable, and motif-specific.

Availability is defined by the existing `detect_motifs` over legal moves, so **no new chess claim is
invented** and nothing needs a source it does not have (R-03).

**Cost:** measured at **10.5 ms per position**, ~20,600 error positions in the reference corpus →
**under 4 minutes**, deterministic, no engine and no model. C1 holds.

### Done when

- `allowed_motif.X` opportunities count only errors where X was available.
- `instances <= opportunities` holds per motif, and is tested.
- A position offering no fork contributes nothing to `allowed_motif.fork`'s denominator.
- The peer reference is rebuilt, and E83's screen is re-run on the result.

## What this forecloses

- **The peer reference must be rebuilt** for D2 — old cells carry the old denominator, and mixing
  them would compare a rate to a differently-defined rate (L-046).
- **Rates for `allowed_motif` will rise**, since the denominator shrinks. Any recorded threshold or
  figure quoting those rates becomes stale and must be re-derived, not carried over.
- D1's list is **evidence, not opinion**, and it must be regenerated when the reference is rebuilt.
  Two of the nine (`skewer`, `backRankMate`) failed at wider MDEs, so D2 may return them.

## Explicitly not decided here

Whether any claim is retired. The author's instruction is that none are, and nothing in this design
removes a detector; D1 removes only a sentence, and D2 changes an arithmetic definition.
