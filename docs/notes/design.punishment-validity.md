---
id: cas-design-punishment-validity
title: 'Design — Was the punishment actually worth playing? Options for scoring a good-enough reply'
desc: 'A fork the opponent could play is not the players fault if playing it would have been bad for the opponent. Four options for deciding whether a punishing reply is good enough to count, drawn from epsilon-optimal action sets, satisficing aspiration levels, and the win-probability thresholds chess analysis already uses.'
updated: 1788656400000
created: 1788656400000
---

# Design — Was the punishment actually worth playing?

**Serves:** V8 (no unfalsifiable coaching), V4 (gap detection), C1 (free) ·
**Follows:** [[experiments.e84-band-references]] · **Status:** design, **options only — not decided**

## The problem, in the author's words

> *"If the player places his pieces with a potential of the fork, but doing the fork is a mistake
> because the opponent can eventually lose material or get checkmated, then entering a position where
> the player can get forked is not a mistake by itself."*

And the converse:

> *"The fork doesn't have to be the very best move by the engine. Sometimes the engine will prioritize
> some in-between move, like check and then forking, or some exchange and then forking. Also there
> could be an option for a checkmate but doing the fork for the opponent is still good for him and
> will gain material even if it is not the very best move."*

These are two failures of the same rule. `allowed_motif.X` currently fires when **the opponent's
single best reply executes X**. That is simultaneously

- **too strict** — it misses a fork that is excellent but second-best, a fork that arrives after a
  check or an exchange, and a fork that is merely good when mate was available;
- **too loose in the form we were about to adopt** — [[design.claims-that-do-not-separate]]'s
  formulation **C** counts *"the error left X available"*, and availability alone counts forks that
  would lose for the opponent, which the player is not at fault for allowing.

**The missing idea is a middle one: was the punishment *worth playing*?** Not best; good enough.

## What already exists, and what it does not cover

`chesscoach/tactics.py` is not naive about this. It already applies **local material validity**
through `chesscoach.material`:

| helper | what it rules out |
|---|---|
| `_lands_safely` | a "fork" that simply drops the forking piece |
| `_is_worth_winning` | a target the opponent is happy to trade on |
| `_loses_material_whatever_the_defender_does` | a fork where one reply saves everything |
| `_is_winnable` | a target that cannot be won once the exchange is counted |

All four are **static exchange evaluation** — they answer *"does this win material right here"* with
no engine and no search. What none of them answers is *"is this good **for the position**"*. A fork
can win a knight and still be losing, and SEE will never say so. That gap is exactly the author's
first case.

## Prior art

**No new chess claim is being invented here** (R-03) — the question is a general decision-theory one,
and three independent literatures answer it the same way.

### 1. ε-optimal action sets (reinforcement learning, decision theory)

An action is **ε-optimal** if its value is within ε of the best available. The suboptimality of an
action is its **action gap** (or **regret**), `V*(s) − Q(s,a)`, and bounding that gap bounds the loss
from choosing it. Directly relevant is the **set-valued policy** line of work, which returns *"the set
of near-optimal actions"* to a human decision-maker instead of one recommendation, precisely because
a single argmax throws away options that are almost as good and may be better on criteria the model
does not see — the situation here, where a coach cares that a punishment existed, not that a
particular engine ranked it first.

- [Clinician-in-the-Loop Decision Making: RL with Near-Optimal Set-Valued Policies](https://arxiv.org/pdf/2007.12678)
  — free preprint (C7). **Evidence class: secondary, methodological.** Used for the *shape* of the
  rule, not for any chess claim.
- [Near-optimal Regret Bounds for Reinforcement Learning](https://www.jmlr.org/papers/volume11/jaksch10a/jaksch10a.pdf)
  — JMLR, peer-reviewed, free. Source of the gap/regret vocabulary.

### 2. Satisficing and aspiration levels (Simon, bounded rationality)

Simon's **satisficing** replaces *"which option is best"* with *"does this option clear a standard I
set in advance"* — the **aspiration level**. Its three parts are an aspiration level, a rule for
judging options against it, and a stopping rule. The middle part is what is wanted here: a punishment
should be judged against a stated bar, not against the argmax.

- [Bounded Rationality, Satisficing, AI and Decision-Making in Public Organizations](https://onlinelibrary.wiley.com/doi/10.1111/puar.13540)
  — peer-reviewed (Public Administration Review). **Evidence class: secondary, methodological.**
- [When and How to Satisfice: An Experimental Investigation](https://www.york.ac.uk/media/economics/exec/heypermanaandrochanahastin/Satisficing%20Revised.pdf)
  — free working paper, University of York.

### 3. What chess analysis already does

Move classification on the major sites keys on **win-probability loss, not raw centipawns**, because
a 50-centipawn swing means different things in a balanced position and a decided one. The conventional
bands are **inaccuracy ≥ 5 %, mistake ≥ 10 %, blunder ≥ 20 %** of win probability. Separately, the
"only good move" label is defined by an **action gap**: the second-best option must be some margin
(≈18 wp) worse.

**This project already agrees with the first half independently.** `analysis/labels.py` holds
`INACCURACY_WP = 5.0` and `BLUNDER_WP = 30.0`, chosen before this note existed.

- **Evidence class: tertiary, commercial.** These are product blogs marketing analysis tools — exactly
  the source quality R-11 warns about, and they disagree with each other on the upper bands. Cited
  only as *"this convention exists and our own threshold matches it"*, never as authority.
  ([Chess It Up](https://chessitup.com/blog/chess-move-classifications-explained),
  [Chesslume](https://chesslume.com/blog/chess-move-classifications-explained),
  [ChessGrader](https://chessgrader.com/blog/chess-move-classifications/))

## The options

Throughout: `wp(m)` is the opponent's win probability after reply `m`; `best` is their best reply;
`stand` is the position as it stands before they reply.

### Option 1 — ε-optimal window ("it would not have been a mistake to play it")

A motif counts if **some reply within ε win-probability of the best** executes it.

```
allowed(X)  ⟺  ∃ m : executes(m, X)  ∧  wp(best) − wp(m) ≤ ε
```

**Choose ε = `INACCURACY_WP` = 5.0.** Not tuned — *reused*. The rule then reads: *a punishment counts
if playing it would not itself have been an inaccuracy, by the same standard we use to judge the
player.* That symmetry is the argument for it, and it means the threshold has one owner rather than
two.

- ✅ Answers "need not be the very best" — second-best forks count.
- ✅ Answers validity indirectly: a fork that loses material is nowhere near the best reply.
- ✅ Mate and a good fork can **both** be in the window, so nothing is lost when mate exists.
- ❌ **Fails in decided positions.** In a dead-drawn or dead-lost position every reply is within 5 wp
  of best, so a fork that achieves nothing counts. This is the option's real hole.
- ❌ Needs an evaluation per candidate move.

### Option 2 — Aspiration floor ("it actually gains something")

A motif counts if playing it **improves the opponent's position by at least δ** over the position as
it stands.

```
allowed(X)  ⟺  ∃ m : executes(m, X)  ∧  wp(m) − wp(stand) ≥ δ
```

This is Simon's aspiration level stated in position terms, and it is the direct answer to the
author's first case: the fork has to *win* something.

- ✅ Answers validity head-on.
- ✅ Mate and fork both clear the floor; both are recorded.
- ❌ **Fails in already-winning positions**, where everything gains and nothing distinguishes.
- ❌ δ has no natural owner — it would be a new tuned constant, which is what L-054 warns about.

### Option 3 — Both, which is the honest rule

Neither hole above overlaps the other: Option 1 fails where nothing matters, Option 2 fails where
everything does. Requiring both closes both.

```
allowed(X)  ⟺  ∃ m : executes(m, X)
                 ∧  wp(best) − wp(m) ≤ ε        (worth playing)
                 ∧  wp(m) − wp(stand) ≥ δ       (actually punishes)
```

**A punishment must be available, worth playing, and actually punishing.** This is formulation C with
the validity test the author asked for — call it **C′**.

- ✅ Everything Options 1 and 2 answer, without either hole.
- ❌ Two constants instead of one. δ can be softened by tying it to the *player's own* loss on the
  error — the punishment should recover a stated share of what the mistake gave away, which makes δ
  relative and removes the free parameter.
- ❌ Still does not catch the in-between move.

### Option 4 — Short principal-variation window ("check first, then fork")

Look for the motif not only in the immediate reply but **anywhere in the first *n* plies of a line
the opponent would actually play**, counting only the opponent's own moves.

```
allowed(X)  ⟺  ∃ line L, ε-optimal at every opponent choice,
                 ∃ ply p ≤ n in L where the opponent's move executes X
```

This is the only option that answers the author's second case — *"check and then forking, or some
exchange and then forking"* — and no threshold rule can, because the fork is not a legal reply yet.

- ✅ Catches zwischenzug and exchange-then-fork.
- ❌ **Attribution weakens with depth.** At ply 3 the player has moved again in between, so the
  finding is no longer purely about the move that was labelled an error. `n = 3` (their move, the
  forced reply, the fork) is the defensible limit; beyond that it is a different claim.
- ❌ Costs more search.

### Option 5 — Severity-ordered attribution (a reporting rule, not a detection rule)

Independent of 1–4, and it answers *"then here checkmate should be prioritized"*. When several motifs
qualify, **attribute the finding to the most severe** — mate, then material, then positional — while
**recording the rest as present**. Detection stays broad; what the coach *says* is ordered.

This is a pure reporting change and can ship with any of the above.

## Recommendation, for the author to accept or reject

**Option 3 (C′) as the eligibility rule, plus Option 5 for what gets said**, and **Option 4 deferred**
until 3 is measured. Reasons: 3 answers both of the author's cases that a single-threshold rule can
answer, using one constant the project already owns and one that can be made relative; 5 is nearly
free and answers the checkmate-priority point on its own; 4 is the most expensive and the one whose
attribution is weakest, so it should be justified by evidence that in-between forks are common enough
to matter — which is itself a measurable question and should be measured before it is built.

## Cost, before anything is built (C1, R-01)

The naive reading is a MultiPV analysis at every error position, which would be expensive. **It is not
needed.** Only the *candidate* moves need evaluating — the handful that execute a motif — and the best
reply's evaluation already exists in the stored observations.

A staged filter keeps it cheap, and the first stage is already written:

1. **Static, free:** discard candidates that fail the existing SEE checks. `wins_material` costs
   nothing and the detectors already run it.
2. **Cached:** where a candidate is the move actually played, its evaluation is already on disk —
   283,576 positions are in `data/cache/peers.db`.
3. **Engine, only for survivors:** one evaluation per surviving candidate.

**Unmeasured, and must be measured before building:** how many candidates survive stage 1 per error
position, and therefore the true engine cost of a reference rebuild. The D2 measurement gives an upper
bound on availability — a motif was available in roughly a third of errors — but availability is not
survival. **Estimated 40,000–80,000 engine evaluations for a full reference rebuild if stage 1 removes
little; possibly a tenth of that if it removes most.** That spread is too wide to build on, so
measuring it is the first task, not the second.

## What this forecloses

- **The peer reference must be rebuilt again** once the rule changes, and by now that is routine:
  `experiments/e84-band-references/build.py`, about fifty minutes.
- **`allowed_motif` rates will move**, so every recorded figure quoting them becomes stale, and the
  separation register must be regenerated — it is generated, so that is one command.
- **The claim's meaning changes** from *"what punished you"* to *"what you left available that was
  worth playing"*. That is the editorial change flagged in [[design.claims-that-do-not-separate]], now
  with the validity test that makes it defensible.

## Open questions this design does not answer

1. **Is δ relative or absolute?** Tying it to the player's own loss on the error removes a free
   constant but couples two measurements.
2. **How common is the in-between fork?** Option 4's whole justification. Measurable now, on the
   existing corpus, without building anything.
3. **Does C′ actually separate players?** Everything here improves *correctness*; nothing here
   promises the claim will discriminate. E84 found twelve claims flat within band, and a more correct
   denominator may leave them flat. Correctness and discrimination are different properties and this
   design only buys the first.
