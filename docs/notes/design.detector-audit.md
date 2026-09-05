---
id: cas-design-detector-audit
title: 'Design — Auditing every detector, naming the pieces, and a reviewer that triages positions'
desc: 'The author read the detection sheet and found most detectors bad. Three pieces of work: audit each detectors position logic against the knowledge base, make detectors name the pieces involved and the move that would execute an unplayed motif, and build a local reviewer that flags implausible detections for the author rather than replacing them.'
updated: 1788656400000
created: 1788656400000
---

# Design — Detector audit, richer output, and a triage reviewer

**Serves:** V4 (gap detection), V8 (explainability), C1 (free) ·
**Follows:** [[design.punishment-validity]] · **Status:** plan, **not started**

## Why

The author read `experiments/e55-detector-precision/results/detection-sheet.txt` and reports that
**most detectors are bad** (time-related claims skipped). That is the instrument
[[learning.risks]] R-16 names as the only one that has ever caught this class of defect:

> *"Precision per detector, measured on hand-verified samples, is the only evidence that counts …
> treat an expert reading real output as a **required** instrument rather than a final validation
> step."*

The same sheet reports **29 claims with instances, 28 that never fired, 57 in the vocabulary**. Half
the vocabulary produces nothing at all, and of what remains the author judges most of it wrong. Note
that a claim that never fires and a claim that fires but cannot separate players
([[experiments.e84-band-references]]) fail the coach identically — both leave it with nothing true
and specific to say.

## The inventory to be audited

| module | detectors |
|---|---|
| `tactics.py` | `fork` `pin` `skewer` `discoveredAttack` `hangingPiece` `hangingPawn` `backRankMate` `removingTheDefender` `trappedPiece` |
| `material.py` | `moved_into_attack` `miscounted_exchange` `left_hanging` `ignored_threat` `sacrificed_for_attack` |
| `structure.py` | `isolated` `backward` `doubled` (+ `persistent`) |
| `squares.py` | `outpost` `open_files` `rook_seventh` (+ `rook_seventh_preventable`) |
| `kingsafety.py` | king-zone pressure |
| `development.py` | development measurement |

**Time-based claims are out of scope** for this pass, at the author's direction.

## A — Audit each detector against the knowledge base

For every detector, record in one table row:

1. **What it actually checks** — the board logic, read from the code, not from its name.
2. **What the knowledge base says the concept is** — the sourced definition now in the graph
   (`:Knowledge`, `:Rule`, `:Passage` nodes, [[design.graph-knowledge-base]]), with its source.
3. **Where they disagree** — the gap is the finding.
4. **Verdict** — aligned / narrower than the definition / wider than the definition / wrong concept.

**The knowledge base is the reference, and it is sourced** — that is what makes this an audit rather
than an opinion. Where the graph has no definition for a concept the code detects, *that is itself a
finding*: the detector is asserting a chess claim with no source behind it (R-03).

**Guard against L-053.** An audit that does not know intent manufactures defects. Several detectors
are deliberately **stricter** than the textbook definition, and the module says so — *"where a
definition could reasonably be read strictly or loosely, the strict reading wins"*, because prior art
had a skewer detector firing 10–18× too often. Narrower-than-the-definition must therefore be
recorded as a *deliberate* verdict where the code says so, not as a defect.

## B — Name the pieces, and the move that would have executed it

Today `detect_motifs(board, move) -> frozenset[str]` returns names only. The author wants the
detectors to yield **the pieces involved** and, where the motif was *not* played, **the move that
would have executed it**:

> *"like pawn on g3 can fork knights on h5 and f5 by moving it on g4"*

So the shape becomes an occurrence, not a label:

```
Occurrence(
    motif    = "fork",
    move     = g3g4,              # the move that executes it, played or not
    played   = False,             # was it actually played in the game
    attacker = g4,                # the piece doing the work, after the move
    targets  = (h5, f5),          # what it hits
)
```

**This serves V8 directly.** *"Your pawn on g3 could have forked the knights on h5 and f5 with g4"*
is a sentence a player can check on the board. *"You missed a fork"* is not. It also gives the
reviewer in § C something concrete to judge, and it gives the detection sheet something the author can
verify without replaying the game.

**It costs a scan of legal moves** where a motif is looked for but not played — the same cost measured
in [[experiments.e84-band-references]] at **10.5 ms per position**, and the same mechanism that was
built and reverted there. Reverted as a *denominator*, it remains correct as a *description*: knowing
which moves would execute a motif is exactly what naming the enabling move requires. **The code was
deleted with D2 and will be needed again here.**

## C — A reviewer that triages, and does not validate

A local agent reads each detected position and flags the ones that do not match the knowledge base's
definition, so the author reads a short suspicious list instead of 145 boxes.

**What it must not be.** It must not *validate* detectors. R-03 forbids LLM-generated chess judgement
as a source, and R-16 says hand-verified samples are the only evidence that counts. A model agreeing
with a detector is two systems sharing a guess.

**So its output is a queue, not a verdict:**

- input: a detected position (FEN, the occurrence from § B, the claim it produced)
- context: the sourced definition from the graph, retrieved by concept name
- output: `plausible` / `suspicious` + which part of the definition is unmet + its confidence
- effect: **`suspicious` positions go to the author.** Nothing is marked correct by the agent, and
  nothing is discarded by it.

**The asymmetry is deliberate.** A false "suspicious" costs the author one position to read. A false
"plausible" would silently retire a real defect — so the agent is never allowed to make that call.

**Its own accuracy is measured before it is trusted** (R-09, and the efficacy rules in
[[evaluation]]). Against a sample the author adjudicates: what share of positions it flags, and of
those, what share the author agrees are wrong. An agent that flags everything is useless in the same
way as one that flags nothing, and only the author's adjudications establish which it is.

**Cost:** local Ollama, one call per detected position, no API spend (C1). The detection sheet's scale
— hundreds of positions, not millions — makes this an outer-loop batch job.

## Order of work

1. **§ A audit** — cheapest, needs no code, and it determines whether § B is even worth doing on a
   given detector. A detector implementing the wrong concept should be fixed before its output is
   enriched.
2. **§ B enrichment** — starting with the motifs the audit finds sound, since enriching a wrong
   detector produces richer wrong output.
3. **§ C reviewer** — last, because it needs § B's occurrences as its input and § A's alignment table
   as its rubric.

## Definition of done

- Every detector in the inventory has an audit row with its four fields, and every "wrong concept"
  verdict has an issue recorded.
- Concepts detected but absent from the knowledge base are listed as sourceless, with a count.
- `Occurrence` replaces the bare motif name for at least the tactical detectors, with tests that the
  named attacker and targets are the squares a human would name.
- The reviewer runs on the detection sheet and produces a suspicious queue, **with its flag rate and
  its agreement with the author measured on an adjudicated sample** — not merely built.

## Open questions

1. **What is the knowledge base's coverage?** § A's reference only works where the graph has a sourced
   definition. If most concepts have none, the audit becomes a sourcing exercise first, and that
   changes the size of this work substantially. **Measure coverage before starting.**
2. **Do the 28 never-firing claims fail because of the detector or because of the gate?** A detector
   can be correct and still never fire if a threshold above it is wrong (L-055 — a guard that fires
   early hides what it caught). The audit must distinguish these, or it will rewrite working code.
3. **Does richer output change any measured rate?** It should not — § B is descriptive. If a rate
   moves, something was wrong in a way the audit did not predict, and that is worth catching.
