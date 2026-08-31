---
id: cas-exp-e70
title: 'E70 — maikel5 is not silent, he is in the wrong population'
desc: 'The author guessed that peer-relative ranking starves strong players of recommendations. It does, and the immediate cause is sharper: half the review corpus is outside the band it was compared against, because the band arm of the peer key was never checked while the speed arm always was.'
updated: 1788193800000
created: 1788174000000
---

# E70 — Who is being compared against a population they are not in

> **Corrected 2026-08-31 by [[experiments.e71-why-the-pool-was-empty]]**, which ran the engine pass
> this note could not. **Both inferred claims were confirmed exactly.** Two things here were wrong:
> the correlation is **−0.79**, not −0.88 (this note counted from E55's sheet-build log rather than
> from a diagnosis), and **the cost pool does not fail the way the section below implies** — it
> delivers a full three priorities to 9 of 12 players, and maikel5 is the only player at zero. The
> band finding itself stands.


**Answers:** the P0 open item *"`maikel5` has no priorities at all"* ·
**Code:** `experiments/e70-band-mismatch/` · **Date:** 2026-08-31 ·
**Status:** done — **the guess was right, the cause was one level deeper**

## The question

The author, reading the silence:

> *"my guess is that he is one of the better players with higher rating and that he just doesn't
> make mistakes as often as others. For 1 player this was an issue before because the priorities are
> measured against the peers to see what mistakes the player make more often then peers, but this
> also removes recommendation options for those with higher ranks."*

Both halves are correct. The mechanism, though, is not only that the ranking is peer-relative — it
is that **the peers were never checked to be peers**.

## What was measured

**No engine pass.** The ratings are in the PGN headers and the finding counts are in E55's
sheet-build log. Everything below was already written down; nothing had ever been joined.

| player | Elo | where | asserted | measured |
|---|--:|---|--:|--:|
| Sheriwoyama | 1994 | **above** | **0** | 6 |
| Odin5306 | 1985 | **above** | **0** | 2 |
| maikel5 | 1929 | **above** | **0** | 2 |
| bjagus | 1860 | **above** | 1 | 7 |
| simonvj | 1775 | inside | 0 | 9 |
| maxhayastan | 1750 | inside | 0 | 2 |
| Crossfire1983 | 1642 | inside | 2 | 7 |
| bernes | 1624 | inside | 1 | 5 |
| goydorak | 1580 | inside | 1 | 8 |
| Hirsican | 1529 | inside | 1 | 11 |
| cademan | 1302 | **below** | **5** | 10 |
| Maximilian_Honigtopf | 1202 | **below** | **6** | 6 |

**r(rating, asserted findings) = −0.88** as counted here from the sheet-build log — **−0.79 when measured directly** ([[experiments.e71-why-the-pool-was-empty]]). The gradient is monotone either way, in the thing that should not be driving it:

| where the player sits | n | asserted findings | mean |
|---|--:|---|--:|
| above the band | 4 | 0, 0, 0, 1 | **0.2** |
| inside it | 6 | 0, 0, 1, 1, 1, 2 | 0.8 |
| below it | 2 | 5, 6 | **5.5** |

## The cause

A peer lookup is keyed on `(band, time_control, claim)`. **The speed arm has been checked against
the games since the stratum guard was written. The band arm never was.** `--band` defaults to
`1400-1800`, and nothing compared that string to who the player actually is — so **6 of the 12
review players were diagnosed against a band they are not in**, four above and two below.

There was also nowhere else for them to go: the reference has **exactly one stratum**. No population
above 1800 or below 1400 exists to compare anyone against.

So maikel5's silence is not a statement about maikel5. It is the output of comparing a 1929 player
against players rated 1400–1800 and finding, correctly, that he does nothing unusually often. **The
report renders that as "nothing in your games is unusual for your rating band", which is a sentence
about a band he is not in.**

**The two below-band players are the same defect with the sign flipped**, and they are what makes
this a mechanism rather than a story about strong players: cademan (1302) and
Maximilian_Honigtopf (1202) get **5 and 6 asserted findings**, far more than anyone else. They are
not worse than the others in proportion to that. They are being compared upward.

## Why the cost pool did not save it

[[decisions.0010-three-priorities-and-the-cost-pool]] exists for exactly the author's concern: when
nothing is unusual, fill the slots by what a pattern costs outright. It took silence from 2/12 to
0/12 and it is the reason maikel5's **earlier** report had three priorities, every one labelled
*"Ordinary for your level"*.

It could not fire **for maikel5**, and the reason is worth recording because it is not the peer
comparison at all. **It fires for nearly everyone else**: 9 of 12 players get a full three
priorities, and the band gradient that is stark in the asserted column is largely absorbed by the
time anything reaches a player ([[experiments.e71-why-the-pool-was-empty]]). The failure is narrower
than "peer-relative ranking starves strong players" — it is that the fallback needs **one priceable
claim costing more than the reference population**, and a player compared against a weaker
population may have none. maikel5 has two measured claims:

- **`concedes_weakness.backward`** — every instance costs **0.0 wp**, because the section
  *structurally cannot price itself*: conceding a pawn structure is a choice, not a mistake. It can
  never enter the cost pool by design.
- **`time_pressure_error.clock`** — priced, and it falls below the peer rate without being
  exposure-driven, so `_worth_a_slot` filters it.

One unpriceable claim and one filtered claim leaves an empty pool. **The fallback needs a candidate,
and being outside the band removes the candidates before the fallback is reached.**

## Consequence

- **Built: `declared_band_is_wrong`**, the sibling `declared_speed_is_wrong` should always have had,
  wired into `build-peer-reference` so a reference can no longer be built from players who are not
  in the band it is filed under. 17 tests. It refuses 6 of the 12 review players today.
- **The median decides, not a purity share.** Purity is right for a categorical label like speed and
  wrong for a continuous one — a rating wanders, and demanding 90 % of games inside a band would
  refuse everyone near an edge. `BAND_EDGE_TOLERANCE = 50` covers drift and is a named constant
  because where a band ends is the author's judgement.
- **The read side is not fixed and needs a decision** — see the open question below.

## Honest limitations

- ~~**The two claims named above are inferred**, not observed.~~ **Confirmed 2026-08-31** by an
  engine pass ([[experiments.e71-why-the-pool-was-empty]]): both claims are exactly the two named,
  and both fail the gate for the reasons guessed. `time_pressure_error` costs him **9.28 wp/game**
  against the reference population's 11.18, at **3.61 exposures a game against 2.50** — he meets
  time pressure far more often, loses nearly ten points of win probability a game to it, and is told
  nothing because a weaker population loses more.
- **n = 12**, and the below-band group is **two players**. The correlation (−0.79 measured) is a strong number over a
  small and non-random sample.
- **Rating and skill are not the same thing**, and this note uses Lichess rating as the band label
  because that is what the band is defined in. It does not show these players' *play* is
  proportionate to their rating.
- **This does not show the corrections were wrong**, and the measurement makes that sharper than
  the guess did. Separating the two changes to the endgame rule shows **E68's calibration cost zero
  priority slots** and **introducing the run at all (E67) cost six** — maikel5, maxhayastan and
  Odin5306, two each. The run was the author's own specification, so that is a correct change with a
  cost, not a regression. The calibration, which was the obvious suspect and the one this note named,
  was innocent.

## The open question this leaves

Fixing the build side stops a bad reference being **made**. It does not tell a player anything.
Three options, and the choice is the author's because it is a coaching decision, not a technical
one:

1. **Refuse, and say so** — "you are rated ~1930; this system is calibrated for 1400–1800". Honest,
   free, and delivers no coaching.
2. **Caveat, and report anyway** — state that the comparison is against a population below them, the
   way [[learning.risks]] I-04 turned a rating stop-gap into a statement of which reading is weaker.
   Keeps the cost pool, which is the half that does not depend on the band.
3. **Build the missing strata** — an 1800–2000 reference, and a 1200–1400 one. This is the only
   option that actually coaches these six players. Costs one engine pass over a new corpus, no cash,
   and it widens [[decisions.0005-scope-band-source-online-only]], which is why it is the author's
   call rather than a maintenance task.
