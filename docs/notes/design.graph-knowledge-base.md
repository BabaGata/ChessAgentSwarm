---
id: cas-design-graph-kb
title: 'Design — a graph knowledge base in Neo4j, and the constraint that decides its size'
desc: 'The author asked for a Neo4j graph holding what a chess coach knows. A graph is the right shape for three things the project has an actual hole for, and the binding constraint is not storage but sourcing: the last knowledge effort endorsed 3 of 14 entries. Staged so each stage is usable alone, with files as the source of truth and Neo4j as a derived index.'
updated: 1788249600000
created: 1788249600000
---

# A graph knowledge base

**Source:** the author, 2026-09-01 · **Status:** **plan, not built** — no code before this note is
checked against the vision (hard rule 2)

## The request

> *"Build the graph knowledge base with neo4j. This knowledge base will be used to store general
> knowledge about chess, chess coaching, general learning processes, typical knowledge about the
> chess understanding for players of different rank ranges, knowledge about openings, chess concepts,
> legal moves and everything that a real chess coach should know."*

## Why a graph is the right shape here

Not a general argument for graph databases — three specific holes this project already has, each
written down before this request:

**1. Prerequisite ordering, which the arbiter has a hole for and refuses to fill.** From
`chesscoach/arbiter.py`, unchanged since it was written:

> *"On prerequisite ordering. The spec lists it as a ranking criterion, and **it is deliberately not
> implemented yet** … among the claim kinds that currently exist, tactical and process weaknesses
> have no defensible ordering between them. **Inventing one would be fabricated pedagogy.** When a
> section emits a claim that genuinely depends on another, this is where that goes."*

The blocker was never the data structure. It was that nobody had written down which concept gates
which, with a source. A graph is where that goes, and `PREREQUISITE_OF` is its most natural edge.

**2. V6 path planning sits at 2/5**, and its gap is exactly traversal: *what should this player learn
next, given what they fail and what they have not yet mastered the prerequisites for*. That is a
query a flat store cannot answer and a graph answers in one hop.

**3. `domain.chess-concepts.md` already describes itself** as *"the domains of chess knowledge, their
concepts, **prerequisite structure and relevance by strength band**"* — which is the author's request
almost word for word, currently held as prose that no code can read.

So this is not a new idea grafted on. It is a structure the vault describes and the code has a hole
for.

## The constraint that decides how big it can be

**It is not storage. It is sourcing.**

[[experiments.e63-knowledge-swarm]] through [[experiments.e65-real-phrases]] built a drafting swarm
for exactly this kind of content and measured what it produced: **14 claims attempted, 3
endorsable.** Eleven were refused because no free source would support a definition — and the
refusals were the honest result, not a failure of the machinery.

[[design.knowledge-base]] states the reason and it applies with more force to a graph:

> *"A knowledge base of written chess explanations is **precisely the artefact most at risk** of
> laundering folklore into the system, and it would launder it into the one place that talks to the
> player."*

**A graph database produces no sources.** It changes where knowledge is kept, not whether it can be
obtained. At the measured rate, *"everything a real chess coach should know"* is thousands of nodes
against an endorsement capacity of three per fourteen — and the author is the only endorser.

This does not argue against building it. It argues that **the schema must make an unsourced node
unservable**, and that the plan must be staged so the first stages need no new chess knowledge at
all.

## What it must not hold

**Legal moves.** `python-chess` computes them exactly, for any position, in microseconds. There are
more legal chess positions than atoms in the observable universe, so they cannot be enumerated; and
C1 prefers deterministic computation over storage. What a graph *can* usefully hold is the
**relationships between named opening lines** — continuation and transposition — which is the CC0
book, already graph-shaped and already loaded.

I am reading "legal moves" as *"the coach must know the rules"*, and the answer is that it already
does, better than a graph could: the engine and `python-chess` are the rules.

**Anything with no source.** The gate below.

## The architectural decision that makes this safe

**Files stay the source of truth. Neo4j is a derived index, rebuilt from them.**

Every node comes from a file the repository already versions — `data/openings/book.json`,
`data/knowledge.json`, the Dendron notes, a new `data/knowledge/concepts.yaml`. A build step loads
them into Neo4j. Nothing is authored *in* the database.

Four reasons, and the last is the one that matters:

- **C5 auditable** — a claim's provenance is a line in a reviewed file, not a row someone inserted;
- **C3 self-hostable** — losing the database loses an index, never knowledge;
- reproducible — the graph is a pure function of the files, so two checkouts agree;
- **the review gate survives.** `reviewed: true` is the author's act and no drafting path may set it
  ([[design.knowledge-base]]). A database that can be written to directly is a way around that gate,
  and the gate is the only thing standing between this project and R-03.

## The model

**Nodes**

| node | what it is | where it comes from |
|---|---|---|
| `Concept` | fork, pin, outpost, backward pawn, king safety, development | `domain.chess-concepts`, `domain.positional-vocabulary` |
| `Claim` | one of the 57 things the detectors can say | the code — `measure()`, no authoring needed |
| `Detector` | the function that decides a claim | the code |
| `Opening` | a named line | `data/openings/book.json`, 3,810 CC0 rows |
| `Band` | 1400–1800, and the neighbours it does not yet serve | [[decisions.0005-scope-band-source-online-only]] |
| `Source` | a book passage, a URL, a paper | `domain.sources`, `chesscoach/books.py`, the guide library |
| `Practice` | a drill, a puzzle theme, an exercise set | Lichess puzzle themes (CC0), `domain.puzzle-themes` |
| `LearningPrinciple` | spacing, retrieval practice, deliberate practice | `domain.expertise-research` — already read and cited |

**Edges**

```
(:Claim)-[:DETECTS]->(:Concept)              which measurement evidences which idea
(:Detector)-[:DECIDES]->(:Claim)             so a claim can name the code that fired it
(:Concept)-[:PREREQUISITE_OF]->(:Concept)    the arbiter's missing structure
(:Concept)-[:EXPECTED_AT]->(:Band)           "typically understood by", with a source
(:Opening)-[:CONTINUES]->(:Opening)          the book's own tree
(:Opening)-[:TRANSPOSES_TO]->(:Opening)      same position, different move order
(:Practice)-[:TRAINS]->(:Concept)            what to actually do about it
(:LearningPrinciple)-[:GOVERNS]->(:Practice) why that drill, in that spacing
(:Concept|:Practice|:Band)-[:CITED_BY]->(:Source)
```

## The gate

**A `Concept` or `Practice` node with no `CITED_BY` edge to an endorsed `Source` may be stored and
may never be served to a player.**

Enforced three ways, because one is a suggestion:

1. a Neo4j constraint on the property that marks a node servable;
2. every read path goes through one function that filters on it — the same shape as
   `KnowledgeBase.show`, which **raises** rather than rendering blank;
3. a test that walks the whole graph and asserts no servable node lacks a source.

`Claim`, `Detector` and `Opening` nodes are exempt and it is worth saying why: a claim is the
**detector's specification**, not chess wisdom, and writing down what the code does is the opposite
of folklore. The opening book is CC0 reference data. Neither is a claim *about* chess.

## Staging — each stage usable on its own (C6)

**Stage 1 — the graph of what the project already owns.** Claims, detectors, openings, bands, and
the concepts already written and sourced in the vault. **No new chess knowledge is invented.** It is
a re-representation of things that exist, and it immediately buys: *which claims evidence the same
concept* (the overlap question E42 answers by measurement today), *which opening a claim fired in*,
and a place for stage 2 to attach.
*Done when:* the graph builds from files, a query answers "what does `allowed_motif.fork` detect",
and the build is reproducible.

**Stage 2 — prerequisite edges.** The one genuinely new structure and the one with a stated need.
Sourced from `domain.chess-concepts` § C and `domain.expertise-research`, and **explicitly refusing
to invent an ordering where none is sourced** — the arbiter's own position. Expect a sparse graph
and treat sparseness as honest.
*Done when:* the arbiter can ask "is A a prerequisite of B" and gets *yes*, *no*, or **unknown**, and
*unknown* is the common answer.

**Stage 3 — band expectations.** *"What a 1400 should understand"* is the hardest to source and the
easiest to invent. C7 says free materials; the honest starting point is what the literature in
`domain.expertise-research` actually supports, which may be very little.
*Done when:* every `EXPECTED_AT` edge cites something, or there are none and that is written down.

**Stage 4 — practice suggestions.** Deliberately last. [[design.knowledge-base]] already found this
the part *"the project's own research is most sceptical of"*, and the Lichess puzzle database (CC0,
themed, millions of puzzles) is the one free asset that could support it without prose.

## Cost (C1, C2, C3)

**Neo4j Community Edition is free and self-hostable** (GPLv3), runs on one machine, and the project
already runs local services — Ollama for the prober, SearxNG in Docker for search. So a second local
service is precedent, not a new class of dependency.

What it does add, and should be said plainly: a JVM, a running process, and roughly a gigabyte of
RAM where the runtime currently needs JSON files and SQLite. **The mitigation is the derived-index
decision above** — if Neo4j is not running, the pipeline loses graph queries and nothing else.

**A cheaper alternative exists and should be named rather than hidden**: `networkx` in-memory, built
from the same files, no service at all. It would answer every stage-1 and stage-2 query. Neo4j earns
its place if the graph outgrows memory or if Cypher's traversal makes stage 3 and 4 queries
materially better — and the author has chosen Neo4j, so the plan is written for it. The
derived-index design means switching later costs a loader, not the knowledge.

## What needs the author

1. **Is "legal moves" satisfied by the engine?** I have read it as the coach knowing the rules and
   proposed leaving it to `python-chess`. If something else was meant, stage 1 changes.
2. **Scope of stage 3.** Band expectations are the part most likely to become folklore. Worth
   deciding in advance how much unsourced structure is acceptable, if any.
3. **The endorsement rate is the real budget.** 3 of 14 is the measured throughput of the existing
   review workflow. A graph of any size needs either more sources, a lower bar, or the acceptance
   that most nodes stay stored-but-unservable. **My recommendation is the third**, and to make the
   unservable count a reported number rather than an embarrassment.

## Honest limitations

- **This plan does not solve sourcing**, and no schema can. It arranges knowledge so that the
  unsourced parts are visibly unsourced.
- **The prerequisite structure may turn out too sparse to rank anything.** That is a real possible
  outcome and stage 2's definition of done accepts it.
- **Nothing here is measured yet.** Every claim about what a graph buys is an argument; the first
  stage that ships should be scored against a query the flat store genuinely cannot answer.
