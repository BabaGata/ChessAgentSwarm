---
id: cas-domain-prior-art
title: Prior Art
desc: 'The five existing LLM chess coaches, read rather than listed: what we adopt, what we avoid, what we do differently.'
updated: 1785254800000
created: 1785254800000
---

# Prior Art

Resolves **F1** in [[open-questions]]. All five projects were cloned and read on 2026-07-28.
Previously this was a list of search-result snippets; it is now based on the source.

**Held locally** at `C:\Users\vujic\Documents\MachineLearning\ChessLLMs\`, alongside the Stockfish
wiki — re-readable without re-cloning. See [[capacity.knowledge]] § local reference library.

Also the raw material for the thesis's related-work section.

## Summary

| Project | Licence | Size | Architecture | Persistent player model | Evaluates coaching correctness |
|---|---|---|---|---|---|
| **bleongcw/Arrakis_Engine** | **AGPL-3.0** | ~13.6k lines Python + Next.js frontend, 240+ tests | 4-stage pipeline: harvest → analyse → coach → aggregate | **yes** — SQLite, cross-game patterns, escalation tiers | no |
| ai-chess-training/LLM-ChessCoach | MIT | 34 Python files | FastAPI + Stockfish + LLM, batch PGN → move feedback | no | no |
| akmenon1996/LLM-ChessCoach | MIT | 5 Python files | fetch → analyse → GPT commentary | no | no |
| renaissancebro/stockfish-coach | MIT | 11 Python files | interactive position Q&A over engine lines | no | no |
| Iamsdt/chess ("Chess King") | **no LICENSE file** | browser app, 61 JS/TS files | in-browser Stockfish 18 + hosted LLM | no | no |

**Licence findings that constrain us:**

- **Arrakis is AGPL-3.0** — the strongest copyleft, and it reaches network use. We may *read it and
  learn from it*, but we cannot copy code into this project without making the whole project AGPL.
  Everything below is recorded as a technique to reimplement, not code to lift.
- **Iamsdt/chess ships no licence file** → default "all rights reserved". Not reusable at all, only
  observable.
- The three MIT projects are freely portable, and are also the three least sophisticated.

## Arrakis Engine — the one that matters

A mature local coaching app (v1.27.4) written by a chess parent for their children. It is the
closest thing to our system that exists, and reading it changed several of our open questions.

### It independently arrived at ADR-0002

Their stated "core insight" is **two-step analysis**: Stockfish produces objective per-move
evaluations; a reasoning LLM interprets that engine output into coaching language. A third layer
aggregates patterns across games. That is [[decisions.0002-compute-first-speak-last]], derived
independently by someone who shipped it.

**Consequence: ADR-0002 should be accepted.** Independent convergence is the strongest evidence
available short of building it ourselves.

### Techniques worth adopting

| Technique | What they do | Why it matters to us |
|---|---|---|
| **Deterministic motif detection** | `motifs.py` — 12 pure-Python detectors over `python-chess` primitives (`board.attackers`, `board.is_pinned`, `gives_check`, a min-value SEE heuristic, PV-walking for mate look-ahead). No LLM, no puzzle-DB matching. Runs only on critical moves (\|cp loss\| ≥ 50–100). | Proves tactical motifs are **deterministically computable**. Directly relevant to D4 — and it sharpens the question: the answer for *tactics* is yes, cheaply. |
| **Conservative-by-design detectors** | "We'd rather miss a real motif than tag a false positive." | Exactly the right default for a coach that must not overclaim (R-13). Adopt as a stated principle. |
| **Anti-hallucination prompt clause** | "The coaching prompt explicitly warns the LLM not to invent motifs that weren't tagged." | Concrete mitigation for R-12 / R-02. The LLM may only speak about tags the deterministic layer produced. |
| **Structured trajectory block injected into prompts** | ~200–250 tokens of measured cross-game signals (weakest/strongest phase ACPL, tactical miss rate, endgame conversion, trend direction over weekly buckets, comeback/collapse rates, repertoire focus) plus a synthesised headline. | This *is* "LLM operates on the summary". It also gives us a real token budget: a rich player summary costs a couple of hundred tokens, not thousands. |
| **Coaching history injection** | last N coached games' lessons (~500 tokens each) fed into the prompt so the coach does not repeat itself and can build on prior advice. | Cheap mechanism for continuity (V7). Note the cost scaling — this is where their token budget actually goes. |
| **Win-probability conversion** | Lichess formula `winPct = 50 + 50 × (2 / (1 + exp(−0.00368208 × cp)) − 1)` before classifying errors. | Better than raw centipawns: 100cp matters enormously at equality and not at all at +9. **Our E01 benchmark uses raw centipawn thresholds and should be revised.** |
| **Mate-transition handling** | Cap evals at ±1000cp *and* record loss as 0 when the played move equals the engine's best move. Documented as a real bug: without it, mate-delivering moves like `Qxf7#` registered as 2000cp *losses* because Stockfish encodes mate as ±30000. | We would have hit this exact bug. Our benchmark clamps but lacks the played-best-zero rule. |
| **Escalation tiers — a real minimum-sample policy** | Per motif, they track **distinct-game spread** (`missed_games`, not raw instance count) and a **recency streak**. `none`/`watch`/`focus`/`priority`: spread ≥3 → watch, ≥5 → focus, ≥8 → priority; an active streak ≥3 boosts one level; the whole thing gated by ≥4 games with motif data "so new accounts can't false-alarm". | **This is a concrete answer to C2.** Someone has already designed a defensible confidence rule, including the distinction between *instances* and *distinct games* — which is the statistically important one. Adopt the shape; validate the thresholds ourselves. |
| **Fire-once alerting** | A priority-tier weakness files exactly one journal entry per episode; the row's existence is the dedup state. | Prevents a coach that nags. Small, and the kind of thing you only learn by shipping. |
| **Curated trap library from CC0 data** | `scripts/build_traps.py` pulls the Lichess `chess-openings` CC0 dataset, filters to named traps/gambits (≤16 plies), vendored as JSON so runtime has no network dependency → 1,475 traps, 3,690 openings. | A second free CC0 asset we had not identified. Directly useful for opening diagnosis, and the vendoring pattern is right. |
| **Engine settings in production** | depth 22, 6 threads, 512MB hash, configurable per-move time limit. | A real-world reference point for our A1 measurements. |

### Re-read in the source, 2026-09-13

Checked against the code held at `ChessLLMs/bleongcw-Arrakis_Engine-main`
rather than against this note. Three corrections and one addition.

- **Test count.** This note said "240+". The README says **725 backend + 228
  frontend**. The thesis had repeated the smaller figure, which understates the
  prior art by four times — the worst direction for that error to run.
- **Motif count.** Twelve here; the source has **15** tactical identifiers
  (fork, pin, skewer, deflection, discovered_check, back_rank_mate,
  hanging_piece, mate_threat, overloaded_defender, removing_defender,
  trapped_piece, zugzwang and others). Still tactical only — nothing positional.
- **One LLM call per game confirmed by counting.** `call_provider` appears once
  in `coach.py`, at line 1045.
- **New, and the strongest differentiator we had not written down: Arrakis
  never compares a player to anyone else.** `peer`, `cohort`, `percentile`,
  `population`, `baseline` return nothing in `src/` but Python exception names.
  Escalation rides on distinct-game spread and a recency streak — absolute
  counts. There is also no interval, no significance test, no scipy or
  statsmodels anywhere. So a weakness every 1500 has escalates exactly like one
  that is genuinely unusual. That is the thing this project exists to do
  differently, and it was missing from the thesis's list of differences.

Also confirmed by search, with nothing found: ground truth, ablation, control
group, expert review, inter-rater agreement, held-out set — and no code that
asks the player anything, and no predicted rate to re-check later.

### The other four, re-read in the source too, 2026-09-13

- **The two LLM-ChessCoach projects are one lineage, not two systems.** Same
  MIT copyright holder (Abhijit Krishna Menon, 2023), same filenames,
  `analyze_games.py` 850 lines against 127 and `api_server.py` 788 against 70.
  The larger is an expanded, productised version of the smaller — Dockerfile,
  Apple auth, an app store module. So the review covers **four codebases, one
  of them in two development stages**, and the thesis now says so.
- **CoachFish asks questions, in the other direction.** Its coaching prompt
  says "End with a short question to engage the user" and its adapter exposes
  `answer_question(question)`. "Nijedan sustav igraču ništa ne pita" was
  therefore contestable as written. The precise claim, which holds: no answer
  is recorded and no answer changes what the system concludes. Reworded.
- **ai-chess-training does persist to SQLite, but it is billing.** `users`,
  `user_entitlements`, `daily_usage`, `subscriptions`,
  `app_store_transactions`. No player model, so the table row stays "ne".
- **No evaluation of advice anywhere in any of the four.** Ground truth,
  ablation, expert review, control group and inter-rater all return zero files
  across every repository. akmenon1996 and CoachFish have no tests at all;
  ai-chess-training has 12 test files, Iamsdt 5.
- File counts here said 61 JS/TS for Iamsdt; excluding `node_modules` it is 32.

### Where they stop, and we do not

These are the honest gaps — and collectively they are this thesis's contribution claim:

1. **No evaluation of coaching correctness.** 240+ tests, but they test *code* (motif detectors,
   aggregation maths, pipeline wiring), not whether the coaching advice is right. There is no ground
   truth, no expert comparison, no ablation. My earlier prediction that none of the five would
   evaluate coaching quality **held for all five**. [[evaluation]] is therefore genuinely novel work,
   not a reinvention.
2. **One LLM call per game, not a swarm.** A single coach prompt does narrative, key lesson,
   practical focus, critical moments, opening analysis and a letter to the player. No specialisation,
   no per-domain expertise, no orchestration — so no agent can be evaluated or improved
   independently. That is precisely what our M4/M5 loop is for.
3. **No active assessment.** Everything is inferred from games. Nothing ever asks the player a
   question or probes their understanding. So they cannot separate a knowledge gap from a skill gap
   (L-002) — the system will happily "teach" a concept the player already knows but cannot execute
   under time pressure. **V9 stands as a real differentiator.**
4. **No prerequisite/curriculum model.** Weaknesses are surfaced and escalated, but there is no
   notion of what should be learned *before* what, no band-dependent priorities, and no ordered
   learning path with time estimates and expected progress signs (V5, V6). It reports; it does not
   plan.
5. **Motifs are tactical only.** Twelve tactical themes, nothing positional. The
   tactics-are-labelled/strategy-is-not asymmetry (D4) is unaddressed there too, which suggests it is
   genuinely hard rather than merely unattempted.

### Also worth noting

"Hunter Mode" — profiling an *opponent's* public games for targeted preparation. Out of scope for us
(the vision is about coaching one player), but a good example of the same analysis core serving a
second purpose, which is an argument for keeping the analysis layer agnostic about who it is
analysing.

## The other four, briefly

- **ai-chess-training/LLM-ChessCoach** (MIT) — the most engineered of the small ones: FastAPI,
  Pydantic schemas, a Stockfish wrapper with **MultiPV and mover-perspective loss**, batch PGN →
  `MoveFeedback` + summary, Redis-backed live sessions, and an **LLM coach with a rule-based
  fallback**. That fallback is a good pattern: the system still says something useful when no model
  is available — worth copying for C1. Stateless per analysis; no cross-game model.
- **akmenon1996/LLM-ChessCoach** (MIT) — the minimal baseline: fetch from Lichess, analyse, feed to
  GPT, show commentary. Useful in the thesis as the "naive approach" comparator.
- **renaissancebro/stockfish-coach / CoachFish** (MIT) — interactive Q&A about a single position,
  LLM translating engine lines into English. No player model, no history; it is a *position*
  explainer rather than a coach. Relevant only to our explanation layer.
- **Iamsdt/chess / "Chess King"** (no licence) — a browser app running Stockfish 18 client-side with
  hosted LLM explanations, puzzles, openings, endgames. Interesting as proof that the engine can run
  entirely client-side (zero server cost — relevant to C1), but unusable as a source.

## What this changes

| Open question | Effect |
|---|---|
| **C5** — accept ADR-0002? | **Yes.** Independent convergence by a shipped system. |
| **C2** — minimum-sample policy | Adopt the *shape* of Arrakis's escalation tiers: distinct-game spread + recency streak + a games-with-data gate. Validate thresholds on our own data. |
| **D4** — positional classification | Unchanged, but narrowed: tactical motifs are cheaply computable (12 detectors, pure python-chess). Nobody has done positional. Still the biggest technical risk. |
| **C1** — player profile schema | Their `move_analysis` / `player_patterns` / `game_coaching` split is a working reference. Ours must additionally carry gap *type* and evidence, which theirs does not. |
| **[[evaluation]]** | Confirmed novel. None of the five evaluates whether the coaching is correct. |
| **[[capacity.tools]]** | New free asset: Lichess `chess-openings` CC0 dataset (traps/openings). |

## Lessons filed

L-004 (deterministic motif detection is proven, and conservative-by-design is the right default) and
L-005 (win-probability conversion beats raw centipawns for error classification) → [[learning.lessons]].
