---
id: cas-learning-lessons
title: Lessons Learned
desc: 'Generalisable lessons extracted from executed work — what worked, what did not, and why.'
updated: 1785254500000
created: 1785254500000
---

# Lessons Learned

Append-only log. One entry per lesson, newest first. A lesson is only a lesson if it would change
what a future cycle does — otherwise it is a diary entry and does not belong here.

## Template

```
### L-NNN — <short title>
**Date:** YYYY-MM-DD · **Cycle / mission step:** Mx · **Class:** technique | process | domain | tooling
**Context:** what was being attempted
**Observation:** what actually happened (with evidence)
**Lesson:** the generalisable claim
**Applied to:** the note/rule/code changed because of it
```

---

### L-030 — Stability and specificity trade against each other, and one metric hides the other
**Date:** 2026-08-06 · **Cycle / mission step:** M6 · **Class:** technique
**Context:** Testing whether weakness rankings can be trusted on 20-game histories
([[experiments.e17-ranking-stability]]).
**Observation:** Two ranking signals were compared across disjoint windows of the same player.
Deviation-from-peers agreed with itself **6 %** of the time against a 4 % chance baseline — real
ordering, real noise. Severity agreed **65 %** of the time, which looked like a clear win until the
second measurement: severity names the same claim for **70 %** of players, from a vocabulary of six.
It is stable *because* it is nearly a constant. Had only the agreement figure been computed, a
signal that turns the coach into one who says the same thing to seven players in ten would have
looked like the best result in the project.
**Lesson:** Reproducibility and discriminating power are separate axes, and a measurement of one
reads as success while the other fails silently. **Any ranking or scoring change must report
agreement *and* concentration together** — how often it says the same thing twice, and how often it
says the same thing to everybody. The general form: an estimator can buy variance reduction with
bias, and a stability metric is blind to exactly that trade.
**Applied to:** [[experiments.e17-ranking-stability]], [[design.short-history-prioritisation]], and
a stated defect in [[experiments.e15-expected-gain]] — raw cost must become peer-relative cost.

---

### L-031 — A correlation means nothing without its own reliability ceiling
**Date:** 2026-08-06 · **Cycle / mission step:** M6 · **Class:** technique
**Context:** Screening whether blitz games can join the diagnostic corpus
([[experiments.e19-blitz-stratum]]).
**Observation:** Blitz error rates correlated with rapid ones at a median **r = +0.17**. Read
straight, that says the two speeds measure different things and the corpora must be kept apart —
an architecture of three corpora and three peer references. The control changed the answer
completely: splitting *rapid* into two disjoint windows of the same size and correlating it with
**itself** gave **r = +0.19**. Blitz predicts rapid as well as rapid does. The low figure was
attenuation from measurement noise, and the tell had been visible all along — r tracked each claim's
**denominator** (+0.67 for `early_error`, which occurs every game; +0.02 for `allowed_motif.fork`,
which does not) rather than anything about speed.
**Lesson:** A correlation between two noisy measurements is bounded by their reliability, so "r is
low" and "these measure different things" are different claims and only the second is interesting.
**Never interpret a correlation without measuring what the same data correlates with itself at the
same sample size.** The same control applies to any spread or ratio statistic — here the per-player
gap "varied" 2.39× against a noise floor of 2.08×, which is also nearly nothing. This is L-019's
rule — a control must be as sample-dependent as the thing it controls — applied to correlation
rather than to a drift constant.
**Applied to:** [[experiments.e19-blitz-stratum]], [[design.short-history-prioritisation]] step 5,
which becomes one pooled corpus instead of three.

---

### L-029 — The constraint you can name is rarely the one that binds
**Date:** 2026-08-06 · **Cycle / mission step:** M6 · **Class:** process
**Context:** Being asked *why* the swarm is silent for nearly half of players at 24 games — a figure
[[state]] had been quoting for several cycles with a stated cause.
**Observation:** The cause on record was `FOCUS_DISTINCT_GAMES = 5`, generalised from S6, where the
threshold had visibly bitten. Instrumenting all five gates and counting
([[experiments.e16-shallow-corpus]]) put it at **5 of 158 sole-gate blocks — 3 %**. What actually
binds is the event occurring in fewer than three games at all (83) and the interval failing to
exclude the baseline (69). The named threshold was real, memorable, and almost irrelevant; it was
promoted to *the* explanation because it was the one that had been watched closely.
**Lesson:** A number that gets quoted — a coverage gap, a latency, a failure rate — attracts a cause
from whatever was being examined when it was first noticed, and then the cause is repeated as if it
had been measured. **Before acting on a bottleneck, count every candidate, not just the one with a
name.** The census is usually cheap next to the fix it would have justified: here it was one script
against a warm cache, and it ruled out the change that was about to be made.
**Applied to:** [[state]] P1 and P2 (both rewritten), [[experiments.e16-shallow-corpus]].

---

### L-028 — A failed experiment answers its question, not the neighbouring one
**Date:** 2026-08-06 · **Cycle / mission step:** M6 (V5) · **Class:** process
**Context:** Building expected-gain reasoning ([[experiments.e15-expected-gain]]), which two
scorecard cycles had recorded as blocked.
**Observation:** [[experiments.e03-relevance-weighting]] looked for a link between a position feature
and errors and did not find one. From then on [[state]] carried *"no expected-gain reasoning"* with
E03 as the reason, and the next two cycles repeated it without re-examining it. The two questions are
not the same one: E03 asked whether a feature **predicts** mistakes — a model that must generalise —
while prioritisation only needs to know, for instances **already identified** as mistakes, how much
was given away on exactly those moves. That is a sum over `loss_wp`, which every observation had been
carrying since M3. The work took one cycle and changed the advice for 33 of 84 players.
**Lesson:** A null result bounds the question that was asked, and nothing else. When a negative
experiment starts being cited as a reason *not to attempt* something, write down the question it
actually asked next to the question now being refused — if they differ in kind (**predicting** versus
**accounting**, causal versus descriptive), the block is inherited rather than measured. The
tell is a limitation that survives several cycles unchanged while being restated in the same words.
**Applied to:** [[experiments.e15-expected-gain]], `chesscoach/arbiter.py` ordering, [[state]] D5.

---

### L-027 — A trait that rises with skill is not a trait
**Date:** 2026-08-06 · **Cycle / mission step:** M6 (V3) · **Class:** technique
**Context:** Screening six candidate style dimensions before building V3
([[experiments.e14-style-dimensions]]).
**Observation:** Four of the six correlated with rating at **0.47–0.56**: capture share, check share,
game length, material kept on. Weaker players capture more, check more and finish sooner. Only two
were independent of strength, and the best of them — how much of a game is spent with the queens off
— sits at **r = −0.069**. A style profiler screening on variation alone would have passed all six and
told a 1200 *"you are an aggressive attacking player"* while measuring *"you are weaker"*.
**Lesson:** Whenever a system already measures one thing well, every *new* thing it measures must be
checked against it, or the new measurement will quietly re-describe the old one in more flattering
words. This is L-025 with the confound named: there the proxy was the error rate, here it is skill,
and the general form is **"what does this correlate with that I already know?"** Style is unusually
exposed to it because the vocabulary is evaluative — "aggressive", "solid", "impatient" — so a
correlation with strength arrives pre-loaded with a personality story that sounds like insight.
[[domain.coaching]] § 6 anticipated this and said to demand measured tendency *and* measured
performance rather than a label; the screen is what turned that instruction into a test.
The other half is worth as much: **the performance half failed.** Everyone errs about 20 % less with
the queens off and players barely differ, so *"and it suits you"* is unsupportable. It shipped as a
tendency with the verdict explicitly withheld, which is a smaller product and the only honest one.
**Applied to:** `chesscoach/style.py` (one dimension of six, no fit verdict), the two-bar screen in
[[experiments.e14-style-dimensions]], and D3 scored 2 rather than 3 for exactly the missing half.

---

### L-026 — More evidence per player beat more things to look for, by a wide margin
**Date:** 2026-08-06 · **Cycle / mission step:** M6 (deep rebuild) · **Class:** technique
**Context:** Coverage had stalled at 20 of 38 players across two consecutive sections
([[experiments.e12-corpus-depth]]).
**Observation:** Six sections — S3 through S8, several cycles of design notes, screens, detectors and
assessments — moved coverage from **24 % to 53 %** of players. Rebuilding the same swarm on 150-game
histories instead of 24-game ones moved it from **53 % to 83 %**, in about forty-five minutes of
mostly-cached engine time, with no new diagnostic capability whatsoever. Overlap *fell* at the same
time (0.06 → 0.05), so the extra advice is more specific rather than more generic, and distinct claim
kinds went 16 → 27 — claims that had never once cleared the confidence gate started clearing it.
**Lesson:** When a system is silent, the instinct is that it does not know enough *kinds* of thing.
Often it does not have enough *evidence* about the thing it already knows. The two are easy to
confuse because adding a section feels like progress and is visible in the codebase, while adding
games is invisible and feels like admin. The diagnostic is cheap and should be routine: **is the
constraint the claim or the count?** Here it was `FOCUS_DISTINCT_GAMES = 5` — a weakness appearing in
three of a player's games cannot clear a five-game floor however well a section measures it, and six
sections' worth of work could not fix that because none of them changed the denominator.
The uncomfortable corollary, which is the honest half: **a real user brings 24 games, not 150.** This
did not make the swarm better at coaching; it made it better at coaching *people with long
histories*. That is a constraint on who it can help, and it should be stated as one rather than
banked as coverage.
**Applied to:** the peer reference and working corpus both rebuilt on the deep histories, [[state]]'s
P0 moved off "more sections", and D12 reopened as a calibration question now that the magnitude floor
is what decides the weakest advice.

---

### L-025 — A claim that varies may still be a proxy for one you already have
**Date:** 2026-08-05 · **Cycle / mission step:** M4 (S7 screened, not built) · **Class:** technique
**Context:** Screening S7's calculation candidates before building it
([[experiments.e10-calculation-candidates]]).
**Observation:** `missed_quiet` — the error rate where the engine's move is quiet rather than forcing
— spreads **1.56** between players, which is inside the range this project treats as promising. It
was nearly built on. Its correlation with `missed_forcing` is **+0.737**: the players who go wrong on
quiet moves are the players who go wrong on forcing moves. The spread is the general error rate, not
calculation. And the contrast that would isolate calculation, `missed_quiet / missed_forcing`, has a
median of 1.17 and a between-player spread of 1.27 — i.e. once the error rate is divided out, almost
nothing remains.
**Lesson:** E09 established *does this vary between players?* as the screen. **That is necessary and
not sufficient.** A candidate can vary handsomely and still be a re-description of something the
swarm already measures, which is worse than a claim that fails outright: it survives every check,
adds a claim kind, raises the coverage number, and tells the player nothing new. The second question
is **does it survive dividing out what we already know?** — a correlation against the base rate, or
better, screen the *ratio* rather than the rate, because the ratio is the thing the section actually
claims. This is L-014 one level up: there the denominator was wrong and the claim tracked the error
rate; here the denominator is right and the claim tracks it anyway.
**Applied to:** S7 not built; [[domain.sections]] records it as a consumer of V9 probes rather than a
section; the two-question screen is now the pattern for S8 and beyond.

---

### L-024 — What the opponent gets discriminates; what your position contains does not
**Date:** 2026-08-05 · **Cycle / mission step:** M4 (S6) · **Class:** technique
**Context:** Screening five candidate claims for S6 before building it
([[experiments.e09-square-candidates]]).
**Observation:** Three candidates failed and two succeeded, and the split was not arbitrary. **Failed
— all descriptions of the player's own position:** a hole in their camp (spread 1.25), a bishop
hemmed by its own pawns (1.27), a rook missing from an open file (1.31). **Succeeded — both
descriptions of what the opponent obtained:** a knight settled where it cannot be evicted (**2.15**,
the highest in the project) and a rook reaching the player's second rank (**1.82**). The same line
runs backwards: S5's `concedes_weakness`, about the player's own structure, spreads 1.20–1.85 and
mostly at the bottom, while S1's `allowed_motif`, about what punishes the player, fires readily.
**Lesson:** Positions converge; consequences do not. Two players at the same rating reach positions
with broadly the same number of holes, bad bishops and unoccupied files, because those are properties
of the openings played at that level rather than of the player. What differs is **what opponents
manage to do about it** — and that is a joint product of the player's choices and their opponent's,
which is exactly what a coach can act on. The practical rule for later sections: **when a topic can
be framed either as a property of the position or as something the opponent achieved, frame it the
second way.** It is also the framing that makes a claim mean something to read: "you have holes" is
a description, "opponents park knights in your position" is a diagnosis.
Second-order, and cheap: this whole finding cost one engine-free minute per candidate. Screening is
so much cheaper than building that the only reason S5 was not screened first is that nobody had
thought to.
**Applied to:** `chesscoach/squares.py` and `chesscoach/sections/s6_squares_and_files.py` (two claims
rather than five), § 9.1 of [[capacity.agents.s6-squares-and-files]], and carried into S7/S8 as a
design prior.
**Counter-example found 2026-08-05, one section later.** E11 screened `shield_broken` — the player's
castled king having lost its pawn cover, squarely a property of their own position — and it spreads
**1.62**, slightly *more* than the opponent-achievement claim beside it. Holes (1.25) and bad bishops
(1.27) did not; a bare king does. **So this is a useful prior and not a law.** One hypothesis, offered
as such: a hole is one square among sixty-four while a broken shield is a property of *the square
that decides games*, so grouping both as "position properties" may be the mistake — the rule might
really be about **how close the property sits to the result**. Recorded rather than resolved, and the
lesson is kept in its weaker form: prefer the opponent-achievement framing when a topic allows both,
but screen the alternative rather than assuming it will fail.

---

### L-023 — A big denominator turns a significance test into a rubber stamp
**Date:** 2026-08-05 · **Cycle / mission step:** M4 (S5) · **Class:** technique
**Context:** Building S5, whose claims carry ~526 opportunities per player against 92–232 for every
other section ([[capacity.agents.s5-pawn-structure]]).
**Observation:** The confidence policy's `focus` tier — the one that reaches the player — requires
only that a claim's 95 % interval **excludes** the peer rate. That is a test of *significance*, with
no floor on *magnitude*; the 1.25× `PRIORITY_MARGIN` applies to the tier above. The rule was
calibrated when every claim had ~100 opportunities, where significance and a coachable effect arrive
at roughly the same point. At 526 they come apart: S5's pooled claim deviates by **1.24× at the 90th
percentile** — comfortably significant, and far too small to say out loud.
**Lesson:** This is **L-022 inverted, and the pair is the real lesson**. Too small a denominator and
a section goes silent; too large and it asserts things that are true, reliable and not worth hearing.
A gate expressed as *"is this distinguishable from the population?"* is only equivalent to *"is this
worth telling someone?"* at the sample size it was calibrated for, and every new section changes the
sample size. **Check the population spread before shipping a section, not after** — S5's design note
made that its § 9.1 and it took one query against the peer reference to answer.
The corollary that made it usable rather than fatal: the spread **predicted which claims could
fire**. `doubled` (1.20) and the pooled `any` (1.24) never fired for anybody; `isolated` (1.40) fired
for two outliers; `backward` (1.85) fired five times. A cheap population-level check told me in
advance which parts of a section were real.
**Applied to:** `chesscoach/sections/s5_pawn_structure.py` (`MIN_PEER_RATIO`), **D12** in
[[open-questions]] for the policy-level fix, and § 9.1 of the S5 note as the pattern later sections
should copy.
**Fixed at the policy level the same day.** `focus` now requires the rate to clear its comparison by
1.25× as well as the interval to exclude it — magnitude *and* significance
([[architecture.confidence]]). The floor was **measured rather than picked**: all 40 findings the
swarm currently asserts were checked and the smallest is 1.40, so it removes none of them and
re-measurement confirmed zero change. Worth noting what that means — **the defect was real and
latent**. It had never yet produced a bad finding, because no section had a denominator large enough
until S5. A rule can be wrong for a long time before it is wrong *about anything*, and the thing that
exposed it was building a section whose shape differed from all the previous ones.

---

### L-022 — Subdivide only where the data can carry the subdivision
**Date:** 2026-08-05 · **Cycle / mission step:** M4 (S3) · **Class:** technique
**Context:** Building S3 for **coverage**, after E08 measured the swarm silent for 29 of 38 players
([[capacity.agents.s3-endgame-technique]]).
**Observation:** S3 emits one pooled claim (`endgame_error.any`) and five material classes. Across 38
real players the pooled claim produced **every single finding**; **all five classes fired for
nobody**. The design note had already argued that finer classes "would fire for nobody" and chose
five deliberately coarse ones as the compromise — and five was still too many. The same shape shows
up in S1, where [[mission.step-07-second-iteration]] recorded roughly three skewer opportunities per
player and only two motifs ever reaching `focus`.
**Lesson:** A subdivision is only worth making if each part can still clear the confidence gate, and
that is a **property of the denominator, not of the taxonomy**. Chess vocabulary invites splitting —
by motif, by material, by phase — and every split divides the evidence while the significance
threshold stays put. The working rule for later sections: **lead with the aggregate**, which is what
lets the section speak at all, and add subdivisions only where the data has been shown to carry them.
The cost of getting it wrong is not a wrong answer, it is silence, which is much harder to notice.
**Applied to:** `chesscoach/sections/s3_endgame_technique.py` (`endgame_error.any` as the
load-bearing claim), and the P0 note in [[state]] directing later sections to the same shape.
**Confirmed by S4, 2026-08-05.** The next section chose its subdivision by denominator instead of by
chess taxonomy — **colour** (two buckets, half the games each) rather than opening name (a dozen
buckets, two games each) — and it **fired for seven players** where S3's five material classes fired
for none. Same lesson, applied at design time rather than discovered, and it worked the first time.
The corollary S4 also found: once a subdivision *does* fire, the pooled claim becomes redundant for
that player, so `drop_redundant_aggregates()` keeps the specific one
([[capacity.agents.s4-opening-outcomes]] § 8).

---

### L-021 — A metric passing is not the same as the output being good
**Date:** 2026-08-05 · **Cycle / mission step:** M5 ([[mission.step-08-assess-prober]]) · **Class:** process
**Context:** Assessing the explainer with the anti-pattern metrics from [[evaluation]].
**Observation:** D4 groundedness scored **100 %** — every reported claim cited a specific game. On the
*same output*, a player was being told *"it is often a `trappedPiece` that punishes you"*: a CC0
Lichess theme key, camelCase, meaningless to a human. The metric was correct and the report was bad,
because groundedness asks whether a claim is *cited*, not whether it is *readable*. I had scored D8
explainability 3 on the strength of that report the cycle before.
Separately, the same run nearly produced a wrong conclusion in the other direction: D2 flagged a claim
made to 56 % of advised players as a probable base-rate artefact, when the real cause was that almost
nothing else clears the confidence gate. One extra column — detected against advised — turned a
"suppress this claim" conclusion into a "build more sections" one.
**Lesson:** Metrics measure the property they define, and a green metric licenses no claim beyond it.
Two habits follow. **Read the actual output** at least once per cycle in the form the user would see
it; every defect this cycle found — theme keys in prose, a byte-order mark, a stopped model — came
from looking rather than from a suite, and 429 tests were green throughout. And **a metric that can
be explained by two mechanisms must report both**, in itself rather than in a note, because the
reading happens months after the design and by someone with less context — often me.
**Applied to:** `chesscoach/phrasing.py` (`subject_name`, and the theme key kept only where the
player can act on it), `experiments/e08-anti-patterns/` (detected-vs-advised), [[evaluation]]'s D2
entry, and D8 corrected in [[state]].

---

### L-020 — A failure that returns a legitimate value is invisible
**Date:** 2026-08-04 · **Cycle / mission step:** M4 (session runner) · **Class:** technique
**Context:** The first live probe session, run against a local model
([[capacity.agents.prober]]).
**Observation:** Every probe came back *unclear*, including an answer that plainly described a pin.
The cause was that **Ollama had stopped** — and `_post` returned `None` on a connection failure,
which is also the legitimate value for *the model replied but not usably*. The stored profile
therefore could not distinguish **"we asked and the player was vague"** from **"we never managed to
ask"**. One is evidence about the player; the other is evidence about the infrastructure. It took a
direct call returning `yes` where the session returned `None` to notice at all, and even then the
first hypothesis was that the model was flaky.
**Lesson:** *Degrade rather than fail* is right, and it is not the whole rule. When a failure path
returns a value the domain already uses, the failure stops being observable — the system looks like
it is working and the data looks clean. **The degraded value has to be distinguishable from the
legitimate one it resembles.** Here that is a status alongside the verdict, plus a warning on screen,
plus `was_actually_asked` so anything reasoning over probes can exclude the ones never really asked.
The general test: for every `None`/empty/default a component can return, ask *what else returns
this, and would I be able to tell them apart afterwards?*
Second-order point worth keeping: both defects in this cycle — this and a byte-order mark turning a
correct move into a knowledge gap — were found by **running the thing for real once**, not by tests.
The tests were passing throughout, because both bugs lived at the boundary where real input arrives.
**Applied to:** `chesscoach/classifiers.py` (`ClassifierUnavailable`), `chesscoach/prober.py`
(`ClassifierStatus`, refusal detection moved to the prober), `chesscoach/cli.py` (the warning),
schema v5, and [[learning.risks]] I-01/I-02.

---

### L-019 — Regression to the mean is a property of the sample, not of the population
**Date:** 2026-08-03 · **Cycle / mission step:** M3 (deep-history rerun) · **Class:** technique
**Context:** Re-running E05 on 84 players with ~150 games each, after L-018 identified sample size as
the blocker ([[experiments.e05-natural-drift]]).
**Observation:** Deepening the histories did not merely add predictions, it **changed the effect being
measured**. Drift with no coaching fell from **+11.2 points to +4.8**, and the median `after`/`expected`
rose from **0.52 to 0.87** — rates no longer halve on their own. The constant calibrated against the
thin sample (0.34) turned out to be unmeetable on the thick one: **1 of 52** untreated predictions met
it.
**Lesson:** The size of a regression-to-the-mean effect is set by how much of the selected value was
luck, so it scales with the *thinness of the measurement*, not with anything about the subjects. The
+11.2 was never a fact about chess players; it was a fact about measuring them over 30 games. Two
consequences that generalise beyond this project. First, **a control measured on thin data
overstates the correction that thicker data needs** — the control is as sample-dependent as the thing
it controls for. Second, **an over-strict constant is not the safe direction**: a target nothing
reaches has no power, so it cannot detect a real effect any more than a loose one can distinguish a
false one. Erring "conservative" on a threshold is still erring. The corollary the project has not
yet paid: a single constant applied regardless of history depth is now *known* to be wrong, because
0.34 and 0.58 fit different depths.
**Applied to:** `chesscoach/planner.py` (`NO_CHANGE_RATIO` 0.34 → 0.58, `UNTREATED_MET_SHARE_RANGE`
introduced, the progress sign's "rates typically halve" claim removed as false at depth),
`experiments/e05-natural-drift/calibrate.py` (`--folds`, `--sweep`), and E05's framing throughout.

**Corrected 2026-08-03, the day after it was written.** The lesson's direction is right and is now
confirmed four times over — but its magnitude was wrong, and wrong in the flattering direction. It
claimed *"0.34 fitted 60-game histories, 0.58 fits 150-game ones"*. **0.34 was never a fitted value at
any depth**: it came from 13 predictions with disagreeing folds and was then tightened by hand.
Controlling depth properly (D9: same 84 players, outcome period held whole, measurement period capped
at 30/45/60/78) the constant runs **0.488 → 0.594**, and drift at K=30 is **+7.4 %**, not the +11.2 %
that was attributed to thinness. Depth explains +7.4 → +4.8; the rest was a different player set.

**The generalisable part is the error, not the numbers.** I compared two runs that differed in *two*
ways — sample depth and player set — and attributed the whole difference to the one I had a mechanism
for. Having a good explanation is what made it persuasive; it is also what stopped me looking for the
confound. A measured effect is only attributable to the variable that was actually isolated, and the
isolating run here cost nothing because the positions were already cached. **The cheap controlled
version should have come first, not second.**

---

### L-018 — A calibrated constant is a fitted parameter, and inherits every disease of one
**Date:** 2026-07-31 · **Cycle / mission step:** M3 (out-of-sample recalibration) · **Class:** process
**Context:** Cross-validating the target rule's constant after L-017 set it from measured drift.
**Observation:** In-sample the rule was met by 8 % of untreated players. **Out-of-sample it was
38 %** — optimistic by roughly five times. Worse, the two folds produced ratios of 0.385 and 0.518
and out-of-sample met-rates of **0/6 and 5/7**: from *nothing* to *nearly everything*, on the same
pipeline and the same kind of data.
**Lesson:** Calibrating against a control (L-017) fixed the *bias* and introduced a *variance*
problem, and the second is easy to miss because the first result looks so good. A constant read off
a distribution is a fitted parameter, and it needs the same treatment as any other: held-out
evaluation, and a look at how much it moves between folds. Where it moves that much, the honest
output is **no number at all** — the system's progress sign now states what was measured (rates
typically halve on their own) rather than a false-positive rate it cannot support. And the blocker
turned out not to be method but **sample size**: 13 predictions cannot calibrate a percentile, and
saying so is more useful than a figure that would not survive the next 13.
**Applied to:** `chesscoach/planner.py` (the claimed baseline share removed, constant kept
deliberately strict), `experiments/e05-natural-drift/calibrate.py`, and the withdrawal of the 8 %
figure everywhere it appeared.
**Resolved 2026-08-03, as this lesson prescribed.** The sample-size blocker it named was the real one:
at 57 predictions the fold spread narrows from 0.133 to **0.011** and 2-fold and 5-fold agree, so a
false-positive rate is stated again — the held-out 15 %, not the in-sample 12 %. The lesson stands;
what changed is that the data now supports a number. Note that the *second* half of it held too, and
harder than expected: see [[learning.lessons]] L-019, where refitting changed the constant by 70 %
because the underlying distribution had moved.

---

### L-017 — When theory and the control disagree, calibrate against the control
**Date:** 2026-07-31 · **Cycle / mission step:** M3 (fixing the target rule) · **Class:** technique
**Context:** Repairing the planner after E05 found 92 % of its targets met by doing nothing.
**Observation:** The principled fix — empirical-Bayes shrinkage, with the prior's strength estimated
from the peer population rather than guessed — moved it only from **92 % to 83 %**. Shrinkage
corrects for sampling noise, and the regression is much larger than sampling noise: the later rate
is a median **0.44** of the earlier one. Setting the target instead at a percentile of the *measured*
no-change distribution took it to **8 %**.
**Lesson:** A correction derived from a model of the noise only removes the noise the model knows
about. When the control says the effect is twice what the theory predicts, the control is measuring
something the theory omits — here, selection on statistical significance and possibly real
improvement over time, which this design cannot separate. Calibrating against the control fixes the
number without needing to know which. Two obligations follow: the constant must be **recalibrated**
whenever anything upstream changes, and it must be **fitted and tested on different players** — the
8 % above is in-sample and therefore optimistic, which is stated wherever it appears.
**Applied to:** `chesscoach/planner.py` (`NO_CHANGE_RATIO`), `chesscoach/peers.py` (shrinkage and
`prior_strength`), and the progress sign, which now states how often doing nothing would suffice.

---

### L-016 — Selecting a weakness guarantees it will look like it improved
**Date:** 2026-07-31 · **Cycle / mission step:** M3 (E05) · **Class:** technique
**Context:** Running the retrospective split across 32 players
([[experiments.e05-natural-drift]]).
**Observation:** **92 % of the plan's targets were met with no intervention whatsoever.** Mean
improvement without coaching was **+11.2 points** against targets asking for **+5.5**. Every one of
the thirteen predictions saw its rate fall in the later period — 19.6 % → 3.8 %, 22.5 % → 7.8 %,
25 % → 11 % — from players who were never told anything.
**Lesson:** This is regression to the mean, and it is **guaranteed by the selection**, not a tuning
error. A finding becomes a finding precisely because its rate was extreme in the measured period;
re-measuring an extreme value returns a lower one on average, with no change in the player. The more
selective the diagnosis, the larger the improvement it will appear to produce. Two consequences.
**Any** coaching system that measures, prescribes and re-measures will appear to work — which is
almost certainly what prior art reporting "your weakness improved" is reporting, since none of them
uses a control. And a target must be set against a **shrunk** estimate of the player's true rate, or
against a measured control, rather than against the selected value that produced the finding.
**Applied to:** [[experiments.e05-natural-drift]], risk R-15, the D7 score in [[state]] (reduced),
and the correction to L-015 below.

---

### L-015 — Build the control before claiming the treatment
> **Corrected 2026-07-31 by L-016.** The numbers in this lesson came from a single player who turned
> out to be the one exception in thirteen. It concluded that untreated drift is "about two points
> against a target asking for four and a half", and therefore that the targets were demanding. At
> scale it is **+11.2 against +5.5** — the reverse, and the targets are routinely met by doing
> nothing. The lesson's *instruction* — build the control before claiming the treatment — was right
> and is what caught this. Its inference from n=1 was not, and generalising from it was the mistake.
**Date:** 2026-07-31 · **Cycle / mission step:** M3 (progress check) · **Class:** technique
**Context:** First end-to-end run of the progress check, on a retrospective split of one player's
history: a plan built from their earlier 41 games, checked against their next 42.
**Observation:** The plan predicted a long-think error rate below **21.9 %**; the later games came in
at **24.4 %**, against 26.4 % before. Verdict **NOT MET**, recorded in the profile. The player never
saw the advice, so this is a **null condition**, and it is more informative than a success would have
been: it shows the check mechanism works end to end, and it puts a number on what "no intervention"
looks like — roughly two points of drift toward the mean, against a target that asked for four and a
half.
**Lesson:** A target that natural drift would satisfy is not a prediction, it is a coin-flip dressed
as coaching. The cheapest way to find out is a **retrospective split**: build a plan from a player's
earlier games and check it against their later ones, with no intervention in between. That is a
control condition costing nothing but engine time, and it should be run for every future target rule
before any claim is made about whether coaching works. Doing it first also means the first thing the
system ever got wrong was something it was *designed* to be able to get wrong.
**Applied to:** `chesscoach/progress.py`, the `check-progress` command, and
[[evaluation]] family F, where this is the cheap version of the longitudinal test.

---

### L-014 — What a rate is divided by decides what it measures
**Date:** 2026-07-31 · **Cycle / mission step:** M7 iteration 2 · **Class:** technique
**Context:** First run of S1 across 38 real players ([[mission.step-07-second-iteration]]).
**Observation:** `allowed_motif` produced 11 findings against `missed_motif`'s 2, and several players
carried *several* allowed findings at once. Being punished by every motif simultaneously is not a
pattern-specific weakness — it is erring more often. The denominator was the culprit: measured over
*all moves*, every allowed-motif rate scales with the player's overall error rate, so a weaker player
lights up for everything together. Re-measured over the player's **errors** — *when you go wrong,
what punishes you?* — the multi-allowed pattern disappeared and one player dropped out entirely.
**Lesson:** Before believing a rate, ask what it is divided by and what else moves that denominator.
A numerator can be perfectly correct while the rate measures something duller than intended, and the
symptom is suspicious *correlation between claims* — several findings arriving together for the same
players. This is the same shape as L-011, one level down: there the comparison was wrong, here the
denominator was. Both produce claims that are true and not about what they appear to be about.
**Applied to:** `chesscoach/sections/s1_tactical_gaps.py`, [[mission.step-07-second-iteration]],
and a check worth running on every future section: do its claims co-occur more than they should?

---

### L-013 — Population rates converge fast; individual verdicts at the boundary do not
**Date:** 2026-07-31 · **Cycle / mission step:** M7 · **Class:** technique
**Context:** Widening the peer reference from 7 players to 38 ([[architecture.peer-reference]]).
**Observation:** The population rate for the long-think condition moved from 17.7 % to **17.8 %** —
a seven-player sample had already estimated it to within 0.1 points across 3,675 moves. Yet
`esik24`, asserted at `priority` against the small reference, went **silent** against the wide one.
A 0.4 percentage point change in the peer rate flipped the verdict, because that player's confidence
interval straddles the population rate.
**Lesson:** These are the same fact seen twice. A small reference is fine for *estimating a
population* and unsafe for *judging a borderline player*, precisely because the borderline is where
a small shift in the reference decides the answer. Two consequences were applied. First, tiering was
wrong: `priority` was reached on **distinct-game count alone**, so a claim whose interval merely
grazed the population rate printed at the strongest tier. It now additionally requires the interval
to clear the comparison **by a margin** (1.25×), which regraded four of six findings from `priority`
to `focus`. Second, the tier follows the interval's *lower bound* rather than the point estimate, so
a player at 1.89× can rank below one at 1.78× — apparent size and strength of evidence are different
things, and the tier should track the second.
**Applied to:** `chesscoach/confidence.py` (`PRIORITY_MARGIN`), [[architecture.confidence]],
[[architecture.peer-reference]].

---

### L-012 — Self-baselines overstate by however much the population shares the behaviour
**Date:** 2026-07-29 · **Cycle / mission step:** M7 (peer reference) · **Class:** technique
**Context:** Building the rating-peer reference and re-running S2 against it
([[architecture.peer-reference]]).
**Observation:** Four players had apparent long-think weaknesses at 2.10–2.85× their own baselines.
Measured against a population of their peers, two disappeared entirely — one sat inside the
population rate, one *below* it — and the two that survived fell to 1.65× and 1.52×. The population
rate for that condition is 17.7 %, against individual self-baselines of 9–11 %.
**Lesson:** A within-player comparison overstates every effect by roughly the amount the behaviour is
universal, and the overstatement is invisible from inside one player's data. Concretely here it was
a factor of about 1.7 and it turned two non-findings into confident ones. Any coaching system without
a peer reference will over-report, and will do so most confidently on exactly the conditions that are
most universal — because those have the largest gap between the population rate and any individual's
"other moves". The display must also state the comparison actually used: showing a self-baseline lift
for a claim promoted on a peer comparison would misrepresent the evidence.
**Applied to:** `chesscoach/peers.py`, S2's peer-aware assertion, `_comparison_line` in the CLI,
and the resolution of open question C6.

---

### L-011 — A weakness most players share is a base rate, not a diagnosis
**Date:** 2026-07-28 · **Cycle / mission step:** M5 · **Class:** domain
**Context:** Running S2 on 135 real games across seven players, the first non-synthetic data in the
project ([[mission.step-05-assess-s2]]).
**Observation:** Four of six eligible players showed `long_think_error` at 2.10×, 2.22×, 2.31× and
2.85× against their own baselines. The uniformity was the finding. The mechanism is plain once seen:
a long think happens *because* the position is hard, and hard positions produce errors — the
condition is **selected by the same thing that causes the outcome**. A self-baseline cannot separate
"you are bad after long thinks" from "long thinks happen in bad positions".
**Lesson:** Before asserting a measured effect, ask whether the condition is *selected* by something
correlated with the outcome. Where it is, a within-player baseline is structurally incapable of
answering, and only a peer population can. Two practical consequences: conditions of this shape are
marked and **withheld** rather than reported (S2's `selection_confounded`), and the check should be
automatic — comparing findings *across* players would have caught this immediately, which is
evaluation metric D1 and is now promoted. More generally, this is why the peer reference corpus is
no longer optional: three separate lines of work (C6, D2, and S2's assertability) now depend on it.
**Applied to:** `chesscoach/sections/s2_decision_process.py`, [[mission.step-05-assess-s2]],
risk R-14, and the reordered priorities in [[state]].

---

### L-010 — When an agent fails its evaluation, suspect the fixture first
**Date:** 2026-07-28 · **Cycle / mission step:** M4 (S2) · **Class:** process
**Context:** Scoring the first agent against the planted `time_pressure` weakness.
**Observation:** S2 reported a `long_think_error` at 2.92× and missed the planted weakness entirely.
The agent was right and the fixture was wrong: the generator's time model made the flawed player
think slowly for its first ten moves, so "long think" coincided exactly with "early game", where
errors still cost win probability, while the planted time-pressure errors happened late, where they
compress toward invisibility (L-009). S2 had correctly found the strongest real pattern in the data
it was given.
**Lesson:** A failed evaluation is a claim about the *pair* of agent and fixture, and the fixture is
the newer and less-examined half. Before changing an agent, check what the fixture actually contains
— here, that a synthetic condition had been made to coincide with a confound. Two fixes followed,
one on each side: the generator now uses uniform think times so a time-pressure plant cannot be
confounded with a long-think signal, and **S2 now excludes moves played in already-decided
positions**, which is a genuine improvement that only surfaced because something was measured. Within
competitive positions the planted signal reads 37.7 % against 6.8 %, where across all moves it read
8.9 % — the decided positions had been burying it.
**Applied to:** `chesscoach/sections/s2_decision_process.py` (`DECIDED_CP`), `cli.py` time-model
options, [[mission.step-04-first-agent]], and `ScoreCard`, which now distinguishes *declined for
insufficient data* from *missed* — scoring an honest refusal as a failure would penalise the
behaviour the whole design is trying to produce.

---

### L-009 — A planted weakness is not automatically a *measurable* weakness
**Date:** 2026-07-28 · **Cycle / mission step:** M3 (evaluation harness) · **Class:** technique
**Context:** Building the planted-weakness generator, family C of [[evaluation]].
**Observation:** Two problems appeared as soon as the fixture was checked against the analysis core.
First, the initial fixture gave planted moves a 16.9 % error rate against **0.0 %** for the flawed
player's other moves — because outside the planted condition it played the engine's own choice. That
is a far easier discrimination than any real player presents, and any agent measured against it
would have been flattered. Second, only a minority of deliberately bad moves registered as errors at
all: once a game is decided, further bad moves cost almost no win probability, so the *measured*
severity of a planted flaw is diluted by the damage already done. Adding a background mistake rate
fixed the first problem and made the second visible — planted error rate fell from 16.9 % to 7.7 %
against a 4.3 % baseline, a lift of 1.81×.
**Lesson:** An evaluation fixture needs its own verification step before anything is scored against
it. Two requirements follow: **background noise**, so the flawed player is not perfect outside the
planted condition; and awareness that **win-probability labels compress in decided positions**, so a
weakness planted late in a lost game is nearly invisible. A fixture that cannot be seen by the
deterministic layer is not a test of any agent — it is a broken fixture, and `check-eval-set` exists
to catch that before it wastes a measurement.
**Applied to:** `chesscoach/evaluation/planted.py` (`background_severity`, and `write_eval_set`
refusing a set where nothing was planted), the `check-eval-set` command, and [[evaluation]]'s
limitations.

---

### L-008 — Held-out replication is not optional; the first striking result was an artefact
**Date:** 2026-07-28 · **Cycle / mission step:** M2 (E03) · **Class:** process
**Context:** Testing whether positional features predict a player's errors
([[experiments.e03-relevance-weighting]]).
**Observation:** Pooled analysis showed nothing. Stratifying by game phase produced a striking
effect — backward pawns in endgames with error lift 2.40 and 2.12 — together with a tidy mechanistic
explanation for why pooling had hidden it. On a held-out sample of four different players the same
measurement gave 0.88 and 0.76: not merely absent, **reversed**. With 8 features across 3 phases
there were 24 cells; the largest was always going to look impressive.
**Lesson:** Any association discovered by searching a space of measurements must reproduce on a
held-out sample of *different players* before it is written down as a finding — and a plausible
mechanism is not evidence, it is the thing that makes an artefact convincing. Practically: every
diagnostic rule the swarm ever uses gets discovered on one player set and confirmed on another, and
the same discipline becomes the B1 split-half test in [[evaluation]]. The cost of this replication
was ten minutes of engine time.
**Applied to:** [[experiments.e03-relevance-weighting]], risk R-13, [[evaluation]] T0 tier,
open question C6.

---

### L-007 — Detecting a feature is easy; knowing it matters is the hard part
**Date:** 2026-07-28 · **Cycle / mission step:** M1 (E02) · **Class:** domain
**Context:** Building positional feature detectors to resolve D4, the project's biggest technical risk.
**Observation:** Four positional concepts were detected with 16/16 hand-verified precision in a few
hundred lines of `python-chess` — no engine, dataset or model. But isolated pawns appear in 74.7 % of
sampled positions and 96 % of games, and rooks on open/semi-open files likewise. Worse, several
*correctly* detected outposts were edge knights in simplified endgames that no coach would ever
mention: the definition held, the relevance did not.
**Lesson:** The scarce resource in automated coaching is **relevance, not detection**. Any pipeline
step that outputs "feature X is present" must be paired with evidence that X *mattered* — through
co-occurrence with evaluation loss, recurrence across the player's games, or comparison against a
peer population. It also names a failure mode that no correctness test catches: **output that is
true, specific and useless.** That belongs in [[evaluation]] as something to test for explicitly.
**Applied to:** [[experiments.e02-positional-detectors]], [[domain.signals]], risk R-14, the M2 brief
(sections defined by what goes wrong, not by what is present).

---

### L-006 — A single move's error label is not a fact; a recurring pattern is
**Date:** 2026-07-28 · **Cycle / mission step:** M1 (E01) · **Class:** domain
**Context:** Measuring whether analysis depth changes the diagnosis
([[experiments.e01-engine-throughput]]).
**Observation:** Between depth 15 and depth 18, about a quarter of error labels disagree and one
blunder in six is seen by one setting and not the other. Depth 12 agrees with depth 18 on only 61 %
of labels. The disagreement concentrates at classification thresholds — moves landing just either
side of a boundary.
**Lesson:** Per-move claims are unreliable at any affordable depth; **aggregate, recurrence-based
claims are robust**, because threshold noise averages out over many instances while a genuine
weakness does not. Therefore: the swarm may say "you missed knight forks nine times across six
games"; it may not assert "move 23 was a blunder" as a bare fact. This turns the minimum-sample rule
(C2) from good practice into a correctness requirement, and it means analysis depth must be stored
with every derived signal — profiles built at different depths are not comparable.
**Applied to:** [[experiments.e01-engine-throughput]], [[domain.signals]], open question C2,
risk R-13.

---

### L-005 — Classify errors on win probability, not raw centipawns
**Date:** 2026-07-28 · **Cycle / mission step:** M1 (F1) · **Class:** technique
**Context:** Writing the E01 benchmark's error classifier, then reading Arrakis Engine's analyzer.
**Observation:** Arrakis converts centipawns to win probability with the Lichess formula
`winPct = 50 + 50 × (2 / (1 + exp(−0.00368208 × cp)) − 1)` before classifying moves. Raw centipawn
thresholds misrank badly at the extremes: losing 100cp at equality can decide the game, while losing
100cp at +900 is irrelevant — yet a fixed threshold labels both identically. They also cap evals at
±1000cp **and** force loss to 0 when the played move equals the engine's best move, documenting the
bug this fixes: mate-delivering moves such as `Qxf7#` otherwise register as 2000cp *losses*, because
Stockfish encodes mate as ±30000 internally.
**Lesson:** Error classification must operate on win probability, with an explicit mate/best-move
guard. Our E01 benchmark used raw centipawn thresholds and lacks the played-best-zero rule — it
measures throughput correctly but its labels need revising before they mean anything.
**Applied to:** [[domain.prior-art]]; `experiments/e01-engine-throughput/benchmark.py` (to revise);
open question C2.

---

### L-004 — Tactical motifs are deterministically detectable; be conservative about it
**Date:** 2026-07-28 · **Cycle / mission step:** M1 (F1) · **Class:** technique
**Context:** Reading Arrakis Engine's `motifs.py` while resolving F1.
**Observation:** Twelve tactical motifs (fork, pin, skewer, discovered check, mate threat, removing
the defender, hanging piece, trapped piece, back-rank mate, deflection, overloaded defender,
zugzwang) are detected by ~900 lines of pure Python over `python-chess` primitives plus a min-value
SEE heuristic — no LLM, no puzzle-database matching, and cheap enough to run only on critical moves.
The author states the detectors are deliberately conservative ("we'd rather miss a real motif than
tag a false positive") and documents a calibration failure where the skewer detector over-fired
10–18× before being constrained.
**Lesson:** Don't reach for a model where board logic suffices — the tactical half of diagnosis is a
solved, free, testable problem. Adopt **conservative-by-default** as a stated principle for every
detector: for a coach, a false positive is worse than a miss, because it sends the player to study
something that was never wrong. And calibrate each detector against real games; plausible-looking
detector code over-fires.
**Applied to:** [[domain.prior-art]], [[domain.signals]], risk R-13, the D4 framing in
[[open-questions]].

---

### L-003 — Diagnosis is computable; only explanation and dialogue need a language model
**Date:** 2026-07-28 · **Cycle / mission step:** M1 · **Class:** technique
**Context:** Answering M1 Q11–Q13 — which coaching diagnoses are computable from game data.
**Observation:** Nearly every diagnostic signal a coach uses (error rates by phase, missed tactics,
motif of the refutation, clock behaviour, conversion rates, repertoire performance) is derivable
from an engine plus parsing plus statistics, at zero marginal cash cost. The language model is
needed only for explaining, planning, and conducting dialogue. See [[domain.signals]] § 5.
**Lesson:** Architect the swarm to **compute first and speak last** — a deterministic analysis core
produces a structured player profile, and language models operate on that summary rather than on raw
games. Token volume then stays roughly constant per player instead of scaling with moves analysed,
which is what makes constraint C1 achievable at all.
**Applied to:** [[decisions.0002-compute-first-speak-last]] (proposed), [[domain.signals]],
[[capacity]] cost discipline.

---

### L-002 — Passive game analysis cannot tell a knowledge gap from a skill gap
**Date:** 2026-07-28 · **Cycle / mission step:** M1 · **Class:** domain
**Context:** Building the diagnosis taxonomy in [[domain.coaching]] § 2.
**Observation:** The same observable error — a hung knight — has at least four distinct causes
(missing knowledge, unexecutable knowledge, a broken checking habit, a psychological state), each
needing a different remedy. Absence of a correct move in a game is weak evidence of not knowing it,
and a correct move may have been played for the wrong reason. Games alone cannot separate these.
**Lesson:** The swarm needs an **active assessment** capability — probe positions where the player is
asked for a move *and its reason*, under controlled conditions — not only passive analysis. Player
interaction is therefore a core diagnostic capability, not a presentation layer added at the end.
**Applied to:** [[mission]] M3 brief, [[domain.signals]] § 3, [[state]] open questions.

---

### L-001 — The knowledge map determines the agent topology, so it must be revisable
**Date:** 2026-07-28 · **Cycle / mission step:** M1 setup · **Class:** process
**Context:** Framing M1 before doing the research.
**Observation:** M2 chunks the M1 knowledge overview into sections, and M4 builds one agent per
section. Any error or arbitrary boundary in the M1 map propagates directly into the swarm's
structure and is expensive to undo once agents exist.
**Lesson:** Treat the section catalogue as a versioned artefact with an explicit revision
procedure, and prefer boundaries that follow *how coaches diagnose* rather than how chess books are
organised — book structure is didactic convention, not diagnostic structure.
**Applied to:** [[mission.step-01-foundations]] (method + definition of done), and the M2 brief
in [[mission]].
