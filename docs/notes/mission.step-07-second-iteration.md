---
id: cas-mission-m7-iter2
title: 'M7 iteration 2 — S1 built and assessed'
desc: 'The second agent: does the architecture take a new section cleanly, and does the swarm say more than one thing?'
updated: 1785313000000
created: 1785313000000
---

# M7 iteration 2 — S1 built and assessed

**Status:** done · **Parent:** [[mission]] · **Agent:** [[capacity.agents.s1-tactical-gaps]]

The M4→M5 loop, second time round. M5's verdict on the first iteration was that the swarm asserts
**one claim kind for 16 % of players**, and that no amount of refining S2 would change it.

## Does the architecture take a new section cleanly?

**Yes, and this is the first time that claim has been tested.**
[[decisions.0006-staged-blackboard-orchestration]] asserts sections are additive and independently
ablatable. Adding S1 to the swarm was a **one-line change** to `default_agents()`. No wiring, no
ordering, no agent aware of any other, no change to the profile, the confidence policy, the
orchestrator or the CLI. The peer reference picked up S1's nine new claim keys automatically,
because it is keyed on claim identity and knows nothing about chess.

One genuine refactor fell out: the eligibility rules — skip the opening, skip decided positions —
moved from S2 into `sections/base.diagnosable()`, since both sections need identical semantics and
two copies would have drifted.

## Does the swarm say more than one thing?

| | before S1 | **after S1** |
|---|---|---|
| players with a finding (of 38) | 6 (16 %) | **9 (24 %)** |
| distinct claim kinds | **1** | **6** |
| silent / insufficient | 28 / 4 | 25 / 4 |

Claim kinds now in use: `long_think_error` (6), `allowed_motif.pin` (4), `missed_motif.pin`,
`missed_motif.discoveredAttack`, `allowed_motif.hangingPiece`, `allowed_motif.trappedPiece`.

**The first real coaching profile appeared.** `Gaurishb` carries three distinct, separately evidenced
weaknesses — misses pins, concedes trapped pieces, errs after long thinks — each peer-compared and
each traceable to sampled positions. That is a different kind of object from anything this project
has produced before.

## The defect assessment found

The first run flagged **11 allowed-motif findings against 2 missed-motif**, and several players
carried *multiple* allowed findings at once: `Gaurishb` two, `LHA-AllAboutTactics` two,
`sumang_blacksuit` two. That pattern is the tell. Being punished by every motif at once is not a
pattern-specific weakness — it is **erring more often**.

The cause was the denominator. `allowed_motif` was measured over *all moves*, so it tracked the
player's overall error rate: err twice as often and every allowed-motif rate doubles together.

Fixed by conditioning on having erred — the denominator is now the player's **errors**, which asks
the pattern-specific question instead: *when you go wrong, what punishes you?* Population rates moved
from 0.3–1.2 % to 1.9–10.1 %, and the multi-allowed pattern disappeared: `sumang_blacksuit` dropped
out entirely, `LHA` kept only its long-think finding, `Gaurishb` went from two allowed findings to
one.

This is L-014, and it is a close relative of L-011: the same claim can be a real diagnosis or a
restatement of something duller, and which one it is depends entirely on what it is divided by.

## What the peer reference now shows

Miss rates across 38 players order themselves the way a chess player would expect, which is a useful
independent sanity check on the detectors:

| Motif | Missed when available |
|---|---|
| hanging piece | **4.5 %** — a free piece is rarely overlooked |
| capturing the defender | 8.9 % |
| pin | 12.1 % |
| skewer | 15.4 % |
| discovered attack | 19.5 % |
| fork | 19.7 % |
| trapped piece | **23.8 %** — hardest to see |

## Honest limitations

- **`missed_motif` rarely clears the confidence gate.** Denominators are small — 130 skewer
  opportunities across all 38 players, roughly three per player — so most motifs can never reach
  `focus` for an individual. Only pin and discovered attack did. This is a structural consequence of
  measuring per opportunity, and it is the right trade: the alternative overstates.
- Still nothing distinguishes *knowledge* from *skill*; S1 reports `gap_type: unknown` by design,
  and closing it needs V9 probes.
- Detector precision rests on E04's hand-checks, which covered pin and skewer thoroughly and four
  other motifs not at all.

## Working log

| Date | Activity | Outcome |
|---|---|---|
| 2026-07-31 | Built S1 on the E04 detectors; registered it; rebuilt the peer reference; ran 38 players; found and fixed the allowed-motif denominator | 9/38 players, 6 claim kinds; ADR-0006's additivity claim tested and held |
