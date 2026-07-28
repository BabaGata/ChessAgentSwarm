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
| **A1** | **How long does analysing a player's games actually take on this machine?** | in-progress | agent | everything in M3; [[decisions.0002-compute-first-speak-last]] | Fetch ~50 real games. Analyse at depth 15 / 18 / 20 and at fixed movetime, across 1 / 4 / 16 threads. Produce a table of seconds-per-position, seconds-per-game and total wall clock. **This is the single most consequential number in the project.** |
| **A2** | Does deeper analysis change the *diagnosis*, or only the evaluation? | in-progress | agent | cost architecture | Same 50 games at depth 15 vs 20: do blunder/mistake labels and the identified weakness set actually differ? If not, use the cheap setting permanently. |
| **A3** | Is a local small LLM good enough for chess explanation and probe dialogue? | open | agent | C1, the language layer | Later benchmark: give one fixed structured profile to a local model and a hosted one; score both against a rubric. Do **after** the profile schema (C1) exists. |

## B. Scope & product decisions

*Not derivable from research — these are the thesis author's calls. Recommendations given.*

| ID | Question | Recommendation | Status | Owner | Blocks |
|---|---|---|---|---|---|
| **B1** | **Target strength band for the first end-to-end slice** | **1400–1800** — the band where sources agree losses come from individual recurring weaknesses rather than generic blunders, i.e. exactly where personalised diagnosis beats generic advice | open | author | M2 priorities, M3 design, evaluation set |
| **B2** | Where do the player's games come from? | **Lichess API first** (free, documented, shares an ecosystem with the puzzle DB and opening explorer); PGN upload as fallback; Chess.com later | open | author | data layer |
| **B3** | Are over-the-board players in scope? | **No.** No digital game record means the entire signal layer is unavailable. A defensible thesis scope limitation | open | author | [[vision]] non-goals |
| **B4** | Report, conversation, or both? | **Both** — M1 showed the probe dialogue is load-bearing (V9), so it cannot be deferred to "the UI later" | open | author | M3 interaction design |
| **B5** | Runtime language | **Python** — python-chess, the data ecosystem and the engine driver all live there | open | agent | M3 |

## C. Architecture questions for M3

| ID | Question | Status | Owner | Blocks | Resolution path |
|---|---|---|---|---|---|
| **C1** | **The structured player profile schema** — the typed artefact every agent reads and writes | open | agent | every agent, [[evaluation]] | Derive from the four gap types ([[domain.coaching]] § 2) plus the signal inventory ([[domain.signals]] § 2). Design **after** F1 — this is precisely where other projects' mistakes are instructive. Most load-bearing artefact in the system. |
| **C2** | **Minimum-sample / confidence policy** — when may the swarm assert a weakness? (risk R-13) | open | agent | first diagnosis agent | Write an explicit rule (e.g. ≥N occurrences across ≥M games within one time control, reported with a confidence band), then **validate it**: run on a player, hold out half their games, check the diagnosis reproduces. Highly testable; strong thesis section. |
| **C3** | Orchestration pattern — pipeline, blackboard, or planner-with-specialists? | open | agent | M3 | Falls out of C1 plus F1. Do not decide in the abstract. |
| **C4** | Precompute-once vs. per-player computation split | open | agent | M3 | Falls out of A1. |
| **C5** | Is [[decisions.0002-compute-first-speak-last]] accepted or rejected? | open | agent | M3 | Decide after A1 and A2. |

## D. Domain knowledge gaps

| ID | Question | Status | Owner | Blocks | Resolution path |
|---|---|---|---|---|---|
| **D1** | The deliberate-practice variance figure is **cited from memory, unverified** | open | agent | thesis honesty | Retrieve the Hambrick et al. (~2014) meta-analysis, check the number, or delete the claim. Nothing unverified enters the thesis. |
| **D2** | Mapping Lichess puzzle themes → the K2 motif list | open | agent | M2, first agent | Mechanical: download the puzzle CSV, extract distinct theme tags, map onto [[domain.chess-concepts]] K2. ~30 minutes; directly seeds M2. |
| **D3** | Typical-plan catalogues per pawn structure | open | agent | any planning agent | Needs a primary source (classic middlegame material). Pairs with F2. |
| **D4** | **Can positional concepts be classified without labelled data?** | open | agent | all positional agents | **The biggest open technical risk.** Tactics have free machine labels; strategy has none. Resolve by experiment: pick one board-computable positional feature (knight outpost, IQP), verify it detects reliably, see how far it generalises. If it does not, positional agents need a fundamentally different design. |
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
| **F2** | **Primary coaching sources unread.** [[domain.coaching]] rests on secondary web content, some of it commercial (risk R-11). Not defensible when an examiner asks on what basis the knowledge was decomposed — and that decomposition *is* the system architecture. | open | agent+author | M2 provenance, thesis defensibility | Target 4–6 sources that justify: (a) the concept decomposition → a published graded curriculum (Steps Method, Yusupov); (b) band-dependent priorities → a rating-banded course (Silman's endgame course); (c) the diagnosis taxonomy → Dvoretsky on training methodology; (d) learning-science claims → de Groot, Chase & Simon, Gobet, Hambrick. **Order: Tier 1 (peer-reviewed, free, retrievable) first** — strongest evidence and the material already cited without reading. For Tier 2 books, the published table of contents/syllabus structure is often enough for M2; only then decide what is worth buying. |

---

## Working order (proposed 2026-07-28)

1. **A1 + A2** — the engine benchmark. Unblocked, converts the largest unknown into a number, decides C5.
2. **F1** — read the five repos. Cheap, and must precede any M3 design.
3. **D2 + E1 + E3** — the mechanical verification batch; pairs naturally with A1.
4. **F2 Tier 1** — free primary sources; closes D1.
5. **B1–B3** — author's scope decisions, then M2.
