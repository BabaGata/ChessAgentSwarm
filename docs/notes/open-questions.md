---
id: cas-open-questions
title: Open Questions
desc: 'The live register of every unresolved question, who owns it, what it blocks, and how it gets resolved.'
updated: 1785254700000
created: 1785254700000
---

# Open Questions

The project's live register of unknowns. [[state]] says where we *are*; this note says what we
*don't know* and how each unknown gets closed.

**Rules.** Every entry has a stable ID (referenced from commits and other notes), an owner, what it
blocks, and a concrete resolution path — "think about it more" is not a resolution path. Entries are
never deleted; they are marked `resolved` with a link to where the answer lives. New questions get
appended with the next free ID in their section.

**Status:** `open` · `in-progress` · `resolved` · `deferred` (with a reason and a revisit trigger)
**Owner:** `author` = thesis author's decision · `agent` = resolvable by doing the work

---

## A. Measurement unknowns

*Unblocked as of 2026-07-28: Stockfish 18 (AVX2) installed at `C:\stockfish`, 20 cores available.*

| ID | Question | Status | Owner | Blocks | Resolution path |
|---|---|---|---|---|---|
| **A1** | ~~How long does analysing a player's games actually take?~~ **RESOLVED 2026-07-28** → [[experiments.e01-engine-throughput]]. **50 games in 27 s (depth 12), 89 s (depth 15), 403 s (depth 18)** on this machine, zero cash cost. Two surprises: more engine threads made fixed-depth analysis *slower* (1 thread is 2.9× faster per position than 16), so cores go to more games at once, not more threads per game; and wall time is dominated by the longest single game, so production should parallelise **per position**, not per game. **C1 is comfortably satisfied for the deterministic layer.** | resolved | agent | — | — |
| **A2** | ~~Does deeper analysis change the diagnosis, or only the evaluation?~~ **RESOLVED 2026-07-28 — and the answer is inconvenient.** It changes the diagnosis. Against depth 18: depth 15 agrees on 73.6 % of error labels and 83.7 % of blunders; depth 12 on 61.3 % / 69.2 %. **A single move's label is not a stable fact** (L-006). Aggregate recurrence-based claims survive; per-move claims do not. Working setting: depth 15 routine, depth 18 for discussed positions, **depth recorded with every stored signal** since profiles built at different depths are not comparable. | resolved | agent | — | — |
| **A3** | Is a local small LLM good enough for chess explanation and probe dialogue? | open | agent | C1, the language layer | Later benchmark: give one fixed structured profile to a local model and a hosted one; score both against a rubric. Do **after** the profile schema (C1) exists. |

## B. Scope & product decisions

*Not derivable from research — these are the thesis author's calls. Recommendations given.*

| ID | Question | Recommendation | Status | Owner | Blocks |
|---|---|---|---|---|---|
| **B1** | Target strength band | **1400–1800** | **RESOLVED 2026-07-28** → [[decisions.0005-scope-band-source-online-only]] | author | — |
| **B2** | Game source | **Lichess API first**, PGN upload as fallback | **RESOLVED 2026-07-28** → same ADR. Note it is a *game* source, not an analysis source — Lichess evals are absent for ordinary amateur games (E1) | author | — |
| **B3** | Over-the-board players in scope? | **No** — online play only | **RESOLVED 2026-07-28** → same ADR; recorded in [[vision]] non-goals | author | — |
| **B4** | Report, conversation, or both? | **Both, with the split settled** — the report is the durable artefact, the conversation is how assessment happens | **RESOLVED 2026-07-28** → [[architecture.interaction]] | agent | — |
| **B5** | Runtime language | **Python** — settled by use; the E01 harness already runs on `python-chess` + Stockfish | effectively settled | agent | — |

## C. Architecture questions for M3

| ID | Question | Status | Owner | Blocks | Resolution path |
|---|---|---|---|---|---|
| **C1** | ~~The structured player profile schema~~ **RESOLVED 2026-07-28** → [[architecture.player-profile]]. Typed Findings carrying evidence, provenance (incl. depth), uncertainty, peer comparison, context and gap-type determination; persistent across sessions. Each field is justified by the specific failure it prevents. | resolved | agent | — |
| **C2** | ~~Minimum-sample / confidence policy~~ **RESOLVED 2026-07-28** → [[architecture.confidence]]. Four tiers; counts in **distinct games**, never instances; gate at 10 games with data per section; `focus` requires held-out split replication; peer-band comparison rather than absolute thresholds. Thresholds are provisional and flagged for validation before the first agent ships. | resolved | agent | — |
| **C3** | ~~Orchestration pattern~~ **RESOLVED 2026-07-28** → [[decisions.0006-staged-blackboard-orchestration]]. Staged blackboard; section agents parallel and isolated; **no inter-agent messaging**. Conversational swarms rejected on cost, determinism, ablatability and explainability — and because agents measuring different things have nothing to argue about. | resolved | agent | — |
| **C4** | ~~Precompute-once vs per-player split~~ **RESOLVED 2026-07-28.** Per-player engine analysis is cheap enough (E01) that little needs precomputing; what is precomputed once is the **corpora** (puzzle themes, openings/traps, peer reference rates) and the shared position cache keyed by (position, engine, depth) → [[decisions.0007-storage-sqlite-cache-json-profile]]. | resolved | agent | — |
| **C5** | ~~Is [[decisions.0002-compute-first-speak-last]] accepted or rejected?~~ **RESOLVED 2026-07-28 — accepted.** Independent convergence with shipped prior art, plus E01 showing the deterministic layer costs ~89 s per player at zero cash. | resolved | agent | — | — |

## D. Domain knowledge gaps

| ID | Question | Status | Owner | Blocks | Resolution path |
|---|---|---|---|---|---|
| **D1** | ~~The deliberate-practice variance figure is cited from memory~~ **RESOLVED 2026-07-28.** Attributed: Hambrick, Oswald, Altmann, Meinz, Gobet & Campitelli (2014), *Intelligence* 45, 34–45 — deliberate practice accounts for **about one third of the reliable variance** in chess. Residual task: check the exact phrasing against the PDF before quoting (*reliable* variance ≠ total variance). Consequence for the vision: the swarm must never promise rating gains it cannot evidence. | resolved | agent | — | — |
| **D2** | ~~Mapping Lichess puzzle themes → the K2 motif list~~ **RESOLVED 2026-07-28** → [[domain.puzzle-themes]]. 75 themes taken from Lichess's own source file rather than the 250 MB dump. Mapped onto K2 in both directions. Two findings: (a) `quietMove` and `defensiveMove` are *calculation* skills with no slot in our concept map — a player who solves forcing puzzles but fails quiet ones has a specific nameable weakness, so **K3 gains a section**; (b) **not one positional tag exists** in the entire vocabulary, confirming the tactics/strategy asymmetry from a third independent direction. | resolved | agent | M2 | — |
| **D3** | Typical-plan catalogues per pawn structure | open | agent | any planning agent | Needs a primary source (classic middlegame material). Pairs with F2. |
| **D4** | ~~Can we build board-feature detectors for the positional taxonomy?~~ **RESOLVED 2026-07-28** → [[experiments.e02-positional-detectors]]. **Yes — 16/16 hand-verified, 15/15 unit tests, a few hundred lines, no engine or model.** The feared blocker does not exist. **But the risk relocated rather than vanished:** isolated pawns appear in 74.7 % of positions and 96 % of games, so presence carries almost no diagnostic information, and several *correct* outposts were edge knights no coach would mention. New question **C6** below inherits it. | resolved | agent | — |
| **C6** | **How is a detected feature weighted for relevance?** | **partially resolved 2026-07-28** → [[experiments.e03-relevance-weighting]] | agent | Tier 2 sections | **Route 1 (error co-occurrence) tested and largely negative.** Pooled lifts 0.87–1.26; drift no better; game phase predicts errors better than any feature; the one striking phase-stratified effect **failed to replicate on held-out players and reversed sign** (L-008). Only `own_outpost` held up across both samples and both measures — a lead, not a result. **Remaining routes:** peer-population deviation (asks whether the player is *unusual* rather than whether the feature predicts errors, so E03's result does not touch it — and the same free corpus doubles as evaluation metric D2); recurrence (C2 — measures consistency, not importance); and a new one E03 suggests, outcome-level association (does the player *score* worse in such games?). |
| **C7** | **Operational definitions for the intent-level concepts** — prophylaxis, restraint, harmony, activity *(new)* | open | agent | Tier 3 sections | → [[domain.hard-concepts]]. Activity reduces to safe-mobility metrics; restraint to prevented pawn breaks; prophylaxis to an engine-assisted test (a quiet move after which the opponent's previously-best continuation has lost its value); harmony to a composite index rather than a detector. Sub-task: **check whether Stockfish 18's `eval` still exposes decomposed evaluation terms** — if so it is the cheapest concept source available. Deliberately scheduled *after* C6. |
| ~~D4 (original entry)~~ | *(superseded — kept for the trail)* | resolved | agent | all positional agents | Still the biggest technical risk, but better posed. The original framing assumed no positional taxonomy existed; that was wrong — *My System* is a positional concept catalogue and Silman's imbalances are another. What is missing is **machine labels**, not vocabulary. So this becomes the same shape of problem as tactical motif detection, which prior art shows is tractable (L-004). Resolve by experiment: take 3–4 concepts from the free corpus (knight outpost, isolated queen's pawn, backward pawn, open file control), implement conservative detectors over `python-chess`, and check them against real games by hand. Report precision honestly. |
| **D5** | How long do coaching interventions take to show results? | open | agent | V6 time estimates | Weakest-evidenced part of the vision. Likely honest answer: give ranges, then *measure* whether the predicted progress sign appeared (V7 doing the work the literature cannot). |
| **D6** | Adult improvers vs. juniors — different sequencing and expectations? | open | agent | B1, M2 | Tier 2/3 reading in F2. |
| **D7** | Is there published methodology for eliciting knowledge in dialogue? | open | agent | V9 probe design | Search *educational assessment* literature, not chess literature — this is a general pedagogy problem. |

## E. Facts to verify before they are relied on

| ID | Claim | Status | Owner | Resolution path |
|---|---|---|---|---|
| **E1** | ~~Lichess API parameters~~ **RESOLVED 2026-07-28** by fetching 59 real games (`experiments/e01-engine-throughput/fetch_games.py`). `clocks=true` → `%clk` comments present ✔. `opening=true` → `ECO` + `Opening` headers present ✔. `division=true` → **no effect on PGN output** (it is a JSON-export field, not a PGN one). `evals=true` / `accuracy=true` → **returned nothing**, because *those games were never analysed on Lichess*. **This is the important finding: evaluations are only present for games a user chose to analyse, which for ordinary amateur games is rare. We cannot rely on Lichess-supplied evals and must run our own engine** — which makes A1 load-bearing rather than merely informative. | resolved | agent | — |
| **E2** | "50% of tournament games reach rook endings" — widely repeated, unsourced | open | agent | Verify against the Lichess database or drop it. Pleasingly, this is *computable* — a good early sanity exercise for the analysis pipeline. |
| **E3** | Puzzle database schema and size | in-progress | agent | Download the header and confirm. Pairs with D2. |

## F. Research debts

| ID | Debt | Status | Owner | Blocks | Resolution path |
|---|---|---|---|---|---|
| **F1** | ~~**Five prior-art projects identified but unread.**~~ **RESOLVED 2026-07-28** → [[domain.prior-art]]. All five cloned and read. Headlines: Arrakis Engine independently implements ADR-0002's architecture (so **C5 → accept**); its escalation-tier design is a concrete answer to **C2**; tactical motifs are deterministically detectable in ~900 lines of pure `python-chess` (L-004); error classification must use win probability, not raw centipawns (L-005); **none of the five evaluates whether its coaching is correct**, which makes [[evaluation]] genuinely novel work. Licence constraint found: Arrakis is **AGPL-3.0** (read and reimplement, never copy); Iamsdt/chess has **no licence** (unusable). Original entry follows. — **Five prior-art projects identified but unread.** What is recorded about them comes from *search-result snippets only* — no file has been opened, no licence checked, no architecture seen. Lead list, not knowledge. | open | agent | M3 (properly — designing before reading is the mistake) | Clone all five; read each against a fixed question list: ① licence ② architecture — does anyone else land on compute-first-speak-last? ③ motif detection technique ④ stateless vs. persisted player model ⑤ tokens/calls per game ⑥ do any of them *evaluate* coaching correctness (prediction: none — if so, that is a contribution claim for the thesis) ⑦ issues & README caveats. **Output:** `domain.prior-art`, with "what we adopt / avoid / do differently" — reusable as the thesis related-work section. |
| **F2 (revised)** | **Primary coaching sources unread — now under constraint C7 (free materials only).** The original plan named paid books; that is off the table except to unblock. **Revised free plan, in order:** ① **Capablanca, *Chess Fundamentals*** ([Project Gutenberg #33870](https://www.gutenberg.org/ebooks/33870), public domain in the USA) — graded pedagogy from a world champion, direct evidence for the band-dependent priorities; ② **Nimzowitsch, *My System*** (archive.org / Wikisource — *verify the specific edition's licence*) — the canonical positional concept catalogue, which is what D4 needs; ③ **Hambrick et al. (2014)** free full text on PubMed Central, to close D1's residual phrasing check; ④ **Gobet PDF already held** in `docs/pdf/`; ⑤ free descriptions of graded curricula (Steps Method syllabus, Lichess's own practice series) for *structure* rather than content. What we give up: modern graded curricula whose banding was F2's most attractive feature — revisit only if M2 is genuinely blocked without them. Original entry follows. — **Primary coaching sources unread.** [[domain.coaching]] rests on secondary web content, some of it commercial (risk R-11). Not defensible when an examiner asks on what basis the knowledge was decomposed — and that decomposition *is* the system architecture. | open | agent+author | M2 provenance, thesis defensibility | Target 4–6 sources that justify: (a) the concept decomposition → a published graded curriculum (Steps Method, Yusupov); (b) band-dependent priorities → a rating-banded course (Silman's endgame course); (c) the diagnosis taxonomy → Dvoretsky on training methodology; (d) learning-science claims → de Groot, Chase & Simon, Gobet, Hambrick. **Order: Tier 1 (peer-reviewed, free, retrievable) first** — strongest evidence and the material already cited without reading. For Tier 2 books, the published table of contents/syllabus structure is often enough for M2; only then decide what is worth buying. |

---

## Working order (proposed 2026-07-28)

1. **A1 + A2** — the engine benchmark. Unblocked, converts the largest unknown into a number, decides C5.
2. **F1** — read the five repos. Cheap, and must precede any M3 design.
3. **D2 + E1 + E3** — the mechanical verification batch; pairs naturally with A1.
4. **F2 Tier 1** — free primary sources; closes D1.
5. **B1–B3** — author's scope decisions, then M2.
