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

### Game length — do not adopt; use think-time instead

The corpus is already filtered to rated rapid and classical, and:

- **73.9 % of games are `600+0`.** 121 distinct time controls exist, and one of them is three
  quarters of the data.
- **20 of 84 players play exactly one time control.** For them the weight is definitionally inert.
- Median within-player spread is **2.7×** longest to shortest.

So the weight would be a no-op for a quarter of players and thin for most of the rest. It is also
confounded: a player who occasionally plays 30+0 is playing a *different sample*, not the same games
more slowly.

**The intuition is right and there is a far better variable for it.** The argument is *"with less
time, players make mistakes they would not otherwise make"* — that is a property of **the move**, not
of the game. Seconds spent per move is present in **100 %** of games via `%clk`, is already extracted
by the analysis core, and is already what S2 diagnoses on. Weighting a mistake by how long the player
thought before making it captures the stated intuition with far more signal: a blunder after 45
seconds of thought is evidence of a real gap; the same blunder after 2 seconds is evidence about
attention.

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

## Recommendation

Not a decision — the author's call. In order of value per unit of work:

1. **F, data cleaning.** One in ten games is contaminating the exact signals under discussion. An
   afternoon, and it improves every measurement already taken.
2. **B + C, accumulate the corpus and recognise that checking ≠ discovering.** Together these
   dissolve most of the stated motivation for the 20-game minimum without changing any statistics.
3. **Peer-relative severity.** E15's ranking is right in mechanism and too generic in quantity; this
   is the smallest change that fixes a defect already shipped.
4. **A, shrinkage.** The principled answer to "flex with history length", and the one that makes a
   20-game minimum defensible rather than aspirational.
5. **Think-time weighting** in place of game-length weighting.
6. Recency decay on calendar time — last, because it *costs* effective sample where sample is the
   binding constraint, and it only helps the quarter of players whose windows span months.

**On the 20-game minimum specifically:** it is a defensible floor for *admission*, and it is not
currently enough to *speak* — at 24 games the swarm is silent for 43 % of players, and 20 is worse.
Setting the minimum to 20 without changing the estimator promises something the measurement
contradicts. With items 1–4 it becomes a real number rather than a hopeful one.
