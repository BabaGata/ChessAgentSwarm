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
