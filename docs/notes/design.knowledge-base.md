---
id: cas-design-kb
title: 'Design — a knowledge base for every detected claim, in two layers with different provenance'
desc: 'The author wants an entry per detector: what it is, why it matters, how to practise it, where to read more. The four parts have four different evidence classes and only one of them is safely writable by a model — so the design splits into a SPECIFICATION layer that the detectors are tested against and a PLAYER layer that is measured or linked. Options, arguments, and what I would change.'
updated: 1788912000000
created: 1788912000000
---

# A knowledge base for the detectors

**Source:** the author, 2026-08-30 · **Fills:** the *"runtime knowledge store — does not exist;
designed in M3"* row in [[capacity.knowledge]] · **Status:** design only, no code

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

## Option D — two layers, different rules for each **(recommended)**

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

## Sequencing

**Not all 33 claims.** An entry for a claim no player is ever told about is wasted work. Across the
review twelve only about fourteen claims ever reached a headline or a plan.

1. **Layer 1 for the claims that currently reach players** — highest value, no retrieval, and it
   doubles as the detector review the author asked for.
2. **The cost template**, which is code rather than content.
3. **Links**, through the existing swarm and approval gate.
4. **Practice**, last and smallest, sourced.

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
