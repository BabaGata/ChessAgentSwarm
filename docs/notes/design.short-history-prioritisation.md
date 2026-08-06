---
id: cas-design-short-history
title: 'Design — prioritisation on short histories'
desc: 'Evaluation of the proposed 20-game minimum and importance score. Two of four ingredients survive measurement; the gate/score framing is a false choice.'
updated: 1786492800000
created: 1786492800000
---

# Design — prioritisation on short histories

**Status:** evaluation, no decision taken · **Date:** 2026-08-06 · **Serves:** V5, V7, C6
**Evidence:** [[experiments.e16-shallow-corpus]], [[experiments.e17-ranking-stability]]

## The proposal, as put

1. **Minimum history = 20 games**, treated as sufficient — because re-evaluating progress after a
   first batch of instructions cannot wait for a long history.
2. **Importance is not occurrence rate alone.** Score each mistake by combining
   **rate + severity + recency + game length**, where recent mistakes count more (players drift
   whether or not they train) and mistakes in longer games count more (with less time, players err
   in ways they would not otherwise).
3. **Score and take the top, instead of requiring criteria to be met** — so the system flexes with
   whatever history length it is given.

## Verdict in one paragraph

**The diagnosis is right and now measured; two of the four ingredients survive; the third point is a
false choice.** Scoring really does degrade gracefully where gating cliffs (E17). Severity really is
the strong ingredient — more so than proposed, since occurrence rate alone ranks *at chance*. But
severity alone tells 70 % of players the same thing, recency has almost nothing to act on for half
the corpus, game length is a near no-op on a rapid-filtered corpus, and replacing gates with a
ranking removes the only thing preventing a confident diagnosis from two data points. The productive
version keeps a score **and** an evidence discipline, by making the estimator sample-size-aware
rather than by choosing between them.

## Ingredient by ingredient

### Severity — adopt, and make it peer-relative

Already built earlier the same day ([[experiments.e15-expected-gain]]) as `Measurement.cost_wp`.
E17 independently validates the choice: severity ranking agrees with itself across disjoint windows
**65 %** of the time at 20 games against a 4 % chance baseline, where deviation manages 6 %.

**The unfinished part:** raw severity picks `advantage_error` for 70 % of players. Costly is not the
same as *unusually* costly, and the fix is the one the peer reference already exists to apply —
compare the player's cost against the population's cost for the same claim. This needs the reference
rebuilt carrying cost per claim, which it does not currently hold.

### Occurrence rate — keep, demote

E17: **6 % top-1 stability against 4 % chance at 20 games, 10 % against 3 % at 60.** Not a
tie-breaking artifact — every claim holds a distinct score. As a *ranking* signal it is close to
worthless, which is a stronger statement than the proposal makes.

It is not useless as a *gate*: "does this happen more than for peers" is a different and easier
question than "is this the thing that matters most", and it is what stops the swarm reporting a
single expensive blunder as a pattern.

### Recency — adopt, but by calendar time, not by game index

Measured on the corpus, the span of a player's most recent 20 games:

| | days |
|---|--:|
| median | **23.5** |
| p10 / p90 | 2 / 446 |
| under 14 days | 30 / 84 |
| under 30 days | 46 / 84 |
| **over 90 days** | **24 / 84** |

**Bimodal.** For over half of players a 20-game batch is three weeks of play, and down-weighting its
older half is weighting noise — the player has not changed. For a quarter of players the same 20
games span three months to nine years, where mixing them really is mixing different players.

So the rationale holds for the tail, not the median, and **weighting by game index would do the
wrong thing for both groups**: it would discount three-week-old games and fail to notice a three-year
gap. If recency is applied it should be a decay on **calendar time with a long half-life**.

One cost to state plainly: recency weighting **reduces effective sample size**, which is precisely
[[experiments.e16-shallow-corpus]]'s binding constraint. It makes the short-history problem
statistically worse, not better, and buys accuracy about *who the player is now* with precision about
*anything at all*.

### Starting clock — the weight is inert, and the reason it is inert is the real finding

*Clock at the start of the game — 10+0 against 3+2 — not number of moves.*

**Within the corpus the weight would do almost nothing:**

- **73.9 % of games are `600+0`.** 121 distinct time controls exist and one of them is three quarters
  of the data.
- **20 of 84 players play exactly one time control.**
- Median within-player spread is **2.7×**.

**But that is an artifact of the fetch, not a fact about players.** `PGN_PARAMS` requests
`perfType=rapid,classical`, so blitz and bullet never arrive. A 3+2 game is blitz — 3×60 + 40×2 =
260 s against Lichess's 480 s rapid threshold — and **the swarm has never seen one**. The proposal's
intuition is therefore already implemented, and more strictly than proposed: fast games are not
down-weighted, they are discarded.

**What that costs, measured** (bulk `/api/users` over the same 84 players):

| share of a player's record the swarm may look at | |
|---|--:|
| **median** | **18 %** |
| under 25 % usable | 51 / 84 |
| under 50 % usable | 69 / 84 |
| over 90 % usable | 4 / 84 |

**The filter discards roughly four games in five.** And the sample is biased *towards* rapid — these
84 were selected for having ~150-game rapid histories — so a typical player in the band is likely
worse, not better. Several have literally 0 % usable to two significant figures: one player has 45
rapid games against 37,955 discarded.

(The count of rapid games *available* per player is not reported here, because selection makes it
meaningless — they were chosen for having many.)

**This inverts the evaluation.** As a weight *inside* the rapid corpus, starting clock is inert. As
the mechanism that would let the other 82 % of a player's chess be used at all, it is the most
consequential idea in the proposal — and it lands directly on the binding constraint, since
[[experiments.e16-shallow-corpus]] found the swarm goes quiet because events are too rare per corpus.

**The objection is real and already recorded.** E01 and [[domain.signals]] found error rates are not
comparable across time controls, which is why the filter exists. Blending blitz into a rapid-built
peer reference would measure the clock rather than the player — L-019's mistake, where the control
was as sample-dependent as the thing controlled.

**Stratify rather than blend, then.** Build a peer reference per time-control class and compare
blitz-to-blitz and rapid-to-rapid, never across. Then:

- a claim that holds in **both** strata is a knowledge or skill gap;
- a claim that holds **only in blitz** is a speed or automaticity finding, which is a different and
  still useful thing to say;
- a claim that holds **only in rapid** is close to nonsense and would flag a measurement bug.

**And the gap between the strata may be a free diagnostic.** Under three minutes a player plays what
is internalised; over ten they play what they can work out. The *difference* between a player's blitz
and rapid rates on the same claim is therefore evidence about whether knowledge is present but not
automatic — which is exactly the SKILL-versus-FRAGILE distinction the prober currently has to ask a
player about. Untested, stated as a hypothesis, and cheap to test: compute both rates for the same
claim on players who have both, and check whether the difference varies between players or is a
constant of chess (the L-023 screen).

**Think-time per move remains worth having and is a different lever.** Seconds spent on the move is
in **100 %** of games via `%clk` and already extracted. It captures *"this player did not think here"*
within a single time control; the starting clock captures *"this whole game gave nobody time to
think"*. They are not substitutes.

### Score instead of gate — a false choice

A gate and a score answer different questions: *"do we believe this at all"* and *"of the things we
believe, which matters most"*. Replacing the first with the second means the swarm always speaks,
including when its best claim rests on two occurrences.

Worse, **severity and recency weighting actively favour thin evidence**. A single recent catastrophic
blunder maximises both. The top-scoring claim on a 20-game history would frequently be the most
dramatic thing that happened once — which is R-13 (statistical overclaiming), R-02 (unfalsifiable
coaching) and R-15 (regression to the mean) simultaneously, and R-15 has already been measured in
this project at 92 % before mitigation.

E16 makes this concrete: the gates that actually bind at 24 games are *"the event occurred in fewer
than 3 games"* and *"the interval does not exclude the baseline"* — 96 % of the silence. Those are
exactly the two anti-fabrication gates. Removing them buys coverage with the project's core claim to
honesty (C5, V8).

**But the underlying need is real**, and the answer is not a gate or a score — it is an estimator
that knows how much evidence it has.

## Alternatives

### A. Empirical-Bayes shrinkage (partial pooling) — recommended

The peer reference already holds 84 players' rates per claim: **that is a prior distribution**.
Instead of asking *"does the Wilson lower bound clear the peer rate?"* — a test that fails at small
*n* — estimate each claim as a posterior that shrinks toward the peer rate by an amount set by the
player's own sample size.

| | |
|---|---|
| **Pro** | Sample size enters **continuously** instead of as a cliff — exactly the flexibility the proposal wants, with the evidence discipline kept |
| **Pro** | At 20 games shrinkage is heavy, so only genuinely extreme claims survive; at 150 the player's own rate dominates. No threshold to tune |
| **Pro** | Shrinkage **is** the regression-to-the-mean correction, applied at estimation instead of patched afterwards — it attacks R-15 at the root |
| **Pro** | Beta-binomial conjugate arithmetic: deterministic, instant, free (C1) |
| **Pro** | Directly attacks E16's second-biggest gate (interval width, 69 of 158 blocks) |
| **Con** | Does nothing for E16's *largest* gate — an event occurring in fewer than 3 games is thin however it is estimated |
| **Con** | The prior is 84 players from one band; a badly-estimated prior biases every player toward it |
| **Con** | Harder to explain in a report than "you do this 1.8× more than peers" — and V8 requires the reasoning be auditable |

### B. Accumulate the corpus across sessions — recommended, and nearly free

The re-evaluation problem is partly self-inflicted. A returning player has **their original history
plus 20 new games**, and profiles are already persisted. Diagnose on everything; measure *progress*
on the new window only.

| | |
|---|---|
| **Pro** | Dissolves most of the stated motivation — the second assessment has *more* evidence than the first, not less |
| **Pro** | Costs almost nothing: the engine cache already holds the old positions |
| **Pro** | Composes with recency decay, which is where calendar-time weighting earns its place |
| **Con** | Needs corpus identity and storage the CLI does not currently have |
| **Con** | If the player genuinely improved, old games misrepresent them — the decay must be right |

### C. The re-evaluation is a different statistical problem — free, and already true

Diagnosis searches ~25 candidate claims; re-evaluation tests **one pre-specified claim** against a
pre-committed target. The multiple-comparison burden is gone, so 20 games is far more adequate for
checking than for discovering. [[experiments.e06-progress-power]] already measured the held-out
false-positive rate of exactly that design at **15 %**.

This is worth stating because it means **the 20-game worry applies to diagnosis, not to progress
checking** — and progress checking was the reason given for it.

### D. Pool related claims — attacks the largest gate

E16's biggest blocker is rarity: the event does not occur in 3 separate games. Grouping claims (all
tactical motifs; all rook-endgame errors) raises events per corpus.

| | |
|---|---|
| **Pro** | The only option that touches the 83-of-158 gate |
| **Pro** | Partly built already — `POOLED_SUBJECT`, `drop_redundant_aggregates` |
| **Con** | Coarser advice: *"you miss tactics"* is less actionable than *"you miss skewers"* |
| **Con** | L-023's magnitude problem returns — pooled claims deviate less, so they may clear the evidence gate and fail `FOCUS_MARGIN` |

### E. Two-tier vocabulary — cheap, and risky in a specific way

Report under-evidenced claims explicitly as *suspected, not established*.

| | |
|---|---|
| **Pro** | Changes the report, not the mathematics. Very cheap |
| **Pro** | Honest: E16 found every silent player has a median of **7** patterns the swarm can see and cannot confirm |
| **Con** | Players discount hedges. A "suspected" weakness read as a real one is the anti-pattern with extra steps |
| **Con** | Adds a second thing the progress check must handle: what does it mean to fix a suspicion? |

### F. Data cleaning — cheapest item here, and independent of everything above

The metadata census found contamination nobody has filtered:

| | share of corpus |
|---|--:|
| **Berserked games** (arena, player halves their own clock) | **8.0 %** |
| **Abandoned games** | 2.2 % |

Berserking is a *self-inflicted time handicap*. Those games systematically inflate error rates and
every time-pressure finding S2 makes — the exact signals under discussion. Abandoned games contain no
chess decisions worth diagnosing. Roughly **one game in ten** is currently biasing the measurement,
and both are single PGN tags away from being excluded.

## What Lichess actually exposes

From the live corpus (11,890 games), not from the documentation:

**Present in 100 % of games:** `Date`, `UTCDate`, `UTCTime`, `White`, `Black`, `Result`, `WhiteElo`,
`BlackElo`, `TimeControl`, `Termination`, `Variant`, `GameId`, `Site`, `Event`, and move-level
`%clk` clock readings.

**Present and unused — the interesting column:**

| tag | coverage | what it would give |
|---|--:|---|
| `Termination` | 100 % | 9.6 % time forfeit, 2.2 % abandoned. Distinguishes losing on the clock from being outplayed — directly S2's subject |
| `WhiteRatingDiff` / `BlackRatingDiff` | 99.5 % | **Rating change per game.** A free, per-game progress signal for V7 that needs no re-fetch and no engine |
| `WhiteElo` / `BlackElo` | 100 % | **Opponent strength per game.** An error against a 1700 is not the same evidence as one against a 1300, and nothing currently conditions on it |
| `WhiteBerserk` / `BlackBerserk` | 8.0 % of games | Self-halved clock — see F |
| `Event` | 216 distinct | ~50 % are arena tournaments, a different psychological setting from a casual rated game |
| `FEN` / `SetUp` | 2.5 % | Games not starting from the initial position |
| `%eval` | **186,783 move annotations** | Lichess's own evaluations, free. Usable as a cross-check, **not** as a substitute: they come at Lichess's depths and the local cache is keyed by depth precisely because mixing depths is a correctness bug |

`ECO` / `Opening` (96 %) are already used by S4.

### G. Admit blitz, stratified by time control — the largest single lever found

Raised by the starting-clock section above and recorded separately because it is not a weighting
question. The swarm currently discards a median of **82 %** of a player's games.

| | |
|---|---|
| **Pro** | Roughly **5× more evidence per player**, aimed squarely at E16's binding constraint — rarity of events per corpus |
| **Pro** | Makes a 20-game rapid minimum far easier to meet, because it stops being rapid-only |
| **Pro** | The blitz-versus-rapid gap may diagnose automaticity for free, where the prober now has to ask |
| **Pro** | Nothing is blended, so the E01 objection is respected rather than overruled |
| **Con** | A second peer reference per time-control class, and the engine cost of analysing ~5× the games — the first real challenge to C1/D9 in a while |
| **Con** | Blitz mistakes are frequently not knowledge gaps, so claim kinds may need to declare which strata they are valid in |
| **Con** | Bullet is probably still worthless and the boundary has to be drawn somewhere |

## The solution, as one design

The options above are pieces. This is the shape they make together, and it follows from a single
observation: **the swarm has been treating "how much evidence do I have" as a threshold question
when it is an estimation question — while simultaneously discarding four fifths of the evidence
available to it.** Those are independent failures, they multiply, and neither is fixed by weighting.

Five layers, each independently useful (C6) and independently verifiable.

### Layer 1 — Supply: stop discarding evidence

| | |
|---|---|
| **Exclude contaminated games** | 8.0 % berserked, 2.2 % abandoned. Both are single tags |
| **Admit blitz and bullet, stratified by speed class** | never blended; one peer reference per class |
| **Accumulate the corpus across sessions** | diagnose on everything held, measure progress on the new window only |

### Layer 2 — Estimation: a posterior, not a gate

Replace the interval test and the distinct-game floors with **empirical-Bayes shrinkage**. The peer
reference for the player's band *and speed class* supplies the prior; the player's own games update
it, shrinking toward the population by an amount their sample size decides.

Sample size then enters **continuously** rather than as a cliff, which is exactly the flexibility the
proposal asked for — obtained without abandoning evidence discipline, because a 20-game claim simply
shrinks most of the way back to the peer rate unless it is genuinely extreme. It is also the
regression-to-the-mean correction (R-15) applied at estimation rather than patched afterwards.

`MIN_GAMES_WITH_DATA` survives as a floor on speaking at all. `FOCUS_DISTINCT_GAMES`,
`FOCUS_GAMES_WITH_DATA`, `FOCUS_MARGIN` and the interval test are subsumed.

### Layer 3 — Ranking: peer-relative expected cost

    score  =  posterior excess rate  ×  cost per instance  ×  opportunities per game

*"The win probability you give away above what a player at your level gives away, per game."*

This is the one quantity that answers both of E17's failures at once. It is severity-based, so it is
**stable** at 20 games (65 %); it is peer-relative, so it should not name the same weakness for
**70 %** of players the way raw cost does. Occurrence rate stays as an input to the estimate and
stops being a ranking signal, which is what the measurement says it is worth.

### Layer 4 — Speaking: graded, not gated

Rank by the score, report one or two. Confidence becomes a property of the posterior rather than a
tier lookup:

- **established** — the credible interval excludes zero excess over peers;
- **suspected** — the point estimate is high and the interval does not exclude zero;
- **silent** — the posterior is indistinguishable from the prior, meaning the player's games say
  nothing this population does not already say.

E16 found every silent player holds a median of **7** patterns visible and unconfirmable. This is
what lets those be spoken about without being overclaimed — and the progress check must then be able
to test a *suspicion*, which is new work, not a free rename.

### Layer 5 — Re-evaluation

The original worry dissolves rather than being solved. **Diagnosis** runs on the accumulated corpus,
so a returning player has *more* evidence than at first contact, not less. **Progress checking** runs
on the new 20-game window alone and is a far easier statistical problem — one pre-specified claim
against a pre-committed target, no search over 25 candidates — already measured at a 15 % held-out
false-positive rate ([[experiments.e06-progress-power]]).

Recency decay on calendar time applies to **diagnosis only**, with a long half-life, and is last
because it *spends* effective sample size where sample size is the binding constraint.

### Sequence, with what proves each step

| # | Step | Done when | Risk |
|--:|---|---|---|
| 1 | ~~Exclude berserked and abandoned games~~ **done 2026-08-06** — see below | E08 re-run; every prior measurement re-stated on clean data | none — pure subtraction |
| 2 | **Screen** the blitz/rapid gap (L-023, L-025): does it vary *between players*, or is it a constant of chess? | a number, and a decision between pooling with an offset and full stratification | the screen says "constant", and the automaticity hypothesis dies |
| 3 | Peer-relative severity: rebuild the peer reference carrying cost per claim | concentration of the top claim falls well below 70 % (E17 re-run) | fixes a defect shipped in E15 |
| 4 | Shrinkage replaces the gates | coverage at 24 games rises from 43 % silent; E08 D1/D2 unchanged or better | the prior is 84 players from one band |
| 5 | Admit blitz per step 2's answer | coverage at a **20-game rapid history** measured, not predicted | **C1/D9** — ~5× the games to analyse |
| 6 | Accumulate the corpus across sessions | a second session on the same player uses both corpora | needs corpus identity the CLI lacks |
| 7 | Recency decay on calendar time | drift measurable on the quarter of players whose windows span 90+ days | costs effective sample |

Steps 1–4 need no new data and no architectural commitment. **Step 5 is the architectural one** and
is the only place C1 is genuinely at risk, which is why step 2 comes before it: the screen is cheap
and decides whether step 5 is one corpus or three.

### Step 1 as built, 2026-08-06

Exclusion lives in `build_corpus`, not at parse time, so the profile records **how many games were
set aside and why** and the report tells the player (C5, schema v10).

**The rule is per-side, which the first count was not.** Berserk is a property of one player: the
earlier 8.0 % counted games where *either* side berserked. If the **opponent** berserked, the
diagnosed player's clock was untouched and their decisions are still theirs, so the game stays.
That refinement kept ~480 games that a naive rule would have discarded.

| | |
|---|--:|
| games excluded | **583** of 11,418 (5.1 %) |
| — berserked *by the diagnosed player* | 471 |
| — abandoned | 112 |
| players losing at least one game | **55 / 84** |
| median share of a player's games lost | **1.3 %** |
| **worst affected player** | **48.8 %** |

Effect on what players are told, against the same run before cleaning:

| | before | after |
|---|--:|--:|
| players advised | 70 | **69** |
| mean pairwise overlap | 0.06 | **0.05** |
| distinct claim kinds | 26 | 26 |
| groundedness | 113/113 | 108/108 |
| `advantage_error` advised | 9 | **7** |
| `advantage_error` share of players (D2) | 13 % | **10 %** |

**It costs coverage and buys correctness.** One player went silent and none gained. The
`advantage_error` fall is the predicted bias confirmed: with half a clock a player throws away won
positions, and those games were inflating exactly that claim — the one E17 had already flagged as
over-selected.

**Honest limitation:** for an arena-heavy player this makes the short-history problem *worse*. The
worst affected player lost 48.8 % of their games. That is the correct call — half their record is
half-clock chess and diagnosing it as ordinary play would be wrong — but it means step 1 pushes
slightly against steps 4–6 rather than with them.

### What this does not fix

- **E16's largest gate is rarity**, and shrinkage does not manufacture events. Only steps 1, 5 and 6
  add events. If the screen kills step 5, claim pooling (option D) becomes necessary rather than
  optional.
- **Nothing here is about correctness.** Every measurement in E15–E17 is reproducibility and
  specificity. That a stable, specific, peer-relative priority is the *right* thing to coach remains
  untested, and success criterion 2 in [[vision]] is where that gets settled.
- **A 20-game minimum is still a promise this design has to earn.** It becomes defensible at step 4
  and measurable at step 5; until then it is an aspiration, and saying otherwise would be the same
  overclaiming the gates exist to prevent.

## Recommendation

Ranked by value per unit of work, for reference — the sequence above is the actual plan:

1. **F, data cleaning.** One in ten games is contaminating the exact signals under discussion. An
   afternoon, and it improves every measurement already taken.
2. **B + C, accumulate the corpus and recognise that checking ≠ discovering.** Together these
   dissolve most of the stated motivation for the 20-game minimum without changing any statistics.
3. **Peer-relative severity.** E15's ranking is right in mechanism and too generic in quantity; this
   is the smallest change that fixes a defect already shipped.
4. **G, stratified blitz.** Biggest lever on the binding constraint and the biggest piece of work
   here. Worth screening before building: does a claim's blitz rate and its rapid rate differ *per
   player*, or by a constant (L-023, L-025)? That screen is cheap and decides whether G is one
   corpus or two.
5. **A, shrinkage.** The principled answer to "flex with history length", and what makes a 20-game
   minimum defensible rather than aspirational.
6. **Think-time weighting**, which is a different lever from starting clock rather than a substitute.
7. Recency decay on calendar time — last, because it *costs* effective sample where sample is the
   binding constraint, and it only helps the quarter of players whose windows span months.

**On the 20-game minimum specifically:** it is a defensible floor for *admission*, and it is not
currently enough to *speak* — at 24 games the swarm is silent for 43 % of players, and 20 is worse.
Setting the minimum to 20 without changing the estimator promises something the measurement
contradicts. With items 1–4 it becomes a real number rather than a hopeful one.
