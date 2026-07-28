---
id: cas-domain
title: Domain Knowledge
desc: 'The chess and coaching subject matter the swarm must know — the output of mission step M1.'
updated: 1785254500000
created: 1785254500000
---

# Domain Knowledge

The subject matter of the coach: chess itself, and the practice of coaching it. This hierarchy is
the output of [[mission.step-01-foundations]] and the input to M2's section catalogue.

Distinct from [[capacity.knowledge]], which is about *how* knowledge is held and quality-marked.

## Notes

| Note | Contents | Status |
|---|---|---|
| [[domain.chess-concepts]] | the concept landscape and its prerequisite structure | first pass ✔ |
| [[domain.coaching]] | assessment, diagnosis, sequencing, progress tracking | first pass ✔ |
| [[domain.signals]] | what is computable from a player's games, with which free tooling | first pass ✔ |
| [[domain.sources]] | sources used, each with an evidence-quality note | first pass ✔ |
| [[domain.sections]] | the prioritised section catalogue | M2 — not started |

## Headline findings so far

1. **Ten knowledge domains** (K1–K10), of which two — practical process and meta-learning — are not
   "chess knowledge" in the classical sense but are among the strongest determinants of club results
   *and* the most machine-diagnosable.
2. **Four gap types** behind any error — knowledge, skill, process/habit, psychological — each
   needing a different remedy. This is the sharpest structural idea found and a strong candidate to
   become a first-class element of the swarm.
3. **Nearly all diagnostic signals are deterministic**, so the language model belongs at the
   explanation and dialogue layer, not the analysis layer ([[decisions.0002-compute-first-speak-last]]).
4. **Tactics are machine-labelled, strategy is not.** The Lichess CC0 puzzle database gives free
   motif labels; nothing comparable exists for positional concepts. This asymmetry will likely decide
   which agent is buildable first.
5. **Advice is band-dependent.** What is right at 1100 is wrong at 1900; the system must know which
   band it is coaching.

## Rules for notes in this hierarchy

1. Every claim carries a source and an **evidence class** (see [[capacity.knowledge]]).
2. Every claim states the **strength band** it applies to — advice that is right at 1000 is often
   wrong at 2000.
3. Prefer structure a diagnostician would use over structure a textbook would use (see L-001 in
   [[learning.lessons]]).
4. Mark whether a claim is **testable against a player's own games**. Untestable claims cannot
   drive automated coaching decisions.
