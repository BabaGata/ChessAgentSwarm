---
id: cas-domain-hard-concepts
title: Hard Concepts — Prophylaxis, Restraint, Harmony, Activity
desc: 'Whether the intent-level positional concepts can be detected, by semantic rules, engine assistance or machine learning.'
updated: 1785255800000
created: 1785255800000
---

# Hard Concepts

[[domain.positional-vocabulary]] rated roughly a third of the positional vocabulary as **hard or
open**: prophylaxis, restraint, piece harmony, piece activity. They form a coherent group — all are
about **intention and relation**, not arrangement, so they do not reduce to the board geometry that
made E02's detectors easy.

This note works out whether that group is actually reachable. **Conclusion: most of it is, and
machine learning is not the reason.** Three of the four have workable operational definitions using
rules plus engine assistance. The correction matters, so it is recorded rather than quietly applied.

## Route 1 — Semantic rules over board relations *(free, no engine)*

### Piece activity — **misclassified; this is not hard**

Activity has a standard operationalisation that E02's framing missed: **mobility**.

- Per piece: count the squares it attacks that are not defended by an enemy pawn (safe mobility),
  optionally weighted by square value (centre > edge).
- **Worst-placed piece** = the piece with the lowest safe mobility relative to its type's norm. That
  is a direct, computable rendering of "improve your worst piece", one of the most-taught principles
  in [[domain.chess-concepts]] K4.
- Trend over a game: is the player's average mobility rising or falling relative to the opponent's?

Cost: pure `python-chess`, comparable to E02. **Reclassify from hard to straightforward.**

### Piece harmony / coordination — **quantifiable as an index, not a boolean**

Harmony resists a yes/no answer but decomposes into countable relations:

- **Mutual defence:** how many own pieces are defended by another own piece.
- **Concentration:** how many own pieces attack the same square, and whether that square matters
  (adjacent to the enemy king, a weak square, a break square).
- **Self-obstruction:** own long-range pieces whose lines are blocked by own pawns — the bad-bishop
  computation generalised to rooks and queens.

Expect a composite index rather than a detection. That is acceptable: a coach saying "your pieces
work together noticeably less well than your opponent's in these games" is a real diagnosis, and it
is comparable against a peer population (C6).

### Restraint and blockade — **split it**

- **Blockade** is geometric and easy: a piece standing directly in front of an enemy passed pawn.
- **Restraint** in Nimzowitsch's broader sense is computable as *prevented pawn breaks*: enumerate
  the enemy's candidate pawn breaks (pawn moves that would open a line or challenge the centre), and
  check whether the break square is controlled by us more than by them. "How many of the opponent's
  freeing moves are currently unavailable" is a number.

## Route 2 — Engine-assisted definitions *(the key to prophylaxis)*

**Prophylaxis** is the genuinely hard one, because it is defined by what the opponent *wanted*. But
the engine can supply that intention, which turns it into a computable test:

> A move M by side A is **prophylactic** if:
> 1. M is quiet — no check, no capture, no immediate threat to win material; **and**
> 2. the opponent's best continuation *before* M is materially less good *after* M — i.e. their plan
>    move has lost its value; **and**
> 3. M does not gain by direct force (the evaluation change comes from denying, not from creating).

Operationally: analyse the position before M to obtain the opponent's best reply and its value;
analyse after M; check whether that specific reply has dropped. Two engine analyses per candidate
move — and E01 established the engine budget is not a constraint.

The same machinery yields the diagnostic that actually matters for coaching: **not "did the player
play prophylactically?" but "how often did the player allow the opponent's best plan when a quiet
preventive move existed?"** That is a failure the swarm can name, evidence, and prescribe against —
which satisfies the design rule in [[domain.sections]] that sections are defined by what goes wrong.

### The engine's own evaluation terms

Historically Stockfish's classical evaluation decomposed into named terms — mobility, king safety,
threats, space, passed pawns — which is a ready-made concept vocabulary with free numeric values.
Stockfish 18 is NNUE-based, so how much of that decomposition survives in the `eval` output must be
**checked, not assumed**. If it does, it is the cheapest concept source available.

## Route 3 — Machine learning *(possible, mostly not worth it)*

| Approach | Assessment |
|---|---|
| **Supervised classifiers** | Blocked by the original problem: training needs labelled positional examples, which is exactly what does not exist. Chicken and egg. |
| **Weak supervision from annotated games** | Extract concept labels from natural-language annotations in public PGN collections (e.g. Lichess studies) using a language model, then train on those. Workable in principle; noisy, and licence-sensitive under C7 — most well-annotated collections are copyrighted. |
| **Concept probing of chess networks** | The genuinely interesting research angle. Published work on AlphaZero probed the network's internal representations for human chess concepts, reportedly using engine evaluation features as concept targets. If the concepts are linearly decodable from a free network's activations, that is a label-free route. **Citation and method must be verified before relying on it.** Heavy for a thesis whose contribution lies elsewhere. |
| **Distillation from engine eval terms** | If the terms are available (above), a small model can be fitted to them — but if they are available, use them directly and skip the model. |

**Verdict: ML is not the unlock.** The reason these concepts looked undetectable was not missing
training data — it was missing *definitions*. Once each concept is given an operational definition,
three of four fall to rules plus engine calls, at a fraction of the cost and with full
explainability, which ML would sacrifice (V8 requires that every claim be traceable, and a learned
classifier's "this position shows poor harmony" is exactly the unfalsifiable output R-02 forbids).

Concept probing stays on the list as *future work*, not as a dependency.

## Priority — deliberately not now

Even granting all of the above: **do not build these next.** L-007 is the binding constraint. A
prophylaxis detector without relevance weighting produces the same true-but-useless output as an
isolated-pawn detector — it just costs more. The order is:

1. Solve relevance weighting (**C6**) on the concepts already proven in E02;
2. then extend the vocabulary with activity and restraint, which are cheap;
3. then prophylaxis, which needs the engine-assisted definition and its own experiment;
4. harmony last, as an index rather than a detector;
5. concept probing only if the thesis has room, which it likely will not.

## Consequences

- [[domain.positional-vocabulary]] ratings revised: **activity** hard → straightforward;
  **restraint** hard → split (blockade straightforward, restraint straightforward-with-definition);
  **prophylaxis** hard → tractable with engine assistance; **harmony** open → index, not detector.
- New open question **C7** in [[open-questions]] tracks the operational definitions and the
  Stockfish-eval-terms check.
- The "undetectable third" claim in earlier notes was **wrong**, and is corrected here rather than
  silently overwritten: it confused *no labelled data* with *no definition*.
