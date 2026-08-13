---
id: cas-domain-expertise-research
title: 'Chess expertise research — the primary basis'
desc: 'What the peer-reviewed literature says about the design decisions this swarm makes, including the two places it contradicts or embarrasses them.'
updated: 1786752000000
created: 1786752000000
---

# Chess expertise research

**Closes F2, partly** · **Date:** 2026-08-14 · Sources in [[domain.sources]]

[[domain.coaching]] was assembled from coach-authored websites and is honest about it: R-11 flags the
source base as *"commercial content marketing of variable rigour"*, and [[capacity.knowledge]] scores
coaching knowledge 2/5. That is a defensibility problem for a thesis — a reviewer may reasonably ask
why these claim kinds and not others, and *"a coaching site said so"* is not an answer.

This note traces the **load-bearing design decisions** to peer-reviewed work. Every quotation below is
verbatim from a source held in `docs/pdf/`, read directly rather than through a summary.

The primary text is **Gobet, F. & Charness, N. (2006), "Expertise in chess", in the *Cambridge
Handbook of Expertise and Expert Performance*, pp. 523–538** — a review chapter by two of the field's
central figures, [freely available from Brunel's repository](https://bura.brunel.ac.uk/bitstream/2438/1475/1/Gobet-Charness-CUP-chess%20expertise.pdf)
(constraint C7).

## 1. Expertise is pattern recognition, and this band is not short of calculation

> "the perceptual/memory advantage for skilled players was only obtained when they viewed
> **structured** chess positions. When pieces were randomly arranged on the board, there was little,
> if any, memory advantage for a Master player compared to a Class A player, compared to a novice
> player. This dissociation … suggested that **acquired patterns not innate abilities** accounted for
> skill differences." (Chase & Simon, 1973)

> "Computer simulations with CHREST show that at least **300,000 chunks** are required to reach
> grandmaster level."

**What it supports.** The swarm diagnoses *patterns* — motifs missed and conceded, structures, squares
— rather than telling players to calculate more deeply. That was chosen on coaching-site advice and
is the mechanism the expertise literature actually describes.

**And it goes further, into territory the swarm has not used.** On whether improvement in this band
comes from searching deeper:

> "Charness (1981a) suggested that **depth of search increases up to Expert level, after which it
> stays uniform**. Charness (1989) conducted a **9-year longitudinal investigation of a Canadian
> player who advanced … from an average level performance (1600 rating points) to International
> master level performance (2300 rating points) and found no significant increase in depth of
> search.**"

A player crossing exactly the range this project targets, improving 700 points, **without searching
deeper**. If that generalises, advice of the form *"calculate more carefully"* is aimed at the wrong
mechanism.

**Recorded as contested, not settled**, because the same page says otherwise:

> "Gobet (1997a) carried out computer simulations with the SEARCH model … and concluded that average
> depth of search keeps increasing with higher skill levels, but with **diminishing returns**."

One longitudinal case against one simulation. The honest reading is that search depth is **not the
main lever** in this band, which is weaker than "not a lever" and still enough to justify the design.

## 2. Playing faster costs less than expected — and this corroborates E19

> "Comparing the quality of play of world-class grandmasters in standard games (about 3 minutes per
> move) and rapid games (less than 30 seconds per move), **Chabris and Hearst (2003) found that this
> decrease of thinking time by a factor of six only marginally affected the number of blunders per
> 1,000 moves (5.02 in classical games vs. 6.85 in rapid games)**. … a substantial decrease in
> thinking time fails to increase the number of blunders substantially, which counts as direct
> support for theories emphasising pattern recognition."

**This is an independent published measurement of the thing [[experiments.e19-blitz-stratum]]
measured**, and it agrees:

| | population | time reduction | error ratio |
|---|---|---|---|
| Chabris & Hearst (2003) | world-class GMs | 6× | **1.36** (blunders/1,000) |
| **E19, this project** | 1400–1800 | ~2–3× | **1.06** (all diagnosable errors) |

Different populations, different error definitions, and the same shape: much less time produces only
modestly worse moves. E19 concluded blitz and rapid measure the same player and pooled the evidence;
that decision now has a peer-reviewed precedent rather than only an internal one.

**Also relevant to E25**, which found `instant_move_error` the most expensive shared weakness in the
band at 16.1 points a game:

> "Calderwood et al. (1988) showed that **masters can make relatively good decisions even under time
> pressure (about 5 s per move)**."

Masters lose little to hurrying; this band loses a great deal. That gap is the thing E25 identified as
shared, expensive and learnable, and it is exactly what a pattern-recognition account predicts —
recognition is fast, and players who lack the patterns must search, which is slow.

## 3. Transfer is narrow, which is why the claims are concrete

> "Didierjean, Cauzinille-Marmèche and Savina (1999) … The results show that **transfer was limited to
> problems perceptually similar to the examples and did not extend to problems requiring the use of
> the abstract principle behind the solution of these problems.**"

**What it supports.** Every claim the swarm makes names a concrete recurring pattern — *this motif*,
*this structure*, *this phase* — rather than a principle. A system that advised *"improve your
positional understanding"* would be aiming at the transfer this study says does not happen.

**And it is the mechanism behind the `FRAGILE` gap type**, introduced on the prober's evidence
(schema v4): a player who finds the right move for the wrong reason has something that will not
generalise. That was an inference from probe answers; this is the experimental result underneath it.

## 4. How much practice, and the honest ceiling

> "Few players reach master level performance with **less than 1000 hours of serious study** (Charness,
> Krampe & Mayr, 1996)."

> "deliberate practice and size of chess library were strong positive predictors, accounting in
> combination for **nearly 70 percent of explained variance** in current rating."

Note *explained* variance — a share of what the model accounts for, not of all differences between
players. Read alongside [[domain.sources]]'s existing Hambrick et al. (2014) entry (~one third of
*reliable* variance from deliberate practice), the two are not in conflict but are easy to quote as
though they were. **Neither licenses promising a player a rating gain**, which is why D1 refuses to.

## 5. The finding that embarrasses this project

> "**The necessity of having a coach is debated in the literature**; for example, Charness, Krampe and
> Mayr (1996) found a bivariate but not a unique multivariate correlation between chess skill and the
> presence of a coach in one sample; however, Charness, Tuffiash, Krampe, Reingold and Vasyukova
> (2005) did find it in another."

**Whether coaching helps at all is contested in the literature, and this project is building a
coach.** Recorded here rather than left out, because a supervisor or examiner will ask, and the
answer should not be improvised.

What can honestly be said:

- the 2005 study, with a larger and a new sample, **did** find coaching predicting rating
  independently of deliberate practice and tournament play;
- the disagreement is about *human* coaching measured retrospectively by questionnaire, which is a
  weak instrument — players remember whether they had a coach, not what the coach did;
- this project does not claim coaching works. It claims a system can **diagnose accurately and
  explain honestly**, and it declines to promise rating gains precisely because that claim is not
  supported.

Sitting next to this: [Sala & Gobet (2016)](https://www.sciencedirect.com/science/article/pii/S1747938X16300112)
find that chess instruction's benefits **transfer poorly to academic and cognitive skills**, and
[Sala & Gobet (2017)](https://journals.sagepub.com/doi/10.1177/0963721417712760) argue far transfer
is largely absent. Not a claim this project makes — worth citing to show it was checked, and to keep
the thesis away from *"chess makes you smarter"*.

## 6. The four-way gap taxonomy — sourced, and the names are inverted

The taxonomy in [[domain.coaching]] § 2 drives `GapTypeHypothesis` in the profile schema and its
provenance was *"found in M1"*. It is not this project's invention: it is a close relative of the
**Skill–Rule–Knowledge** classification (Rasmussen, 1979–1987) and the **slips/mistakes** distinction
(Norman, 1981; Reason, 1990), the standard framework for classifying human error in safety-critical
work. Read from
[Embrey, *Understanding Human Behaviour and Error*, Human Reliability Associates](https://mail.humanreliability.com/articles/Understanding%20Human%20Behaviour%20and%20Error.pdf),
held in `docs/pdf/`.

The foundational split is **intention against execution**:

> "**Slips** are defined as errors in which the intention is correct, but a failure occurring when
> carrying out the activities required. … **Mistakes**, by contrast, arise from an **incorrect
> intention**, which leads to an incorrect action sequence, although this may be quite consistent
> with the wrong intention. … Incorrect intentions may arise from **lack of knowledge** or
> inappropriate diagnosis."

And the three levels carry labels that could have been written for chess:

| SRK level | the article's label | its example |
|---|---|---|
| skill-based | **"misapplied competence"** | *"operator fails to close valve due to spatial confusion with another valve"* |
| rule-based | **"a failure of expertise"** | *"operator assumes reactor is OK based on one temperature indication which proves to be faulty"* |
| knowledge-based | **"a lack of expertise"** | *"operator fails to diagnose the causes of a severe abnormality under considerable time-pressure"* |

### The mapping

| this project | SRK / GEMS | fit |
|---|---|---|
| **knowledge gap** — doesn't know the pattern exists | knowledge-based mistake, *"a lack of expertise"* | **close** |
| **skill gap** — knows it, cannot execute under time or complexity | rule-based mistake, *"a failure of expertise"* | **close** |
| **process gap** — doesn't check threats, moves fast, no candidate comparison | skill-based slip, *"misapplied competence"* | **close** — and the article's listed causes are *"strong habit intrusions"* and *"situational changes that do not trigger the need to change habits"*, which is precisely "played it instantly because nothing prompted a check" |
| **psychological gap** — tilt, panic, risk aversion | **not an error type at all** | **the taxonomy is mixing two kinds of thing** |

**Two honest consequences, and the second is the more useful one.**

**The names are inverted against the standard framework.** This project's *"skill gap"* is the
literature's **rule-based** level, and this project's *"process gap"* is the literature's
**skill-based** level. Anyone reading the thesis with a human-factors background will trip over that.

**Not renamed, deliberately.** `PROCESS` and `SKILL` are what a chess player understands; *"a
skill-based slip"* is not, and the report is written for the player rather than for the literature.
The mapping is recorded here so the thesis can state it in one table and move on — which is cheaper
and clearer than a schema migration that would make the player-facing text worse.

**The psychological gap is a category error, mildly.** In SRK, stress and unfamiliarity are
**performance-influencing factors** that push a person *up* the levels toward effortful
knowledge-based processing — the article notes humans *"do not perform very well in high stress,
unfamiliar situations where they are required to 'think on their feet'"* — rather than a fourth kind
of error. The project's taxonomy lists three error types and one modifier as though they were four
peers. Worth stating rather than defending; it also explains why `PSYCHOLOGICAL` has never once been
assigned by any section.

### Where this project adds something

The slips/mistakes distinction is a 2×2 of intention against action, and the literature names only
three of its cells:

| | correct action | wrong action |
|---|---|---|
| **correct intention** | fine | **slip** *(process gap)* |
| **wrong intention** | **— unnamed —** | **mistake** *(knowledge gap)* |

The empty cell is *right move, wrong reason*, and it is exactly the project's **`FRAGILE`** gap type
(schema v4), introduced on the prober's evidence: a player who finds the move and explains it wrongly
holds something that will not transfer — which §3's transfer result then explains.

**The prober is the instrument that cell requires.** Separating intention from action needs the
intention observed independently, and a played move does not reveal it; that is why probes ask for a
move **and its reason**, and why [[domain.coaching]] concluded games alone cannot tell a knowledge gap
from a skill gap (L-002). That conclusion was reached from coaching sites; it is the same conclusion
the error literature reaches from the definition of a slip.

## What this changed

| | |
|---|---|
| **Nothing in the code** | every decision it touches was already made, and the literature supports rather than overturns them — which is the good outcome and would have been worth knowing either way |
| `domain.coaching` evidence base | four load-bearing claims move from coach-authored websites to peer-reviewed sources |
| A new caveat | whether coaching works is **contested**, and the thesis must say so rather than assume it |
| A corroboration | E19's pooling decision has independent published support |

## Still open

- **Intervention timescales** — open question D5, still unanswered. Nothing found here says how long
  a change takes to show up in results, which is why plans carry no time estimates.
- **The Steps Method** or another published curriculum, for comparison against the swarm's sequencing.
- **Instruction methodology** — the chapter says outright: *"Given the importance of deliberate
  practice in an entrepreneurial domain such as chess, one could expect that powerful training methods
  have been developed. **There is not much about this topic in the literature, however.**"* That is a
  gap in the field, not in this reading of it, and it is worth stating in the thesis as such.
