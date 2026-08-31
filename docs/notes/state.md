---
id: cas-state
title: State
desc: 'Where the project actually is right now, how far that is from the vision, and what comes next.'
updated: 1788201000000
created: 1785254500000
---

# State

**Snapshot date:** 2026-08-31
**Active mission step:** **M6/M7** — correcting what the detectors name, and giving each claim
something to say
**Last commit:** `chore(M6): regenerate at the normalised keys, and record a silenced player`
**Scale:** 18,882 lines in `chesscoach/`, **1,683 tests at 88 % coverage**, 57 experiments,
138 vault notes

Rewritten at the end of every cycle. The honest answer to "if someone joined today, what would they
need to know?"

## What exists

| Area | Exists | Notes |
|---|---|---|
| Documentation / steering | yes | full vault; [[open-questions]] register; 4 ADRs |
| Process automation | yes | `adaptive-cycle` skill, exercised over several cycles |
| Chess domain knowledge | first pass + primary source | [[domain.chess-concepts]], [[domain.coaching]], [[domain.signals]], [[domain.puzzle-themes]], [[domain.sources]] |
| Prior-art knowledge | **complete** | [[domain.prior-art]] — all five projects read |
| Tooling | **verified working** | Stockfish 18 driven from python-chess; Lichess API fetching real games |
| Measured evidence | **three experiments** | [[experiments.e01-engine-throughput]], [[experiments.e02-positional-detectors]], [[experiments.e03-relevance-weighting]] |
| Positional vocabulary | yes | [[domain.positional-vocabulary]] — rated for detectability |
| Section catalogue | **yes, first pass** | [[domain.sections]] — 11 sections, 3 tiers, build order set |
| Working detectors | **4, tested** | outpost, isolated pawn, backward pawn, rook on open file — experiment code, to be reimplemented in M4 |
| Scope | **decided** | [[decisions.0005-scope-band-source-online-only]] — 1400–1800, Lichess, online only |
| Architecture design | **done** | [[architecture]] + 3 children; profile schema, orchestration, interaction, confidence, storage all specified |
| Architecture **built** | **skeleton done** | `chesscoach/` — ingest, analysis core, profile, CLI. Sections, arbiter and language layer outstanding |
| Evaluation harness | **built, before the first agent** | `chesscoach/evaluation/` — split-half (B1), planted weaknesses (family C), ground-truth scoring, fixture verification |
| **S2 decision process** | **built, scored, assessed** | finds the planted weakness at 5.54× with 0 spurious. One working detector in practice |
| **S1 tactical gaps** | **built, assessed** | eight motif detectors, precision-gated by E04; took the swarm from 1 claim kind to **6** → [[mission.step-07-second-iteration]] |
| Orchestration | **built** | `chesscoach/orchestrator.py` — fan-out, failure isolation, section-scoped replacement. Findings now reach the profile |
| Shared pipeline | **built** | `chesscoach/pipeline.py` — engine/cache session and provenance, extracted in M6 from three copies |
| Peer reference corpus | **rebuilt at full size 2026-08-19** | `data/raw/out/peers-full.json` (gitignored, regenerable): **71 rapid + 65 blitz players**, 30 games each, 104 cells, ~81,000 moves at depth 15. Replaces the 5-per-stratum throwaway that every population rate had been resting on since the threshold change. **The top finding changed for 8 of 12 review players**, and the degeneracy check improved (most-named claim 4/12 → 3/12) |
| Peer reference corpus *(previous)* | **built, widened, stratified** | `chesscoach/peers.py` — **84 players**, band 1400–1800, **rapid *and* blitz strata** (schema v2), carrying per-claim **rates and costs**, depth 15, leave-one-out |
| Parallel analysis | **built** | `chesscoach/analysis/parallel.py` — corpus-wide dedup + prefetch. ~3× on a cold cache, measured |
| Confidence policy | **enforced at runtime** | `chesscoach/confidence.py` — tiers, distinct-game counts, split-half replication as a promotion requirement. Shrinkage was tried here and **reverted** (E20) |
| **Sections S3–S6, S8** | **built, each screened first** | endgame technique, opening outcomes, pawn structure, squares and files, attack and defence. **Eight sections total** since S7 reopened |
| **S7 material safety** | **built 2026-08-17** | `moved_into_attack`, `miscounted_exchange` — the only section reading **the move the player actually played**, answering D13. Two further candidates refused for restating the error rate (E34) |
| **Arbiter + planner** | **built** | one or two priorities, ranked by peer-relative recoverable cost; every step carries a falsifiable target and a check point |
| **Confidence policy — corpus-relative games floor** | **changed 2026-08-20** | `FOCUS_GAMES_WITH_DATA = 20` retired for `FOCUS_GAMES_FRACTION = 0.80` against `ClaimStats.corpus_games` (E43). The old floor demanded a perfect score from a 20-game corpus. Surgical: 15 claims change at 20 games, **0 at 60** |
| **Claim overlap suppression** | **built 2026-08-20** | `chesscoach/overlap.py` — every claim now reports `instances_at`, so two sections describing the same moves is **measured** rather than asserted from a table. Threshold 0.60, calibrated against the pairs `drop_redundant_aggregates` already deletes. Effect is small and stated: **1 player of 12** (E42). Profile schema v15 |
| **Explainer** | **built** | the report a person reads: strength, style, findings with cited positions, plan, band notes, limits |
| **Prober (V9)** | **built** | probe selection, move check, a local model classifying reasons at kappa 0.74, `gap_type` written back |
| **V1 strength / V3 style** | **built, per speed** | two fitted lines (rapid ±103, blitz ±123); one style tendency, mix-matched to the player's speeds |
| **Band-level notes** | **built** | what the whole rating band loses most to — five screened claims, never competing for a priority (E25) |
| **Speed pooling** | **built** | blitz joins the corpus; the baseline stays per-speed by direct standardisation. 24-game coverage 50 % → **79 %** |
| **Corpus hygiene** | **built** | berserked and abandoned games excluded, counted, and disclosed to the player |
| **Opening resources** | **built 2026-08-28** | `chesscoach/opening_plans.py` + `opening_resource.py` — the shape the author approved on the Pirc entry, for every family: the **main line and a few variants** from the CC0 book (`Opening` now keeps `pgn`), **two plan sentences quoted verbatim** from the linked page, and the link. **The system selects sentences and never writes one** ([[decisions.0012-quote-the-plans-rather-than-write-them]]) — checked first that the sentences the author endorsed were the page's own words. 26 of 35 pages yield a plan sentence; the nine that do not are references, which is E48's finding measured page by page |
| **Opening summaries (Ollama)** | **built 2026-08-28** | `chesscoach/grounding.py` + `opening_summary.py` — a local model rephrases the **quoted** plans into prose that reads as one voice, and every output is checked against its source before being kept ([[decisions.0013-a-local-model-may-rephrase-what-it-cannot-assert]]). **qwen2.5:3b: 88 % accepted, 18 % novelty, 3.6 s**, beating qwen3:8b (38 %, 38 %, 8.2 s) on every axis at a third of the memory. The checker rejected an invented square on its first real run — and a **subject swap got through**, so `grounded` never means correct |
| **Web search** | **live 2026-08-28** | SearxNG in Docker (`experiments/e50-ollama-summaries/searxng/`), and `SearxSearcher`'s "untested against a live instance" caveat is retired: **6 of 6** uncovered openings returned candidates. Finding a link is still not finding a guide — the Grob returned a Duolingo blog post |
| **Opening guide scope** | **fixed 2026-08-28** | A guide may name a **subline**, and then reaches only players who play it. Found by measurement: 5 of 10 `Indian Defense` games are Londons and 5 are not, so a family-wide London guide was right for half the players and misleading for the other half. `Indian Defense` is `1. d4 Nf6` — a move, not a thing anyone studies. **Systematic, not a one-off:** the Sicilian candidates carry an Alapin page right for 7 of 16 games — left for the author, since which page covers which subline is curation. Also `MAX_MAINLINE_STEP = 2`, after the Indian Defense main line printed an obscure `1. d4 Nf6 2. c4 e6 3. Qb3` |
| **Plan selection (composed)** | **built 2026-08-28** | `chesscoach/plan_selector.py` — a model judges *"is this a plan"* and the non-`PLAN` filters stay as a **veto** over its choice ([[experiments.e51-llm-selection-and-search]]). Measured: the model finds real plan sentences the regexes lose **and** admits marketing, trivia and annotated variations; the veto cuts its exclusive picks **32 → 12** and keeps the good ones. Handing it the whole page was refused first, on measurement — the grounding check's false-claim pass rate goes **3 % → 76 %** as the source grows, so selection is what makes the later check mean anything |
| **LLM-guided search** | **built, not earning its place** | `chesscoach/opening_search.py` — the model rejects results and rewords the query. Safe by construction (never returns fewer than the plain searcher) and **0 candidates gained on 4 openings**. The judge itself agrees with a person **10 of 12** and errs only by rejecting genuine guides, so it is conservative rather than broken. Recorded so it is not re-proposed as an obvious win |
| **Opening swarm (3 LLM agents)** | **built 2026-08-28** | `chesscoach/opening_swarm.py` — **Scout** writes queries and casts a wide net, **Assessor** discards with reasons, **Compiler** writes the brief ([[decisions.0014-three-agents-for-the-opening-brief]]). Built after the author's objection that the project was mostly deterministic Python and thin as an AI artefact. Runs end to end from an opening name: 17 pages found for the London, 12 discarded, a grounded PLAN for the Pirc. **The WATCH half fails 0 of 6 in every run** — the retrieved pages describe the player's plans, so nothing supports a claim about the opponent, and the Compiler invents or restates. `_restates` added, a check the grounding gate cannot supply |
| **Skip list (learned)** | **built 2026-08-28** | `chesscoach/skiplist.py` — domains the swarm does not fetch, seeded and then **learned by the Assessor** ([[decisions.0015-a-learned-skip-list-and-a-bullet-brief]]). The only persistent state a language model may write to here, under four guards; the load-bearing one is that **a site which has ever yielded a usable sentence can never be skipped**. The Assessor is only asked to classify a page that already failed to yield prose, so it cannot condemn a site it merely disliked |
| **Note supply** | **fixed 2026-08-28** | The swarm's binding constraint, located stage by stage: 1,061 sentences passed the veto across 38 pages and **3** reached the Compiler. The cause was the Assessor's prompt — six DROP rules against three KEEP rules made refusal the attractor, and `qwen2.5:3b` answered `NONE` on four pages of six. **Reframed from filtering to ranking**, plus `is_usable_note` (relevance, never readability — the author's correction), chunking at 25, and a case-sensitivity bug in `FIRST_PERSON` that let forum chatter through. Notes 3 → ~30, briefs **0 of 5 → 5 of 5**, and the opponent half produces points for the first time |
| **Run store** | **built 2026-08-28** | `chesscoach/runstore.py` — SQLite, stdlib, one file: every page the Scout found, every sentence the Assessor kept, every point the Compiler wrote **and every one it dropped, with the reason** ([[decisions.0016-a-run-store-for-the-swarm]]). Written as the run proceeds and the run row opened **before** the search, so a rate limit leaves a visible unfinished run rather than nothing. It paid immediately: across five runs the top drop reason is *"repeats a point already made"* (7), more than every grounding failure combined. `dump_run.py` turns any run back into the text report and answers what a text file cannot. **The opening book stays JSON**, measured: 0.04 s to load, 1.2 ms per game walked — a load format, not a query format |
| **Report reads the store** | **wired 2026-08-28** | `render(profile, opening=...)` prints a **YOUR OPENING** section, and `RunStore.approved_brief` is the only door into it — nothing unapproved, nothing unfinished, and no dropped point can reach a player. **Approving is the same act as `reviewed: true` on a guide link** and belongs to the author, **point by point**: `dump_run.py --run N` numbers the kept points and `--approve N --points 1,3` shows only those. A run read and rejected is recorded as reviewed rather than returning to the pending list. Five runs sit pending and nothing is approved, so no report shows the section yet — the gate works and nobody has walked through it. The store also gained an additive migration, after a file written an hour earlier failed to open once the schema grew |
| **Structured outputs** | **built 2026-08-29** | Every agent asks with a JSON Schema (`ollama.generate(schema=...)`), so `NONE` where a list was required, `"3, NONE"` and prose-read-as-indices become unrepresentable ([[decisions.0017-constrain-the-answer-with-a-schema]]). **Adopted on construction, not measurement** — the parse rate was already 100 % because the prose fallback was catching everything, and the fallback is kept and tested on both paths. The change also *caused* a regression worth more than the feature: the format example anchored the model to answer `{"keep": [3, 11, 24]}` on every page, costing three briefs of five until it was found by reading raw answers. **L-048** |
| **Detector precision screen** | **apparatus built 2026-08-29, nothing measured** | `chesscoach/precision.py` — Wilson intervals and three verdicts, sized on the asymmetry that **five samples can condemn a detector and cannot exonerate one** ([[experiments.e55-detector-precision]]). Floor 0.70, anchored on the author's own 4/5-accepted and 0/5-rejected. **The 23 existing marks cannot be dated against the code they judged** — the motifs were rebuilt 08-24 and `moved_into_attack` fixed 08-27, and no marking date was ever recorded — so the project has no valid precision data, which is worse than none because it looks like some. The sheet now stamps its generating commit so this cannot recur |
| **`advantage_error` retired** | **done 2026-08-29** | The second-commonest claim in the system stops being counted ([[experiments.e56-retire-advantage-error]]). Measured before shipping, as the design note promised: it fired for **6 of 12** players, **nobody** loses a priority or is left with nothing, and **two players were being told about it first** — `bjagus` and `Sheriwoyama` now lead with something else. The cost pool refilled the freed slots invisibly, which is the mechanism working. Uncomfortable half: `bjagus` swapped it for `early_error.white`, which is **also** on the correction list at 0/4 |
| **`fork` rebuilt** | **done 2026-08-29 — and it now never fires** | Four conditions where there were two: the targets must be **newly** attacked, and no defender reply may save them ([[experiments.e57-fork-rebuilt]]). The strictness is the whole correction, measured: over random positions only **3 of 1,014** knight double-attacks on a rook and bishop are genuine forks, and **the old detector counted all 1,014** — a rook attacked beside a bishop usually steps to a square that defends it. Nine fixtures, and the **negatives carry the file**; hand-building positives failed three times because most double attacks are not forks. **`allowed_motif.fork` 113 → 0 and `missed_motif.fork` 33 → 0**, both now in the sheet's NEVER FIRED list. Consistent — a direct scan finds 65 forks in 3,908 best moves (1.7 %), and S1's populations are a few hundred positions, not thousands — but **consistent is not correct**, and the claim is currently unmakeable for every player. `allowed_motif.pin` 32 → 43 was recorded as unexplained and is now **closed**: it was never caused by the fork rebuild. `_is_pin` is byte-identical across that commit, and the sheet the 43 came from is stamped `GENERATED from commit 3fb8541` — **before** the rebuild. The change belongs to 605be31, the earlier motif rebuild, which touched `_is_pin` in seven lines. **L-046's eighth instance**, and the second where the arms of a comparison were not what I said they were. **Pointing it at played moves then found a sixth L-046: every checkmate was a fork** — the defender-reply loop is vacuously true when there are no replies, 104 of 1,779 hits, and one was the second position read by eye. Fixed. What remains fires **1,675 times over 2,125 games** (1.1 % of moves, against 1.7 % of best moves): 39 % a check that also wins a pawn, 32 % a check that wins a piece, 28 % two pieces and no king. **15 positions are sampled as diagrams with mark boxes** (`experiments/e57-fork-rebuilt/results/fork-sample.txt`) and nothing more should be built on this detector until they are marked |
| **Development measurement** | **built 2026-08-29** | `chesscoach/development.py` — castling ply, development-complete ply, repeat moves, pawn moves and the window they are counted in, per game per colour ([[experiments.e58-opening-development]]). **No threshold in it**: the comparison belongs to the peer reference, keyed by the opening. Per-opening norms derived over 2,019 games and 97 families, and the spread justifies the whole apparatus — **castling ranges from move 7 (Ruy Lopez, W) to move 17 (Bishop's Opening, W)**, pawn share from 25 % to 41 %, book depth from 1 to 5 moves. The author's *"some openings allow more pawn moves"* is confirmed directly. **But their two predictions do not reproduce**: Italian predicted move 5, corpus says 8; Ruy Lopez predicted 8–10, corpus says 7 — the ordering is inverted, and until that is resolved no claim can be wired up, because peer-derived and theory-derived norms are different quantities. A censoring bug was also found **in this experiment's own method** — a median over only the games that castled understates lateness exactly where it is worst (Bishop's Opening: 47 % never castle, median moved 11 → 17) |
| **Strong-player expectation** | **built 2026-08-30** | 5,917 rated rapid games from the **top 100 rapid players (2556–2932)**, supplying the expectation the author asked for — *"not by peer reference but by better players who usually know the opening"* ([[experiments.e59-strong-player-expectation]]). **Coverage 90 %** of subject games (22 of 26 families); the four that fall through are exactly the openings strong players do not play, which is the own-median fallback the author required, needed where they predicted and carrying only 10 %. **Separation is the decisive test and two signals pass**: late castling **AUC 0.73** (29 % vs 42 %) and repeat moves **AUC 0.70** (31 % vs 36 %). **The author then caught a composition confound** — the separation test pooled openings, so *which* openings a population plays was mixed with *how* they play one. Standardised to a common opening mix over 36 family×colour cells: **late castling holds at +9.8 pp** (subjects later in **30 of 36** openings) — a genuine within-opening effect; **repeat moves halves to +2.0 pp** (26 of 36), so E59's first figure was double-counting repertoire; and **pawn moves collapse to nothing** — on the count that matches the hypothesis the split is **17 of 36**, a coin. The apparent inversion was an artefact: subjects push the *same* number of pawns but take +0.29 moves longer to develop, so the *share* falls. **Pawn share is therefore not a measure of pawn behaviour** and is dropped. **`slow_development` then tested strongest of all**: +10.6 pp standardised (moving only 0.2 pp, so almost none of it was repertoire), **32 of 36** openings, AUC 0.76 — and **not redundant** with late castling at **r = 0.68**, under the design's 0.85 ceiling. The concrete reason: **24 of 72 subjects are slow without being late to castle** — they castle on time and still leave a piece at home. A calibration of mine was also withdrawn: a 25 % false-positive ceiling treated the threshold as a per-game verdict when the claim is a per-player rate |
| **Development claims wired + peer reference rebuilt** | **built 2026-08-30 — and blocked at the arbiter** | `chesscoach/development_norms.py` (the strong-player expectation as a loadable artefact, 232 cells, 86 with 20+ games) and `chesscoach/opening_development.py` (tallies, both bases in **separate claim keys** so *"late by this opening's standard"* and *"later than you usually are"* can never pool), wired into **S4** where the `early_error` they replace already lives. Games are rebuilt from the observations, so no new data path. Reference rebuilt across **both strata**, 112 cells, 62–71 players per development cell ([[experiments.e60-peer-reference-rebuild]]). **They do separate 1600 from 1600** — spread 45–51 pp, and **~a quarter of the band clears the 1.25× priority margin** on the two headline claims (`repeat_move` only 6–10 %, matching its halved effect). **But they reach 0 of 12 plans.** `arbiter._sort_key` ranks every claim that cannot state a cost below every claim that can, and these have none by construction — so they can be true, asserted and undeliverable. Three ways out, all changing what every player is told, none taken without the author. Two bugs found en route: tallies carried **no evidence**, so V8's gate refused them **silently** with every count correct; and my first reference was **rapid-only** while 10 of 12 review players are blitz, which produced a clean 0/12 that was an artefact and was caught only by instrumenting before reporting |
| **Habit cost** | **built 2026-08-30** | The author's costing method, which was not among the three options offered ([[experiments.e61-habit-cost]]): sum `loss_wp` over the moves each habit **names**, rather than measure where the opening ended — *"in the games of weaker players they don't have to eventually end opening worse because their opponent also plays badly"*. Two weak players' errors cancel, so the end position says nothing; per-move attribution never touches the opponent. **Repeat moves cost a median 20.4 wp/game, pawn moves 12.8, declined castles 9.7** — 36 %, 22 % and 17 % of all opening loss. The **"instead of" condition is load-bearing**: a repeat move counts only while a minor is still at home, or the sum re-measures the general error rate under a habit's name. Correlations with that error rate are **0.44–0.64**, well under E10's 0.917. **Development claims reach a plan for the first time, 0/12 → 1/12**, on the same terms as every other claim — no reserved slot, no reordering. The bottleneck moves to the **assertion rate**: 1 of 12 asserts where the band figure predicts ~3. **Then the author's gambit guard and the pawn claim's return**: a move the book still names is theory, not the player's mistake — which protects the King's Gambit's `f4` and the Englund's `e5`, and cuts the **pawn cost 11 %** while barely touching the other two, exactly the specific effect predicted. And `pawn_error` rebuilds E59's dropped claim around the **quality** of the choice rather than its frequency — *of the pawn moves you played instead of developing, how many went wrong* — which clears the margin for **18 of 71** rapid players and takes a plan slot. **Development claims now reach 2 of 12 plans, from 0**. **Then reading the positions found two defects the counts could not** ([[experiments.e62-reading-the-pawn-claim]]): **40 % of `pawn_error` instances were *"you pushed the wrong pawn"*** — the engine wanted another pawn move, not development — and the castling claim wanted castling on only **26 %** of what it charged. A second defect surfaced in the **first sampled position**: a bishop already on b4 counted as *developing*. Both fixed by charging a habit only where the engine's own preference was development-from-home or castling. **Every metric improved**: costs fall ~80 % while correlation with the general error rate falls 0.73 → 0.52 (pawn 0.69 → 0.31, spread 24 → 42 pp), and plans go **2/12 → 3/12** — the arbiter ranks on excess over peers, and peers shrank too |
| **Knowledge base foundation** | **built 2026-08-30** | `chesscoach/knowledge.py` — one entry per detected claim, with the four parts kept in **separate fields because they have separate provenances** ([[design.knowledge-base]]). `reviewed` means the **author** endorsed it and no drafting path can set it; a redraft never overwrites a reviewed entry; an entry with no usable source cannot be endorsed (hard rule 7); `folklore` is a recorded evidence class so it can be **refused** rather than silently accepted (R-03); and showing an unreviewed entry **raises** rather than rendering blank in front of a player. **`not_this` is the load-bearing field and the swarm may not write it** — the web's definition of a fork is *"one piece attacks two"*, which is exactly what the broken detector implemented. 13 tests. Plus `FallbackSearcher`, which reverses `SearxSearcher`'s no-fallback rule **only for motif definitions**, where Wikimedia is the right genre — made safe by recording the substitution in `fell_back` rather than hiding it. 6 tests |
| **Knowledge drafting swarm** | **built 2026-08-30 — output not yet usable** | `chesscoach/knowledge_swarm.py`, Scout → Assessor → Compiler pointed at a claim instead of an opening ([[experiments.e63-knowledge-swarm]]). **The `Assessor` is reused unchanged** — its prompt takes a topic string and a claim name is as good a topic as an opening name. **The definition is chosen by index**, so it is a page's own sentence by construction and never model prose. **The first run drafted 3 of 3 and every one was wrong**: a "definition" of castling that read *"there are two possible moves that place a pawn in the centre of the board"* — a real sentence, verbatim, about something else. **Choosing by index guarantees provenance, not relevance**, and with no way to say *"none of these"* the model must return the least-bad sentence. L-046 with the failure moved out of the pipeline and into the content, and invisible in any count because the run reported 3 of 3. Fixed by letting the Compiler answer `-1`: now **1 drafted, 2 correctly refused**, and an incomplete entry cannot be endorsed. **The bottleneck is retrieval reach** — mojeek/mwmbl/wikipedia/wikibooks reaches no chess tactics glossary, so the surviving entry is an *example* of a fork rather than a definition, which is useless for the detector review that is the half the author wanted most. **Engines widened 4 → 7** after checking which names the image knows: results for *"what is a fork tactic in chess"* **6 → 92**, no unresponsive engines, `yep` and `fireball` removed as measured dead weight. **And the drafts got worse, 0 of 3** — because the real problem was **telling a definition from an example**, and my prompt fix had swung it from always answering to always refusing. **A refusal option needs a criterion, not a bias.** Even with the criterion spelled out, `qwen2.5:3b` picked the example; `qwen3:8b` and `phi4-mini:3.8b` both picked the definition. **A capability, not a wording** — so the roles are split, cheap model for bulk sentence-picking and `qwen3:8b` for the one judgement that decides the entry. The `fork` entry is now real and sourced — **and still wrong for detector review**, because *absolute* fork is a **subtype**. Which is the design note's own argument for keeping the precise rule with the author |
| **Books, real phrases, and the full batch** | **built 2026-08-31 — 3 usable of 14** | Three moves that each fixed a different failure, and the honest total is still three entries. **Public-domain books** (`chesscoach/books.py`, [[experiments.e64-chess-books]]): Capablanca 1921, Edward Lasker 1915, Staunton 1848 from Project Gutenberg — free under C7, cited as `book://<slug>#<passage>` rather than a URL. They are **strong exactly where the web was weak** (castling, development, pins) and **silent where it was strong** — "skewer" and "outpost" appear **zero times** in all three, because the words postdate the books. **The measured vocabulary** (`TERMS`, [[experiments.e65-real-phrases]]): several real phrases per claim, each counted in the books and on the web, which **corrected four guesses outright** — "outpost" 0 uses against "hole" 50, "trapped" 0 against "hemmed in" 5. Searching for the word I would use is not the same as searching for the word writers use. **And the Assessor was the wrong judge**: built to screen opening pages, it passed running commentary as a definition (the `hangingPawn` entry read like a game annotation) and let four off-topic pages through — a Beyoncé film, a Go wiki, a constructed-language grammar, a libertarian-communism essay. Now a URL-structural check plus a chess-density floor of 1 mention per 5 KB, with the **title no longer able to short-circuit it**. **Two defects worth keeping**: the SAN pattern was written three times before it was tested (`Nxf3+` missed, `b12` matching `b1`, `0-0` and `1-0` absent), and the books then **starved the web** — 34 book sources and **zero** web sources — until the read budget was split. The batch yields **3 entries a player could be shown and 11 refusals**, and the refusals are the measurement: most of this vocabulary has no definition the sources will support |
| **`rook_seventh` and `doubled` corrected** | **done 2026-08-31** | Step 3 of the six corrections ([[experiments.e66-rook-seventh-and-doubled]]). **`rook_seventh` fires only when arrival was preventable**: three or more open files — the author's own threshold — and the claim goes silent, which removes **52 % of 4,077** rook-on-seventh positions. Half is not most, so the precise two-ply search **still has something to buy**, the opposite of what the design note guessed. **`doubled` gained both of the author's conditions and they are wildly unequal**: distance (1–2 ranks) removes **17 %**, while **64 % of doubled files never survive three moves** — 490 of 765 exist only until the end of an exchange, exactly as they said. `persistent_doubled` is built and tested but **not wired into S5**, which sees one board at a time; so the 64 % is what the claim *would* lose, not what it has lost |
| **Persistence everywhere, and endgame runs** | **done 2026-08-31** | Steps 3–4 of the six corrections finished ([[experiments.e67-persistence-and-endgame-runs]]). **Persistence generalised to every pawn weakness** on the author's extension — *"isolated pawn should also have similar persistance check"* — and **wired into S5**, which E66 left undone: a conceded weakness is kept only if it survives three more of the player's own moves, and a game that ends first is not a repair. **`endgame_error` rebuilt as a run**: 3 drops within 4 moves, with tactical drops removed **before** the run is sought, so a hung rook between two inaccuracies does not join them. **211 firings → 50**, and the conditions are unequal again — the residual removes **10 %**, the run condition the rest. The claim is now **explicitly residual**: when `fork` was wrong, this was wrong with it. **5 of 6 corrections built** |
| **Sheet and peer reference regenerated at HEAD** | **done 2026-08-31** | Five detectors were corrected after the sheet was written, so the marking queue described behaviour that no longer existed — marking it would have produced the undateable marks E55 was built to end, at the cost of the author's scarcest resource. Reference rebuilt across both strata and the sheet regenerated: **145 boxes, 29 claims, `GENERATED from commit 3af3206`**. **And the stamp is now read rather than merely written**: `score.py` **refuses** a sheet whose detectors have changed since it was generated, naming the commits. A stamp nothing reads is a comment, which is how E57's pin difference was scored against a sheet two commits old |
| **Endgame run threshold calibrated** | **done 2026-08-31** | A permutation test — same moves, same error counts, shuffled which moves erred, so the gap is clustering and nothing else ([[experiments.e68-run-calibration]]). **The window was letting chance in**: 3-in-3 beats the shuffled baseline **1.96×** with **0 of 200** shuffles reaching it, while **3-in-4 — the setting E67 shipped — was matched by one shuffle in eight**. The pattern is monotone: every move of slack lets the error rate masquerade as clustering. **The author's literal words beat the design note's relaxation** — *"imprecise one move after the other"* means consecutive, and the note had softened it. Adopted **3 in 3**; endgame errors **50 → 35**, from 211 under the old any-drop rule |
| **Development correlation screen** | **done 2026-08-31** | The screen [[design.opening-development-signals]] promised before the claims shipped, run at last and read straight from the rebuilt peer reference — no engine pass, and current by construction ([[experiments.e69-development-correlations]]). **No pair exceeds the 0.85 ceiling, so all four ship.** `slow_development`/`repeat_move` at **0.81** is distinct **narrowly** and should be re-run whenever either detector changes. The pair E59 measured at **0.68 is now 0.75** — nothing about the claims changed, the detectors underneath them did five times, which is the stamp lesson in a different artefact. `pawn_error` is the outlier and earns its slot: 0.16–0.29 against the others, median rate 6 % against their 41–46 %. Against `early_error` the highest is 0.55, so none is restating the general opening error rate |
| **Development claim keys, and a sheet that lied** | **fixed 2026-08-31** | Every claim in the system is `kind.subject.own`; the development tallies emitted `kind.subject`, because I built them without going through `_key()`. **That made the detection sheet lie**: it builds its vocabulary from `measure()` and its fired set from `Claim.key()`, subtracts one from the other, and so listed four claims as **NEVER FIRED** while the peer check showed them reaching **3 of 12 plans**. The never-fired list is the half of that sheet the author **cannot check by reading positions**, because there are no positions to read — a false entry there is invisible by construction. Keys normalised, a test pins the shape, reference and sheet rebuilt. **Open:** `maikel5` now has **no priorities at all**, and E56 established silence was 0/12 |
| **One-command session** | **built** | `cli coach` — username in, report out; verified end to end on a live player, deterministic across runs |

## Distance to vision

| Dim | Vision item | Score | Δ | Evidence / why |
|---|---|:--:|:--:|---|
| D1 | V1 skill assessment | **3** | **+1** | **down to 2 on its first external test, and back up now the defect is repaired** → [[experiments.e27-held-out]], [[experiments.e29-attenuation]]. E27 tested it on 30 players fetched after every constant was frozen: **rapid excellent (MAE 79) and blitz barely an estimator (150 against 157 for guessing)**, compressed by slope attenuation that cross-validation structurally could not see (L-036). E29 corrected it by the standard remedy — divide the slope by the predictor's reliability, **0.641 measured on the fitting corpus alone**, a 1.56× stretch that the held-out players **independently demand at 1.48×**. Held out: **MAE 149 → 129**, bias −111 → −97, within 200 points 75 % → 88 %. Rapid was left alone because the same theory says it should not help there and the data agrees (79 → 111 if applied), which is what makes the blitz correction evidence rather than tinkering (L-037). Not 4: **blitz at 129 against 148 for guessing is still weak**, a −97 bias remains, and the vision asks for strength *and its variance* while every player still gets the same error bar |
| D2 | V2 knowledge assessment | **2** | **+2** | **the prober works end to end** — probe selection, move check, a local model classifying reasons at kappa 0.74 with zero false-ignorance (E07), `gap_type` written back. Not 3: the rubric's answer set is written and labelled by the author and the figure is in-sample, so it may not yet change a real player's finding |
| D3 | V3 style profiling | **2** | — | **built, half deliberately refused, and now compared against the right population** → [[experiments.e14-style-dimensions]]. One measured tendency — how much of a game is spent with the queens off — that varies between players (1.40) and is **independent of strength** (r = −0.069). Four of six candidates were strength wearing a style label. A live session found it comparing an all-blitz player against the *rapid* population (I-03); it is now mix-matched like every other comparison. Not 3: **the performance half does not survive** — everyone errs ~20 % less with queens off and players barely differ, so the report says what a player tends to do and refuses to say whether it suits them |
| D4 | V4 gap detection | **3** | **−2** | **eight sections, and the shallow-corpus caveat that held this back is gone.** On 150-game histories 70 of 84 players advised (83 %); on the **24 games a real user brings, 50 % → 79 %** once the player's other speeds are pooled in, with claim kinds 20 → 25 and overlap unchanged at 0.09 ([[experiments.e21-pooled-speeds]]). Groundedness 113/113. The lever was never more sections: six sections moved coverage 24 → 53 %, corpus depth and then speed pooling did the rest. **S7 reopened 2026-08-17** → [[experiments.e34-material-causes]]: the slot E10 emptied, refilled on a different question — not *how deeply do you calculate* but *did you check*. Two claims read **the move the player actually played**, the first detectors here to do so, closing the structural gap E33 named. Two further candidates were refused for correlating +0.917 and +0.914 with the overall error rate, which is where E10 closed the slot in the first place. Anonymous errors 52 % → 49 % | **Down 2 on 2026-08-23** → [[decisions.0011-detection-correctness-over-expert-agreement]]. The author read the reports against the games and found the detection itself wrong: forks mis-detected, `moved_into_attack` firing on ordinary exchanges, king-attack claims raised deep in endgames, and every Black move cited a number too high. **Coverage was never the question this score should have been answering** — 83 % of players advised says nothing about whether what they were told is true. The figures above stand; what they measure is reach, not correctness. It returns when D17's re-screen reports precision per detector on hand-verified samples. **Five of the six corrections have now landed** ([[design.detectors-name-consequences]]): `fork` rebuilt on four conditions after it turned out to call **every checkmate a fork** (104 of 1,779 instances were vacuous); `rook_seventh` silenced on positions with three or more open files, which the author says nobody can be blamed for (**52 % of instances**); `doubled` and `isolated` required to **persist three moves** rather than exist for one; `endgame_error` rebuilt on a **run of three imprecise moves in a window of three**, calibrated against a permutation baseline rather than against its own fixtures ([[experiments.e68-run-calibration]]); and four development claims added and screened for mutual independence ([[experiments.e69-development-correlations]]). `early_error` is the one left. **None of this moves D4**, and saying so is the point: a corrected detector is still a detector nobody has checked against a position. The sheet is regenerated and stamped, and `score.py` now refuses a stale one — but 145 boxes are unmarked and only the author can mark them.
| D5 | V5 prioritisation | **4** | **+1** | **ranks by what a weakness costs *above what it costs peers*** → [[experiments.e15-expected-gain]], corrected by [[experiments.e17-ranking-stability]]: raw cost named one claim to 70 % of players, so the excess over the population is what a plan can honestly promise, and occurrence rate is kept as a gate but **demoted as a ranking signal** (it ranks at chance, 6 % against 4 %). **And the first expert review then found that ranking blind in a way no internal measurement could** → [[decisions.0010-three-priorities-and-the-cost-pool]], L-039. For `bernes` the most expensive pattern in their games (7.3 wp/game, 10 of 53 games) was measured, correctly judged *not statistically unusual*, and **destroyed** — because being unusual was the only route onto the page. Cost now fills the slots unusualness leaves empty, labelled *"ordinary for your level"*, capped at 3 and never displacing a peer-relative finding; the band-level section (E25) still carries the shared weaknesses that pass its learnability screen. Verified across all 12 review players: **18 distinct claims, most-named 4/12**, so E17's degeneracy did not return one level down, and a second defect was caught on the way (a claim the player did *better* than peers was being offered as a priority). Not 5: it is still an **accounting** cost rather than a forecast, plan length is now near-constant at 3 for 11 of 12, **silence went 2/12 → 0/12**, and the vision asks for gain *per unit of study time*, which needs D5's unresolved question about how long anything takes |
| D6 | V6 path planning | **2** | **+2** | plans built and persisted, every step carrying a machine-checkable progress sign and a derived check point. No time estimates — D5 is unresolved and inventing them was refused |
| D7 | V7 progress tracking | **3** | **+1** | **restored, on evidence this time.** 57 predictions from 84 players with ~150-game histories; the constant is cross-validated at 2 *and* 5 folds with a fold spread of 0.011, and a held-out false-positive rate of **15 %** is stated in the output. Not 4: the test's **power is unmeasured** — no coached cohort exists, so nothing shows a real improvement could clear the bar (**D8**) |
| D8 | V8 explainability | **3** | — | the report exists, is deterministic, and is **13/13 grounded** on real players (E08 D4). **The 3 claimed last cycle was not earned**: reading a real report found Lichess theme keys in player-facing prose — *"a `trappedPiece` punishes you"* — which the groundedness metric scored 100 % on, because it only checks citation. Fixed (`phrasing.subject_name`), so the score now stands. Not 4: the report states measurements without explaining *why these one or two* were chosen over the rest, and the arbiter's reasoning is invisible |
| D9 | C1–C4 cost profile | **4** | **+1** | **re-timed 2026-08-06 against a genuinely empty cache**, which is what the previous 3 was missing. A new player, 60 pooled games: **5 s fetch + 76 s analysis ≈ 81 s**, of which 98 % is the engine. The same player again: **1.5 s**. A deep 197-game pooled corpus: **232 s cold, 2.9 s warm**. Cold scales at **~1.2 s per game**, so the 300-game accumulation ceiling is ~6 min for someone starting from nothing. Probes add ~2.7 s each (E07). **Zero cash throughout.** **A correction:** pooling speeds was expected to multiply session cost ~5× and does not — `--games 60` still fetches 60 games, it changes *which* 60, and only `--previous` raises the count. Not 5: one player on one machine, and the 300-game ceiling is extrapolated from 197 rather than measured |
| D10 | Evaluation capability | **5** | **+1** | both sides of the progress check measured (E05, E06), the **anti-pattern family D** built and run (E08), depth-robustness tested from both directions ([[experiments.e26-depth-robustness]]), and now **the pipeline run end to end on 30 players it was never built on** ([[experiments.e27-held-out]]) — which promptly caught a real generalisation failure in V1-blitz that cross-validation could not see. **An evaluation capability that only ever confirms is not one**; this one has now demoted a dimension on its own evidence. Not held back: the remaining gap is not a missing *measurement* but a missing *judge* — criteria 2 and 3 need a person, which is a resource problem rather than a capability one |
| D11 | Process & documentation health | **3** | **−1** | **down, and the reason is this table.** The cycle kept working — E20 was withdrawn on evidence, step 7 refused before it was built, three lessons recorded about misreading our own measurements. But across seven steps of the short-history plan the **scorecard rows went stale while the narrative below them was updated every cycle**: D4 still claimed 53 % coverage after pooling took it to 79 %, D5 still described raw cost, and *"What exists"* carried `Any agent \| no` beneath seven built sections. The rule says close no cycle without updating [[state]]; it was honoured in the part that reads like prose and not in the part that reads like a score. Reconciled 2026-08-08. **Held at 3 on 2026-08-14 rather than restored**, because the same drift was found again one level out: the README still advertised 688 tests, 82 % coverage, "7.6 seconds", "rated rapid and classical games" and *"two of the eleven section agents"* against seven built. And criterion 6 was **ticked without ever being run** — executing it from an empty directory broke the chain twice (L-038). All corrected and the chain re-run end to end, but a process that catches its own drift only when something else forces it to look has not yet earned the point back. **Found a third time on 2026-08-31, and again only because someone asked**: the snapshot header still read 2026-08-08 with *"849 tests"* against 1,683, `mission.md` still called the next iteration *"a section (S3)"* with S3–S8 all built, and *"Next logical steps"* had grown to **37 entries, 20 of them done** — a list nobody could act on. The pattern is now specific enough to name: **prose gets rewritten each cycle and structured rows do not**, because a row is not where the thinking happens. Corrected, and the next cycle should test the fix rather than assume it |
| D12 | V9 dialogue & active assessment | **3** | **+1** | **the whole interaction exists**: four context questions before the analysis, probes after it, both feeding the profile, and probe results now reaching the diagnosis inside a coaching session. Answers accumulate as a dataset by-product. Not 4: the classifier's rubric is still the author's own (D10), and the dialogue is four fixed questions rather than anything adaptive |

**Total: 37 / 60**, and **no dimension is at zero.** It has gone 17 → 16 → 17 → 16
→ 17 → 18 → 20 → 22 → 25 → 26 → 27 → 28 → 29 → 32 → 34 → 36 → 37 → 38 → 37 → 38 → 39 → **37**, and every move
was forced by a measurement — including the last two, where **D1 fell to 2 when strangers exposed a
defect nothing internal had caught, and returned to 3 once it was repaired and re-validated on those
same strangers**:
down when E05 showed the verdicts meant nothing, up when the target rule was recalibrated, down
again when cross-validation showed that calibration was itself optimistic, and up now that 57
predictions can support what 13 could not, and again now that both sides of the progress check are
measured rather than one. A scorecard that only went up would not be measuring anything.

The loop is closed — diagnose, prioritise, predict, check — and the prediction is now both demanding
and **quantified**: about 15 % of untreated players meet it, held out rather than in-sample.

**No dimension is at zero**, down from four earlier in the project. The empty column — everything
requiring the player to be *asked* something — has filled, and the loop runs end to end: analyse →
diagnose → prioritise → **ask** → plan → **report** → check.

**V1–V8 are now all built.** Nothing in the vision is missing a mechanism; what remains is that
several of the mechanisms are weaker than the vision asks for, which is what the scores say.

Two honest qualifiers. **The prober's rubric is still the author's own** (D10), so the asking is
load-bearing but validated in-sample. And **the swarm is still silent for about a fifth of players
at 24 games** — down from 43 % once their other speeds are pooled in
([[experiments.e21-pooled-speeds]]), and every silent player has patterns the swarm can see and
cannot confirm, so the silence is a measurement limit rather than a verdict.

**The move this cycle is D11 down one**, which is the whole point of scoring the process alongside
the product: the work was sound and the record of it was not.

**And the gap that now dominates everything is external validity.** Of the six success criteria in
[[vision]], three are measured — the strength estimate against real ratings, the cost, and
reproducibility from this vault. Criterion 6 was ticked on the strength of the vault looking
thorough; it has now been **executed from an empty directory**, which is a different claim and was
not a free one. The chain broke twice — the corpus-building step did not exist in the product at
all, and once it did, an unstratified fetch produced a reference that silently dropped the peer
comparison and the entire band-level section from a report that still looked finished (L-038).
Both are fixed, guarded and re-run end to end. **Three criteria are not measured**: whether the
weaknesses the swarm names match what
a strong independent reviewer would name (criterion 2), whether the path reads as reasonable and
specific to a strong player (criterion 3), and whether following it beats a control (criterion 4).

**Criterion 2 now has its first evidence**, and it is favourable:
[[experiments.e26-depth-robustness]] re-labelled 1,200 sampled moves at depth 22 and **90 % of the
errors survived, 97 % of blunders, with an implied rate ratio of 1.05**. That is engine against
engine — it establishes the *foundation* is not an artefact of the depth setting, and it cannot say
whether hanging pieces and early errors are the right way to describe a player. Only a person can.
The one number that looked like a dent — the report's suggested move still being the engine's top
choice only **78 %** of the time — was chased down and is not one: on every sampled move where the
report offers an alternative, **169 of 169**, that alternative still beats what the player actually
played, by a median of **17.8 win-probability points**. The report never claimed the move was
optimal, only that it was better, and that claim holds.

**And then the review started, and its first player disagreed.** On `bernes` the reviewer's Form A
named *undefended pieces*; the report named *missed forks*. The pattern they named **had been
measured** — 7.3 win-probability points a game, the most expensive in that player's games, 10 of 53
games — and was discarded because its interval did not clear the peer rate. The gate was
statistically right; it was also the **only door**, so a claim failing that one test was destroyed
rather than demoted (L-039). Fixed by [[decisions.0010-three-priorities-and-the-cost-pool]]: three
priorities, and cost fills what unusualness leaves empty, labelled as ordinary for the level. One
disagreement of one is not a result, and it is counted against the ≥ 7/12 threshold regardless. What
it does establish is that **criterion 2 was worth the cost** — no amount of further internal
measurement would have found this, because every component was individually correct.

So the honest position: everything measurable without a human has now been measured. **Criteria 2 and
3 — a strong player reading a dozen reports — are the gate, and they are the one thing on this list
that cannot be done alone.**

**The review is prepared and pre-registered** → [[evaluation.expert-review]]. Protocol, sample and
**pass thresholds fixed before any reviewer was approached**, because deciding what counts as a pass
after reading the answers is how a review becomes a testimonial.

**Amended 2026-08-14, before any answer was collected: the reviewer is the author at ~1880, not a
titled player.** No titled reviewer is available, and a substitute could not be found for a
structural reason worth recording — published expert analysis covers **one game deeply** or gives
**band-level advice**, while this swarm diagnoses **one player across ~60 games**, so there is no
public source pairing a fetchable account with a strong player's diagnosis of that player's
*recurring* weakness. The result will therefore read *"agreement with an 1880-rated player"*, never
*"agreement with expert judgement"*. Three or four club reviewers at 1800–2000 would be **better than
one titled reviewer**, because inter-rater agreement would show whether *"the main weakness"* is even
a well-defined question at this level. Twelve players drawn from the E27
held-out set — including the two the swarm was silent about and the weakest finding that still
shipped, so it cannot be run on the flattering cases. The reviewer writes their **own** diagnosis
before seeing the system's, in a separate folder, because *"would you have said this?"* and *"do you
agree with this?"* are different measurements. Build it with
`experiments/e28-expert-review/prepare.py`; it costs about 15–20 minutes per player of the
reviewer's time.

The uncomfortable part of this cycle is not the score. Expected-gain reasoning had been treated as
blocked ever since E03 failed to link a feature to errors — for two scorecard cycles the note read
*"no expected-gain reasoning"* as though the measurement had settled it. It had not. E03 asked a
**predictive** question and this asks an **accounting** one, and the second was a sum over evidence
the profile had been carrying the whole time (L-028). A failed experiment had been quietly promoted
into a boundary.

What changed is smaller than it sounds and more important than it looks: the swarm can now say *"this
is costing you four points a game"* instead of *"you do this 1.8× more than your peers"* — the
difference between something interesting and a reason to spend a month on it.

## Capacity readiness

This is what actually moved this cycle.

| Capacity dimension | Score 0–5 | Δ | Note |
|---|:--:|:--:|---|
| Domain knowledge (chess) | 4 | +1 | primary sources in use; positional vocabulary assembled and rated for detectability |
| Domain knowledge (coaching) | **4** | **+2** | **F2 largely closed 2026-08-14** → [[domain.expertise-research]]. The decisions the code rests on are traced to Gobet & Charness (2006), read directly from the PDF and quoted verbatim: pattern recognition over search depth (Chase & Simon; 300,000 chunks; a 1600→2300 player with **no significant increase in search depth**), the small cost of playing fast (**5.02 → 6.85 blunders per 1,000 moves for a sixfold cut in thinking time**, which independently corroborates E19), narrow transfer (Didierjean et al.), and ~1,000 hours to master. **The four-way gap taxonomy is sourced too**: Rasmussen's Skill–Rule–Knowledge classification and Norman/Reason's slips-versus-mistakes, which also exposed two things worth a thesis paragraph each — the project's `skill` and `process` are named the **inverse** of the standard framework, and `psychological` is **not an error type** there but a performance-influencing factor, which explains why no section has ever assigned it. And the swarm's `FRAGILE` type occupies the one cell of the intention × action square the literature leaves unnamed, which is what the prober was built to detect. Not 5: the procedural claims (lesson shape, the anti-pattern list, sequencing) still rest on coaching sites, and no published curriculum has been read |
| Signal & tooling knowledge | 5 | +1 | engine, API, tactical and positional detection all verified **by running them** |
| Prior-art knowledge | 5 | — | complete |
| Architecture | 4 | +1 | fully specified — profile schema, orchestration, interaction, confidence, storage — and each choice traced to a measurement or a rejected alternative. Not yet built |
| Evaluation design | 4 | +1 | design space mapped; harness built and proven useful. Predictive-validity (A1) and anti-pattern (D) families still unbuilt |

## Next logical steps (priority order)

**Rewritten 2026-08-31.** This section had grown to 37 entries, 20 of them done. A finished step is
history and its history is in its experiment note, so the completed ones were removed rather than
struck through: a list nobody can act on is not a plan.

### Waiting on the author — nothing else can substitute

0. **P0 — Mark the detection sheet.** `experiments/e55-detector-precision/results/detection-sheet.txt`,
   **145 boxes, 29 claims, stamped `20b1cef`**. Regenerated after five detector corrections, so the
   examples are behaviour the code actually has. `score.py` now **refuses** a stale sheet by name, so
   this cannot silently become marks about deleted code again.

0. **P0 — Fifteen fork positions.** `experiments/e57-fork-rebuilt/results/fork-sample.txt`. The claim
   fires for nobody after the rebuild, and only a person reading positions can say whether the rule
   is right or unreachable. **Nothing more should be built on `fork` until these are marked.**

0. **P1 — Fifteen pawn positions.** `experiments/e58-opening-development/results/pawn-sample.txt`,
   every one with development or castling as the engine's own preference.

0. **P1 — Two knowledge entries worth endorsing** (`fork`, `hangingPiece`) via
   `experiments/e63-knowledge-swarm/review.py`. **Read the definition against the detector before
   endorsing**: the fork entry defines an *absolute* fork, which is a subtype, and adopting it as the
   rule would narrow the detector wrongly.

0. **P1 — Two chess judgements.** Whether the Italian/Ruy Lopez castling norms should come from
   theory or from peers ([[experiments.e58-opening-development]]), and whether a check that also wins
   a pawn is too small to call a fork ([[experiments.e57-fork-rebuilt]]).

### Open, and unblocked

0. **ANSWERED — `maikel5` has no priorities at all** → [[experiments.e70-band-mismatch]]. Not a
   correction misfiring: **he is 1929 and was compared against the 1400-1800 band**. A peer lookup is
   keyed on `(band, time_control, claim)`, the speed arm has been checked against the games since the
   stratum guard and **the band arm never was**, so `--band` defaulted and nothing noticed. **6 of the
   12 review players are outside the band they were diagnosed against**, four above and two below, and
   the reference has only one stratum so there was nowhere else to put them. r(rating, asserted
   findings) = **−0.88**; the two players *below* the band get 5 and 6 findings, the most of anyone,
   which is the same defect with the sign flipped. `declared_band_is_wrong` now refuses this on the
   build side, 17 tests.

0. **P0 — the read side of the band mismatch is not fixed** *(new 2026-08-31)*. Refusing a bad
   reference at build time stops one being made; it tells a player nothing. Three options in
   [[experiments.e70-band-mismatch]] — refuse and say so, caveat and report anyway, or **build the
   missing 1800-2000 and 1200-1400 strata**, which is the only one that actually coaches those six
   players. It widens [[decisions.0005-scope-band-source-online-only]], so it is the author's call.
   **E71 makes the stake concrete**: what is being withheld from maikel5 is not a vague finding but
   9.28 win-probability points a game lost to the clock.

0. **ANSWERED — did the run rule take maikel5's endgame claim too?**
   → [[experiments.e71-why-the-pool-was-empty]]. Yes, and **the obvious suspect was innocent**:
   separating the two changes shows **E68's calibration cost zero priority slots** and **introducing
   the run at all (E67) cost six** — maikel5, maxhayastan and Odin5306, two each. E67 implemented the
   author's own words, so that is a correct change with a price, not a regression. The engine pass
   also confirmed both claims E70 could only infer: maikel5 gives away **9.28 wp/game** to the clock
   at **3.61 exposures a game against a peer's 2.50**, and is told nothing because the 1400-1800
   population gives away 11.18.

0. **ANSWERED — how many claim kinds can never reach a player?**
   → [[experiments.e72-can-it-reach-a-player]]. **13 of 50 are mute**: they fire, they are priced,
   and they never become a finding for anyone. 14 reach players, 12 are eligible and lose to
   something dearer, 10 are silent by design. **The whole endgame section is unreachable** — all six
   `endgame_error` variants — which is E67's run rule seen one level above the six priority slots
   E71 priced it at. **And the detection sheet is well targeted**: only 2 of its 29 claims are mute,
   so marking it is not time spent on claims nobody can be told about.

0. **P1 — the endgame threshold's reach cost belongs with the author's open judgements.** The run
   rule is what the author asked for and a single blunder was the thing being corrected, but a
   section that can no longer speak to any of twelve real players is a fact the person who set the
   threshold should have. Not a bug to fix unasked.

0. **P2 — `early_error.any` is mute while `early_error.white` and `.black` both reach players.** The
   pooled claim is redundant against its own split. Worth settling *before* building the
   `early_error` correction below, not after.

0. **SCREENED AND HELD — `early_error` → the opening claims.** The last of the six corrections
   → [[experiments.e73-opening-scores]]. 1a shipped as the development claims. **1b is built, tested
   and wired into nothing**: it fires for 2 of 12 with findings that read well, and then fails two
   screens. Its players are a **strict subset** of `early_error`'s, so `early_error` cannot be retired
   in its favour; and a **depth sweep is fatal** — four of five players flip in and out across window
   sizes, nobody is named at 30 games and four are at 45. **`early_error` stays, on evidence.**

0. **P1 — does 1b settle at greater depth?** The one test that would revive it. Both survivors are
   contiguous over the last three windows, which is what a claim looks like just before it settles,
   and every corpus on hand stops at 60 games per player. Fetching deeper histories is free and
   R-10-compliant; then `experiments/e73-opening-scores/depth.py` at 100+.

0. **P1 — `slow_development` against `plies_in_book`.** The one part of E69's screen not run, because
   book depth is not a claim in the peer reference. It settles whether book depth has anything left
   to add beside the development claims.

0. **P1 — Re-run E31 and E44** on the corrected move numbers. Both joined the author's noted moves
   with a formula that has since been fixed, and neither has been redone.

0. **P1 — Wire `build_resource` into the report.** The resource exists and nothing consumes it.

0. **P1 — The precise `rook_seventh` rule.** The cheap open-files screen removes 52 %, and the design
   note said the two-ply preventability search would be unnecessary only if the screen removed *most*
   ([[experiments.e66-rook-seventh-and-doubled]]). Half is not most.

0. **P2 — D15 defect (a): claims that never become candidates.** 27 of the vocabulary never fire for
   the review twelve. Four of those were an artefact of a key-format mismatch and are fixed; the rest
   are unexplained.

0. **P2 — D19: locate where the player actually left the opening book**, replacing the "edge of your
   preparation" phrasing with the move it happened on.

0. **P2 — D20: make the advice actionable**, with sources carrying an evidence class (C7, R-03). The
   knowledge base ([[design.knowledge-base]]) is this, and it is three entries deep.

0. **Parked — D21:** whether E33's 5-point floor is what produces incomprehensible examples.

0. **Parked — the expert review as a requirement.** Six of twelve returned Form A and three Form B;
   the detection sheet replaced it as the instrument, because judging a claim against a position is
   one repeated action rather than nine different ones.

## Open questions

Full register with owners and resolution paths: **[[open-questions]]**.
Resolved this cycle: A1, A2, C5, D1, D2, E1, F1. Reframed: D4. Added: C7 constraint, and
**D8** (the progress check's power) and **D9** (the constant is depth-dependent) — both surfaced by
fixing the calibration, which is the usual pattern: resolving a question exposes the two behind it.
Author-owned and waiting: B1–B5.

## Blockers

None technical. B1–B3 are waiting on the thesis author, but P1 and P2 can proceed without them.
