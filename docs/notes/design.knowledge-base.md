---
id: cas-design-kb
title: 'Design — a knowledge base for every detected claim, in two layers with different provenance'
desc: 'The author wants an entry per detector: what it is, why it matters, how to practise it, where to read more. The four parts have four different evidence classes and only one of them is safely writable by a model — so the design splits into a SPECIFICATION layer that the detectors are tested against and a PLAYER layer that is measured or linked. Options, arguments, and what I would change.'
updated: 1788912000000
created: 1788912000000
---

# A knowledge base for the detectors

**Source:** the author, 2026-08-30 · **Fills:** the *"runtime knowledge store — does not exist;
designed in M3"* row in [[capacity.knowledge]] · **Status:** **Option C chosen by the author 2026-08-30** — the swarm drafts, the author approves, and LLM agents are used as far as they can be. Design only, no code

## The request

> *"This knowledge base will have information for everything that is being detected by detector.
> There will be an explanation of the motifs, like explanation what is fork, explanation why is good
> or bad whatever is detected and a couple of practice suggestions. The explanation what is the thing
> that is being detected should be used for you to review the design of detectors, also this should
> be used with prober to see if the player understands the information or not, and it will be used to
> explain to player what kind of mistakes are they doing. The rest should be used primarily to convey
> information to the player about what these weaknesses cost the players and a few ways on how to
> practice them. Everything should have links of the resources."*

Four parts, three consumers. **The parts do not share a provenance**, and treating them as one record
is the mistake this note exists to avoid.

| part | consumers | where the truth comes from | evidence class |
|---|---|---|---|
| **what is detected** | detector review, prober, player | the detector's own rule | `measured` — it is a specification |
| **why it matters / what it costs** | player | **this project's own corpus** | `measured` |
| **how to practise it** | player | outside sources, and thin ones | `single-expert` at best |
| **links** | player | the web, author-reviewed | n/a — a pointer, not a claim |

## The constraint that shapes every option

**R-03: LLM-generated chess advice is not a source.** Hard rule 7: every chess claim carries a source
and an evidence class. The prober's own code carries the reasoning already —
*"the motif name **is** the reason, and it came from a detector rather than from a model. This is
what keeps the agent clear of R-03."*

So a knowledge base of written chess explanations is **precisely the artefact most at risk** of
laundering folklore into the system, and it would launder it into the one place that talks to the
player.

**But three of the four parts escape this**, and that is the design:

- *what is detected* is not chess wisdom, it is **the detector's specification** — writing it down is
  the opposite of folklore;
- *what it costs* the project already **measures**, per player, in win probability;
- *links* are pointers, and the guide library already handles them under author review.

Only **practice suggestions** genuinely need outside authority, and they are the part the project's
own research is most sceptical of (below).

---

## Option A — one hand-written entry per claim, authored and sourced

The author writes all four parts for each of ~33 claims; sources cited; nothing generated.

**For:** highest quality, zero folklore risk, and the author is the chess expert the project already
relies on for every judgement.

**Against:** **the bottleneck is already visible.** 90 guide links sit at `reviewed: false` and 33
detection-sheet claims sit unmarked; the fork sample and the pawn sample are both waiting. Adding
~33 × 4 hand-written sections to that queue makes the knowledge base the thing that never ships. This
is the honest objection to the whole proposal in its stated form.

## Option B — derive everything that can be derived, write only the rest

- **what is detected** ← generated from the detector's docstring and its test fixtures;
- **what it costs** ← computed from the corpus, per claim and per player;
- **links** ← the existing retrieval swarm, author-approved as today;
- **practice** ← the only hand-written part.

**For:** cheap, self-updating, and **the derivation is a test**: if the docstring and the fixtures
disagree, one of them is wrong and CI can say so.

**Against:** a docstring is not a player-facing sentence, and the two audiences want different
registers. Deriving the player's text from code would produce something correct and unreadable.

## Option C — the existing swarm retrieves and drafts, the author approves

Reuse exactly what is built: Scout finds pages, Assessor discards with reasons, Compiler writes,
`RunStore.approved_brief` gates, the author approves point by point.

**For:** the machinery exists, works, and has a measured approval workflow with a run store behind
it. It is the shortest path to a populated base.

**Against:** the swarm's own weakness is measured and recorded — the WATCH half fails 0 of 6 in every
run, the Compiler invents or restates when the retrieved pages do not support a point, and
`_restates` had to be added because the grounding gate could not catch it. Pointing that at *"why is
a fork good"* — where confident-sounding text is abundant and cheap — is aiming it at the target it
is worst against.

## Option D — two layers, different rules for each

> **Not chosen.** The author picked **Option C** and asked that LLM agents be used as much as
> possible. Recorded because one piece of it survives regardless — see *"What the swarm must not
> write"* below.



Split by provenance rather than by claim.

**Layer 1 — the specification (internal).** One record per detector: the rule in prose, **what it is
not**, and the fixtures that pin it. Written by the author or derived from the tests; never by a
model. Consumers: detector review, and the prober.

**Layer 2 — the player-facing entry.** Cost measured from the player's own games, a worked example
from their own games, and **links** rather than prose. Practice suggestions only where a source
supports them.

**For:** each part is produced the way that part can honestly be produced; the expensive human input
goes only where nothing else can supply it; and layer 1 pays for itself immediately (below).

**Against:** two artefacts to keep in step, and the player layer is thinner than the author asked
for — it links rather than explains.

---

---

# The chosen design: Option C, and the one thing it must not do

The author's decision, after the arguments above:

> *"I want C — the existing swarm drafts, you approve. LLM agents should be used as much as
> possible."*

**One objection I raised is weaker than I made it sound, and I should say so.** I argued the swarm is
worst at exactly this target because confident chess prose is abundant and cheap to invent. But
abundance cuts both ways: the WATCH half fails on openings because the retrieved pages genuinely *do
not discuss* the opponent, so the Compiler has nothing to ground against and invents. Motif
definitions are the opposite — the web is full of real text about what a fork is. **The failure
mode therefore changes from *inventing* to *copying a mediocre source*, which is a different and more
manageable risk**: it is visible to a reader, it is catchable by the grounding gate, and it fails
loudly rather than plausibly.

So Option C is more likely to work here than it would have on the opening briefs, and the existing
machinery — Scout, Assessor, Compiler, `_restates`, the run store, `approved_brief` — carries
over unchanged.

## What the swarm must not write

**The precise specification stays with the author.** Not because a model cannot write a definition,
but because of what happened this session:

- the web's definition of a fork is *"one piece attacks two pieces at once"*;
- **that definition is what the broken detector implemented**, and it counted 1,014 double attacks
  where 3 were forks;
- what fixed it was the author's sentence — *"and the result is definite loss of material... if
  the bishop was defended the rook could be moved and there would occur only exchange of the pieces,
  not material loss"* — which no consulted source states.

**A retrieved definition is the vague version by construction.** Vagueness is invisible in prose and
fatal in a detector.

**But it is still worth retrieving**, for a reason the author's framing supplies: if the retrieved
definition and the detector's behaviour disagree, that disagreement *is* the detector review. So the
swarm drafts the definition, and it is used as **an independent cross-check against the code**, never
as the code's specification. The author's precise version sits beside it.

That keeps R-03 satisfied: the retrieved text is quoted with a source and an evidence class; the
authoritative rule is the author's.

## What each agent produces

Reusing the three roles rather than inventing new ones:

| agent | for a knowledge-base entry |
|---|---|
| **Scout** | queries per claim — *"what is a fork in chess"*, *"why are doubled pawns weak"*, *"how to practise tactics"* |
| **Assessor** | keeps sentences that **define or explain**, discards listicles and product pages, learns the skip list as today |
| **Compiler** | writes the four sections, each grounded in kept sentences |

Two checks it needs that the opening brief does not:

- **the definition section must quote rather than paraphrase**, because a paraphrase of a definition
  is where precision is lost and precision is the whole point;
- **the practice section must cite or be empty.** [[capacity.knowledge]] records that the expertise
  research found training-method evidence thin and coaching's value contested, so an unsourced
  practice suggestion is exactly the unfalsifiable coaching CLAUDE.md forbids.

## Why layer 1 is worth more than layer 2, and should be first

The author's own framing contains the strongest argument in the proposal:

> *"The explanation what is the thing that is being detected should be used for you to review the
> design of detectors."*

**This session is the evidence.** Three detectors were found to be wrong, and each failure was a
missing written specification:

| detector | what went wrong | what a written spec would have caught |
|---|---|---|
| `fork` | counted 1,014 double attacks where 3 were forks; every checkmate was a fork | *"a fork against two defended pieces is not a fork"* — the author's own sentence, unwritten until they said it |
| `late_castling` | charged moves where the engine wanted castling only **26 %** of the time | *"the alternative must be castling"* |
| `pawn_error` | **40 %** of instances were *"you pushed the wrong pawn"* | *"the alternative must be development"* |

Every one was found by a person reading positions, late, after the numbers looked good (L-050).
**A specification is the artefact that turns that from luck into a test.** The "what it is not"
section is the load-bearing half — all three defects were false positives, and a definition that only
says what a thing *is* cannot exclude anything.

Layer 1 also feeds the prober properly. Today `expected_reason` is the bare motif name, so a player
who says *"his knight and rook were both attacked and he could not save both"* is judged against the
string `"fork"`. A specification gives the classifier something to match against that is not a single
word.

## What I would change about the information retrieved

**Add — the cost, from the player's own games.** Not *"forks win material"* but *"this cost you 3.2
points of win probability a game, third-worst of your weaknesses"*. The project computes this
already. It is `measured`, it satisfies V8, and it is far more persuasive than any textbook sentence.
**Against:** it is per-player, so it cannot live in a static base — the base holds the template and
the number is filled at report time.

**Add — "what it is not".** Argued above. **Against:** it is the hardest part to write and the
easiest to leave vague.

**Add — prerequisites.** [[domain.chess-concepts]] already carries a prerequisite order. Telling a
player to work on forks when they hang pieces every game is bad coaching, and the plan has no notion
of ordering today. **Against:** it is a second ordering next to the arbiter's, and two rankings that
disagree is worse than one.

**Cut, or demote — "why it is good or bad".** For most detected things this is close to tautological:
*hanging a piece is bad because you lose a piece*. Author time spent writing that buys little, and
the measured cost says it better. **For keeping it:** for the *positional* claims — outposts, the
seventh rank, pawn structure — the "why" is genuinely non-obvious and is exactly what a player is
missing.

**Treat practice suggestions with more suspicion than the rest.** [[capacity.knowledge]] records that
the expertise research produced *"the two findings that do not flatter the project: coaching's value
is **contested**, and the field has **little on training methods**"*. Writing confident practice
advice would therefore contradict the project's own knowledge base, and *"do 20 puzzles a day"* is
exactly the unfalsifiable coaching output CLAUDE.md forbids. **Prefer linking to a resource over
prescribing a method**, and where a method is named, name its source and evidence class with it.
**Against:** the author asked for practice suggestions specifically, and a player who is told a
weakness and given no way to work on it has been diagnosed and abandoned. That is a real cost and it
argues for keeping them — but as *sourced pointers*, not as invented advice.

## The dependency: search has to work again

Option C is a retrieval design, and retrieval is currently blocked — Mojeek returned 403 and
DuckDuckGo a CAPTCHA, confirmed in the container logs. **The diagnosis matters, because the obvious
one is wrong for this project.**

**What this project actually does**, checked rather than assumed:

| the usual accusation | this codebase |
|---|---|
| generic `python-requests` User-Agent | `ChessAgentSwarm/0.1 (thesis research; opening guide lookup)` — honest and descriptive |
| parallel agents hammering an endpoint | sequential `urllib`, `POLITE_SECONDS = 1.5`, per-searcher spacing, 60 s back-off on 429 |
| brittle scraper libraries (`duckduckgo-search`, `googlesearch-python`) | none; a self-hosted **SearxNG** and the **Wikimedia API** |
| sending whole HTML to the model | sentences extracted, `is_usable_note` filter, chunked at 25 |

**So none of the standard causes apply, and the real one is structural:** SearxNG is a *metasearch*
proxy — it queries Google, DuckDuckGo and Mojeek on our behalf, and **those engines are blocking
the container**, not us. No change to this project's HTTP code can fix that, because this project is
not the thing making the blocked requests.

**Fixed 2026-08-30, and the cause was in the config all along.** `use_default_settings: true`
**merges** a top-level `engines:` list with the defaults rather than replacing it, so the four
engines the file listed were simply re-affirmed and **the other eighty stayed on**. Measured against
the running container: **84 engines enabled, including `brave`, `duckduckgo`, `google cse` and
`startpage`** — the exact four the file's own comment claimed were disabled. Every query fanned out
to all of them, so the CAPTCHAs were guaranteed rather than unlucky.

Two of the four names it listed, `marginalia` and `stract`, **do not exist in this image**, and
SearxNG ignores unknown engine names silently.

`use_default_settings: engines: keep_only:` is the setting that actually restricts the list.
**84 → 4**, and `mwmbl`'s timeout raised from 10 s to 20 s because it was timing out and a timeout
reads as an unresponsive engine, which is the same L-046 shape again. Verified live: three motif
queries return 6, 21 and 4 results with **no unresponsive engines**.

**Four routes, in order of preference:**

1. **Reconfigure SearxNG's engine list.** Disable the engines that block metasearch; enable ones that
   tolerate it. Free, inside C1 and C7, no key, no signup, and the examiner can reproduce it.
2. **Lean harder on APIs built to be called.** Wikimedia already works and needs no key. The same is
   true of other CC-licensed corpora, and for *motif definitions* — unlike opening plans —
   Wikipedia's coverage is genuinely adequate.
3. **A keyed provider with a hard local cap.** Google Programmable Search (100/day free) or Brave,
   which the author offered to configure *"if you can block searches that will go over the free
   limit"*. **Built: `chesscoach/quota.py`.** `MeteredSearcher` wraps any searcher and refuses the
   query that would exceed the tier, with three properties the free-tier problem actually needs:
   it **counts attempts rather than successes** (a timed-out request is still billed), it **refuses
   loudly** with a `SearchUnavailable` subclass rather than returning an empty list (L-046 again --
   *"we did not look"* must never read as *"the web has nothing"*), and it **persists** across
   processes, because a limit that resets on restart is not a limit. `keep_back` reserves part of
   the allowance so an automated run cannot consume the author's whole month.
   **Against:** it still needs a key, which means secret management and a signup an examiner cannot
   reproduce -- the exact objection `SearxSearcher`'s own docstring raises. **And a fact to check:**
   that docstring records *"Brave withdrew its free tier in February 2026"*, which contradicts the
   author's offer. One of the two is out of date and it should be established which before a key is
   created.
4. **Cache and reuse.** 33 claims is a small, fixed, slow-changing set. One successful crawl can be
   stored in the run store and never repeated, which turns a rate limit into a one-off cost.

**Two things from the general advice are refused, not deprioritised.** Spoofing a browser User-Agent
to defeat bot detection, and rotating proxies to evade IP blocks, are circumvention of access
controls the sites deliberately put up. They are also self-defeating here: the honest User-Agent is
*why* the Lichess and Wikimedia APIs work reliably, and an evasive one puts that at risk to gain
access to engines that have already said no.

## Sequencing

**Not all 33 claims.** An entry for a claim no player is ever told about is wasted work. Across the
review twelve only about fourteen claims ever reached a headline or a plan.

1. **Unblock retrieval** — SearxNG engine config first, since Option C cannot start without it.
2. **The claims that currently reach players**, not all 33: only about fourteen ever reached a
   headline or a plan across the review twelve.
3. **The cost template**, which is code rather than content and needs no retrieval at all.
4. **Practice**, last and smallest, cited or empty.

## What still needs deciding

| question | for the author |
|---|---|
| who writes layer 1 | the author's own words have been the specification every time so far; deriving it from docstrings is cheaper but circular — the docstring is what the code already believes |
| how much the player sees | links only, or short prose? Prose is what was asked for and is where R-03 bites |
| whether practice advice is prescribed or linked | argued above; my recommendation is linked |
| the storage format | JSON beside `guides.json`, following a precedent that works, versus notes in the vault derived at build time |

## Honest limitations

- **Nothing here is measured.** This is a plan, and the claim that layer 1 would have caught the
  three defects is a retrospective argument, not an experiment.
- **The bottleneck objection in Option A applies to every option**, including the recommended one.
  Anything requiring author review joins a queue that already has 90 unreviewed links in it.
- **"Derived from tests" is circular for detector review.** A specification generated from the code
  cannot catch the code being wrong; only an independently written one can. This is the strongest
  argument for the author writing layer 1 by hand, and it is why the recommendation does not lean on
  derivation for that layer.
