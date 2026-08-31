---
id: cas-state
title: State
desc: 'Where the project actually is right now, how far that is from the vision, and what comes next.'
updated: 1785255200000
created: 1785254500000
---

# State

**Snapshot date:** 2026-08-08
**Active mission step:** **M6/M7** — maintain, then repeat M4 with the next capability
**Last commit:** `feat(M6): refit the strength estimate for blitz, and make it name its speed`
**Scale:** 8,100 lines in `chesscoach/`, 849 tests at 85 % coverage, 25 experiments, 83 vault notes

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
| **`rook_seventh` and `doubled` corrected** | **done 2026-08-31** | Step 3 of the six corrections ([[experiments.e66-rook-seventh-and-doubled]]). **`rook_seventh` fires only when arrival was preventable**: three or more open files — the author's own threshold — and the claim goes silent, which removes **52 % of 4,077** rook-on-seventh positions. Half is not most, so the precise two-ply search **still has something to buy**, the opposite of what the design note guessed. **`doubled` gained both of the author's conditions and they are wildly unequal**: distance (1–2 ranks) removes **17 %**, while **64 % of doubled files never survive three moves** — 490 of 765 exist only until the end of an exchange, exactly as they said. `persistent_doubled` is built and tested but **not wired into S5**, which sees one board at a time; so the 64 % is what the claim *would* lose, not what it has lost |
| **Persistence everywhere, and endgame runs** | **done 2026-08-31** | Steps 3–4 of the six corrections finished ([[experiments.e67-persistence-and-endgame-runs]]). **Persistence generalised to every pawn weakness** on the author's extension — *"isolated pawn should also have similar persistance check"* — and **wired into S5**, which E66 left undone: a conceded weakness is kept only if it survives three more of the player's own moves, and a game that ends first is not a repair. **`endgame_error` rebuilt as a run**: 3 drops within 4 moves, with tactical drops removed **before** the run is sought, so a hung rook between two inaccuracies does not join them. **211 firings → 50**, and the conditions are unequal again — the residual removes **10 %**, the run condition the rest. The claim is now **explicitly residual**: when `fork` was wrong, this was wrong with it. **5 of 6 corrections built** |
| **Sheet and peer reference regenerated at HEAD** | **done 2026-08-31** | Five detectors were corrected after the sheet was written, so the marking queue described behaviour that no longer existed — marking it would have produced the undateable marks E55 was built to end, at the cost of the author's scarcest resource. Reference rebuilt across both strata and the sheet regenerated: **145 boxes, 29 claims, `GENERATED from commit 3af3206`**. **And the stamp is now read rather than merely written**: `score.py` **refuses** a sheet whose detectors have changed since it was generated, naming the commits. A stamp nothing reads is a comment, which is how E57's pin difference was scored against a sheet two commits old |
| **Endgame run threshold calibrated** | **done 2026-08-31** | A permutation test — same moves, same error counts, shuffled which moves erred, so the gap is clustering and nothing else ([[experiments.e68-run-calibration]]). **The window was letting chance in**: 3-in-3 beats the shuffled baseline **1.96×** with **0 of 200** shuffles reaching it, while **3-in-4 — the setting E67 shipped — was matched by one shuffle in eight**. The pattern is monotone: every move of slack lets the error rate masquerade as clustering. **The author's literal words beat the design note's relaxation** — *"imprecise one move after the other"* means consecutive, and the note had softened it. Adopted **3 in 3**; endgame errors **50 → 35**, from 211 under the old any-drop rule |
| **Development correlation screen** | **done 2026-08-31** | The screen [[design.opening-development-signals]] promised before the claims shipped, run at last and read straight from the rebuilt peer reference — no engine pass, and current by construction ([[experiments.e69-development-correlations]]). **No pair exceeds the 0.85 ceiling, so all four ship.** `slow_development`/`repeat_move` at **0.81** is distinct **narrowly** and should be re-run whenever either detector changes. The pair E59 measured at **0.68 is now 0.75** — nothing about the claims changed, the detectors underneath them did five times, which is the stamp lesson in a different artefact. `pawn_error` is the outlier and earns its slot: 0.16–0.29 against the others, median rate 6 % against their 41–46 %. Against `early_error` the highest is 0.55, so none is restating the general opening error rate |
| **One-command session** | **built** | `cli coach` — username in, report out; verified end to end on a live player, deterministic across runs |

## Distance to vision

| Dim | Vision item | Score | Δ | Evidence / why |
|---|---|:--:|:--:|---|
| D1 | V1 skill assessment | **3** | **+1** | **down to 2 on its first external test, and back up now the defect is repaired** → [[experiments.e27-held-out]], [[experiments.e29-attenuation]]. E27 tested it on 30 players fetched after every constant was frozen: **rapid excellent (MAE 79) and blitz barely an estimator (150 against 157 for guessing)**, compressed by slope attenuation that cross-validation structurally could not see (L-036). E29 corrected it by the standard remedy — divide the slope by the predictor's reliability, **0.641 measured on the fitting corpus alone**, a 1.56× stretch that the held-out players **independently demand at 1.48×**. Held out: **MAE 149 → 129**, bias −111 → −97, within 200 points 75 % → 88 %. Rapid was left alone because the same theory says it should not help there and the data agrees (79 → 111 if applied), which is what makes the blitz correction evidence rather than tinkering (L-037). Not 4: **blitz at 129 against 148 for guessing is still weak**, a −97 bias remains, and the vision asks for strength *and its variance* while every player still gets the same error bar |
| D2 | V2 knowledge assessment | **2** | **+2** | **the prober works end to end** — probe selection, move check, a local model classifying reasons at kappa 0.74 with zero false-ignorance (E07), `gap_type` written back. Not 3: the rubric's answer set is written and labelled by the author and the figure is in-sample, so it may not yet change a real player's finding |
| D3 | V3 style profiling | **2** | — | **built, half deliberately refused, and now compared against the right population** → [[experiments.e14-style-dimensions]]. One measured tendency — how much of a game is spent with the queens off — that varies between players (1.40) and is **independent of strength** (r = −0.069). Four of six candidates were strength wearing a style label. A live session found it comparing an all-blitz player against the *rapid* population (I-03); it is now mix-matched like every other comparison. Not 3: **the performance half does not survive** — everyone errs ~20 % less with queens off and players barely differ, so the report says what a player tends to do and refuses to say whether it suits them |
| D4 | V4 gap detection | **3** | **−2** | **eight sections, and the shallow-corpus caveat that held this back is gone.** On 150-game histories 70 of 84 players advised (83 %); on the **24 games a real user brings, 50 % → 79 %** once the player's other speeds are pooled in, with claim kinds 20 → 25 and overlap unchanged at 0.09 ([[experiments.e21-pooled-speeds]]). Groundedness 113/113. The lever was never more sections: six sections moved coverage 24 → 53 %, corpus depth and then speed pooling did the rest. **S7 reopened 2026-08-17** → [[experiments.e34-material-causes]]: the slot E10 emptied, refilled on a different question — not *how deeply do you calculate* but *did you check*. Two claims read **the move the player actually played**, the first detectors here to do so, closing the structural gap E33 named. Two further candidates were refused for correlating +0.917 and +0.914 with the overall error rate, which is where E10 closed the slot in the first place. Anonymous errors 52 % → 49 % | **Down 2 on 2026-08-23** → [[decisions.0011-detection-correctness-over-expert-agreement]]. The author read the reports against the games and found the detection itself wrong: forks mis-detected, `moved_into_attack` firing on ordinary exchanges, king-attack claims raised deep in endgames, and every Black move cited a number too high. **Coverage was never the question this score should have been answering** — 83 % of players advised says nothing about whether what they were told is true. The figures above stand; what they measure is reach, not correctness. It returns when D17's re-screen reports precision per detector on hand-verified samples.
| D5 | V5 prioritisation | **4** | **+1** | **ranks by what a weakness costs *above what it costs peers*** → [[experiments.e15-expected-gain]], corrected by [[experiments.e17-ranking-stability]]: raw cost named one claim to 70 % of players, so the excess over the population is what a plan can honestly promise, and occurrence rate is kept as a gate but **demoted as a ranking signal** (it ranks at chance, 6 % against 4 %). **And the first expert review then found that ranking blind in a way no internal measurement could** → [[decisions.0010-three-priorities-and-the-cost-pool]], L-039. For `bernes` the most expensive pattern in their games (7.3 wp/game, 10 of 53 games) was measured, correctly judged *not statistically unusual*, and **destroyed** — because being unusual was the only route onto the page. Cost now fills the slots unusualness leaves empty, labelled *"ordinary for your level"*, capped at 3 and never displacing a peer-relative finding; the band-level section (E25) still carries the shared weaknesses that pass its learnability screen. Verified across all 12 review players: **18 distinct claims, most-named 4/12**, so E17's degeneracy did not return one level down, and a second defect was caught on the way (a claim the player did *better* than peers was being offered as a priority). Not 5: it is still an **accounting** cost rather than a forecast, plan length is now near-constant at 3 for 11 of 12, **silence went 2/12 → 0/12**, and the vision asks for gain *per unit of study time*, which needs D5's unresolved question about how long anything takes |
| D6 | V6 path planning | **2** | **+2** | plans built and persisted, every step carrying a machine-checkable progress sign and a derived check point. No time estimates — D5 is unresolved and inventing them was refused |
| D7 | V7 progress tracking | **3** | **+1** | **restored, on evidence this time.** 57 predictions from 84 players with ~150-game histories; the constant is cross-validated at 2 *and* 5 folds with a fold spread of 0.011, and a held-out false-positive rate of **15 %** is stated in the output. Not 4: the test's **power is unmeasured** — no coached cohort exists, so nothing shows a real improvement could clear the bar (**D8**) |
| D8 | V8 explainability | **3** | — | the report exists, is deterministic, and is **13/13 grounded** on real players (E08 D4). **The 3 claimed last cycle was not earned**: reading a real report found Lichess theme keys in player-facing prose — *"a `trappedPiece` punishes you"* — which the groundedness metric scored 100 % on, because it only checks citation. Fixed (`phrasing.subject_name`), so the score now stands. Not 4: the report states measurements without explaining *why these one or two* were chosen over the rest, and the arbiter's reasoning is invisible |
| D9 | C1–C4 cost profile | **4** | **+1** | **re-timed 2026-08-06 against a genuinely empty cache**, which is what the previous 3 was missing. A new player, 60 pooled games: **5 s fetch + 76 s analysis ≈ 81 s**, of which 98 % is the engine. The same player again: **1.5 s**. A deep 197-game pooled corpus: **232 s cold, 2.9 s warm**. Cold scales at **~1.2 s per game**, so the 300-game accumulation ceiling is ~6 min for someone starting from nothing. Probes add ~2.7 s each (E07). **Zero cash throughout.** **A correction:** pooling speeds was expected to multiply session cost ~5× and does not — `--games 60` still fetches 60 games, it changes *which* 60, and only `--previous` raises the count. Not 5: one player on one machine, and the 300-game ceiling is extrapolated from 197 rather than measured |
| D10 | Evaluation capability | **5** | **+1** | both sides of the progress check measured (E05, E06), the **anti-pattern family D** built and run (E08), depth-robustness tested from both directions ([[experiments.e26-depth-robustness]]), and now **the pipeline run end to end on 30 players it was never built on** ([[experiments.e27-held-out]]) — which promptly caught a real generalisation failure in V1-blitz that cross-validation could not see. **An evaluation capability that only ever confirms is not one**; this one has now demoted a dimension on its own evidence. Not held back: the remaining gap is not a missing *measurement* but a missing *judge* — criteria 2 and 3 need a person, which is a resource problem rather than a capability one |
| D11 | Process & documentation health | **3** | **−1** | **down, and the reason is this table.** The cycle kept working — E20 was withdrawn on evidence, step 7 refused before it was built, three lessons recorded about misreading our own measurements. But across seven steps of the short-history plan the **scorecard rows went stale while the narrative below them was updated every cycle**: D4 still claimed 53 % coverage after pooling took it to 79 %, D5 still described raw cost, and *"What exists"* carried `Any agent | no` beneath seven built sections. The rule says close no cycle without updating [[state]]; it was honoured in the part that reads like prose and not in the part that reads like a score. Reconciled 2026-08-08. **Held at 3 on 2026-08-14 rather than restored**, because the same drift was found again one level out: the README still advertised 688 tests, 82 % coverage, "7.6 seconds", "rated rapid and classical games" and *"two of the eleven section agents"* against seven built. And criterion 6 was **ticked without ever being run** — executing it from an empty directory broke the chain twice (L-038). All corrected and the chain re-run end to end, but a process that catches its own drift only when something else forces it to look has not yet earned the point back |
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

**Reordered 2026-08-29.** The author's six corrections ([[design.detectors-name-consequences]])
supersede marking for four of the claims on the sheet: a detector about to be rebuilt is not worth
marking first, and `advantage_error` is not worth marking at all. Mark the **motifs** — that is where
the sheet still buys information, since the SEE rebuild has never been checked.

**Reordered 2026-08-23** → [[decisions.0011-detection-correctness-over-expert-agreement]]. The author
filled three Form B/C and found the detectors systematically wrong. **Detection correctness now
outranks expert agreement**, and the remaining Form A collection is dropped as a requirement.

0. **P0 — The author's first 23 marks, and what they change** *(2026-08-23)* →
   [[design.informative-claims]]. Four claims covered: `allowed_motif.hangingPawn` **4/5 — works,
   leave alone**; `moved_into_attack` **0/5 — broken**, cause verified (even-or-better captures fall
   through a guard and fire on every ordinary trade, `Bxd8+` at +6 among them); `early_error` **0/4**
   and `advantage_error` **0✓/5?** — both detect real errors and **name nothing that can be worked
   on**. Design note has options compared and a sequence: fix `moved_into_attack`, screen "name the
   error kind when ahead" (free), build per-opening outcomes from the **already-parsed ECO data**,
   then screen a peer-derived opening book. **D22** generalises the lesson.

0. **~~P0 — D17: rebuild the motif safety test on SEE and re-screen every detector.~~ Done; the
   re-screen is what produced the marks above.** The design fault
   is concrete: `tactics.py:280` `_lands_safely` asks *"attacked → is it defended?"* with no piece
   values, while `material.py` already has a static exchange evaluator the motifs never call, and
   `_is_fork` never asks whether the tactic **wins** anything. **Deliverable is precision per
   detector on hand-verified samples**, the method of [[experiments.e04-motif-precision]] — not a
   pass/fail.

0. **P0 — D18: make the evidence readable.** **Done 2026-08-23.** SAN, and citations carrying
   colour, opponent, date and a `lichess.org/<id>#<ply>` link. It also exposed a **content** bug: S1
   put the opponent's punishing move in `better_move`, so every `allowed_motif` example recommended a
   move the player could not make. Now stated as theirs — *"you played O-O-O, and Nxe5 punished it"*.

0. **~~P0 — D18 (superseded by the line above)~~** SAN instead of UCI, and game citations carrying colours,
   opponent and date. Cheap, and it is what makes every other check on this list faster for the
   author, so it comes early rather than last.

0. **P0 — Six detectors, corrected by the author** *(2026-08-29)* →
   [[design.detectors-name-consequences]]. Reading the precision sheet they rewrote the
   specifications for six claims at once, and **five share one fault**: they fire on a *state of the
   board* rather than on something that happened to the player. `advantage_error` is **retired**
   (uninformative, 182 instances stop being counted — the arbiter's ranking will move and must be
   inspected); `fork` is redefined around **newly** attacked pieces and **definite** material loss,
   so a fork against two defended pieces is not one; `rook_seventh` fires only when arrival was
   preventable; `doubled` needs adjacency and persistence past three moves; `endgame_error` becomes a
   **residual** claim — consecutive drops that the motif detectors do not already explain;
   `early_error` is replaced by two opening-knowledge claims and absorbs **A3**. Sequence and the
   parameters still needing calibration are in the note. **2 of 6 built** — `advantage_error`
   retired ([[experiments.e56-retire-advantage-error]]) and `fork` rebuilt
   ([[experiments.e57-fork-rebuilt]]); `doubled`, `rook_seventh`, `endgame_error` and the two
   opening claims remain. **The fork rebuild needs the author's eye before the next one starts:**
   it went from 146 firings to zero, and only a person reading positions can say whether that is
   the correction working or the rule being unreachable.

0. **P0 — Opening knowledge as development behaviour** *(2026-08-29)* →
   [[design.opening-development-signals]]. The author's proposal, and it **supersedes correction 1a**
   (book depth): castling time, development completion, **repeated moves of an already-developed
   piece**, and pawn-move share — all inside a window that ends when the player has castled and all
   four minors have moved, rather than at a constant ply. **Every threshold comes from the player's
   band, none is asserted**, which is what keeps *"castle by move 10"* out of the system and disposes
   of the French/King's Indian objection at the same time: peers who also leave that bishop home make
   the deviation zero. Measured separately, presented together — `overlap.drop_covered_claims` gives
   the headline the plan slot and the largest of the three explanations supplies the *why*. **The
   correlation screen runs first** (E10's precedent, |r| > 0.85), because the three explanations will
   overlap and the screen, not an argument, decides how many ship. No engine work of its own; the
   cost is a peer-reference rebuild, free on a warm cache. **Measurement built**
   ([[experiments.e58-opening-development]]); the claims are not wired up, and are blocked on the
   author resolving why the corpus puts the Ruy Lopez *faster* than the Italian when they predicted
   the reverse. **Book depth (1a) is reinstated by the author as learning feedback** — *"when the
   player usually stops knowing what to play by the book"* — rather than as a competing claim.
   **Expectation now built from strong players** ([[experiments.e59-strong-player-expectation]]):
   after standardising for the opening mix: **`slow_development` ships as the headline** (AUC 0.76),
   **`late_castling` beside it** (r = 0.68, under the redundancy ceiling),
   **`repeat_move_in_opening` at half strength**, and **`pawn_moves_in_opening` is dropped**.
   All four screened. The peer half is now done too
   ([[experiments.e60-peer-reference-rebuild]]): the claims discriminate within band, and the
   blocker moved to the **arbiter**, and the author cleared it with a costing method better than
   any of the three offered ([[experiments.e61-habit-cost]]): price each habit by what its own
   moves lost. Claims now reach plans (0/12 → 1/12) with no special case. **The remaining
   blocker is the assertion rate** — 1 of 12 where the band predicts ~3 — plus the standing
   debt that no development claim has been read by a person against the games it is made about. The remaining blocker is the **peer** half — separating 1600 from 2600
   is not the claim's job, and separating 1600 from 1600 needs the reference rebuilt.

0. **P0 — A knowledge base for every detected claim** *(2026-08-30)* →
   [[design.knowledge-base]]. The author's request, and it fills the *"runtime knowledge store —
   does not exist; designed in M3"* row in [[capacity.knowledge]]. **The four parts they asked for
   have four different provenances**, and treating them as one record is the trap: *what is detected*
   is a **specification** (the detector's own rule, `measured`), *what it costs* the project already
   **measures** per player, *links* are pointers the guide library already handles under review, and
   only *practice suggestions* need outside authority — the part the project's own expertise research
   is most sceptical of, having found training-method evidence thin and coaching's value contested.
   Recommended: **two layers**, a specification layer written by the author and never by a model, and
   a player layer that is measured or linked. **The specification layer is worth more and is
   cheaper**: this session's three broken detectors (`fork`, `late_castling`, `pawn_error`) each
   failed for want of a written *"what it is not"*, and all three were caught late by a person
   reading positions (L-050). **Design only — no code yet**, and four questions in the note are the
   author's to settle. **Option C chosen 2026-08-30** — the swarm drafts, the author approves,
   LLM agents used as far as they go. One objection I raised is weaker than I made it: the swarm
   invents on opening briefs because the pages genuinely do not discuss the opponent, whereas the
   web is full of real text about what a fork is — so the failure mode becomes *copying a mediocre
   source*, which fails loudly instead of plausibly. **The precise specification still stays with
   the author**: the web's definition of a fork is *"one piece attacks two"*, which is exactly
   what the broken detector implemented. Retrieved definitions are kept as an **independent
   cross-check** against the code, never as its spec. **Blocked on retrieval**: the searches fail
   because SearxNG is a metasearch proxy and the upstream engines block the container — not
   because of anything in this project's HTTP, which sends an honest User-Agent, spaces requests
   at 1.5 s and backs off 60 s on 429. Fix is SearxNG engine config, not client code.

0. **P0 — Mark the detection sheet** *(2026-08-29)* →
   `experiments/e55-detector-precision/results/detection-sheet.txt`, 33 claims, 165 boxes, stamped
   with the commit it judges. Change `[ ]` to `[y]`, `[n]` or `[?]` and run
   `experiments/e55-detector-precision/score.py`. **The top ten by firing count are where it
   matters** — `early_error.white.own` alone fires 200 times. Until this produces numbers D4 cannot
   move off 3 and nothing downstream of a detector can be trusted.

0. **P1 — The author's read of the opening resources** *(2026-08-28)* →
   `experiments/e49-opening-resources/results/resources.txt`. Twelve families, each with its main
   line, up to four variants ordered by the player's own games, and the plan sentences quoted from
   each candidate page. **Nothing is `reviewed=true`, so none of it reaches a player**, and quoting
   now rides on that flag as well as linking does — approving a page means "these sentences may be
   repeated in my name". The extractor cannot judge chess: a confidently wrong plan, plainly
   written, passes every rule in it.

0. **P1 — Wire `build_resource` into the report.** The resource exists and nothing consumes it. It
   attaches to D19, where the player left the book.

0. **P1 — Re-run E31 and E44.** Both joined the author's noted move numbers with the formula fixed in
   `f5872ff`, so every Black note was matched against the wrong move. **Their figures are not
   quotable until this is done.**

0. **P2 — D19: locate where the player actually left the opening book**, and replace the "edge of your
   repertoire" wording with something testable. Needs a free opening book, so it needs a design note
   before code.

0. **P2 — D20: make the advice actionable**, with sources carrying an evidence class (C7, R-03).
   Deliberately behind D17 — actionable advice on a wrong detection is worse than vague advice on a
   right one.

0. **Parked — D21:** whether E33's 5-point floor is what produces incomprehensible examples. **Raised
   by the agent, deferred by the author for discussion.** Not being worked on; recorded so it is the
   next place to look if the D17 re-screen finds the detectors sound on the disputed examples.

0. **Dropped as a requirement — the expert review.** Six of twelve Form A and three of twelve
   Form B/C exist. That is enough to have found what it found; it is no longer the thing being
   optimised, and the pre-registered 0/6 stands as a measurement of a system since shown defective.

0. **P0 — D15, defect (c): cross-section aggregate suppression.** **Done 2026-08-20** →
   [[experiments.e42-claim-overlap]]. Built as instructed, and **the premise was wrong**: the claims
   barely overlap (501 pairs, median 3 % coverage, none over 80 %), so `early_error` outprices
   `hangingPiece` by covering more distinct mistakes, not by containing it. `chesscoach/overlap.py`
   ships anyway with a threshold **calibrated** against the pairs `drop_redundant_aggregates` already
   deletes, and changes **1 player of 12** (maxhayastan, whose `time_pressure_error` was 77 % the same
   moves as `endgame_error`). Profile size 1.09×. **L-043.**

0. **P0 — D15, defect (b): swept.** **Done 2026-08-20** → [[experiments.e43-focus-gates]].
   `FOCUS_GAMES_WITH_DATA = 20` blocks **15** claims at a 20-game window and **0** at 60 — it measures
   the window, not the evidence. A fraction of the corpus fixes it at any value 0.70–0.90, and window
   agreement rises **66 % → 75 %**, decomposing 9 points of E39's disagreement as artefact rather than
   sampling. Two of the fifteen are the reviewer's own top concern (`allowed_motif.hangingPiece`,
   1.84× and 2.60×). **`FOCUS_MARGIN` is exonerated and stays at 1.25** — +0 claims at 20 games, and
   S5's pooled claim does not return even at 1.10. **Applied 2026-08-20 at the author's instruction:**
   `FOCUS_GAMES_FRACTION = 0.80` against a new `ClaimStats.corpus_games`, wired at eight sections, with
   a zero corpus size refused rather than waved through. Verified surgical — **15 of 122 claims change
   at 20 games, 0 of 123 at 60**, so the production path is byte-identical. Cost pool's share of the
   three falls **2.1 → 1.5**, reviewer agreement **0/6 → 1/6**, and the author's rating hypothesis
   **recovers from +0.19 to +0.54**, the gate having been noise on that measurement. Also surfaced: the **two strongest players
   (1981, 2033) are the only two with nothing assertable at 60 games.**

0. **P0 — D16 fixed, and the band note re-measured.** **Done 2026-08-20** →
   [[experiments.e45-increment-correction]]. `seconds_spent` now adds the increment back, which
   14.7 % of the peer corpus needed. `instant_move_error` falls **22.40 → 17.69** wp/game in rapid
   (−21 %) and 34.33 → 32.16 in blitz, and **still leads the band note in both strata**. Control clean:
   **0 clock-free cells moved**. Reference rebuilt (both strata) and all twelve reports regenerated;
   Sheriwoyama's leading finding changed and simonvj's recoverable gain doubled.
   **Caught on the way, and larger:** `early_error.black` (−0.13) and `allowed_motif.backRankMate`
   (−0.12) no longer clear E25's −0.2 bar and are **removed from the band note**. Neither reads the
   clock — they had been stale since the 2026-08-19 corpus rebuild, because E25 was never re-run
   against it. `band.py` now carries **3** screened claims, not 5.

0. **P1 — The clock, for the moves the reviewer noted.** **Done 2026-08-20** →
   [[experiments.e44-clock-on-noted-moves]]. They annotated without ever opening the clock, so no note
   says "instant move". Joining 263 move-numbered notes to the PGN finds **89 (34 %) played in ≤ 2 s**
   — delivered as `a-your-reading/<player>-clock.txt`, a **companion file that touches no note**,
   because the notes are the answer key E31 and E40 score against. **The hypothesis is not supported:**
   against a post-opening denominator the enrichment is **0.77× median**, only 2 of 6 players above
   1.0. Unlooked-for: for all six, **engine-flagged errors are instant less often than typical moves**,
   which sits awkwardly beside E25's band note and should be reconciled. Surfaced **D16**.

0. **P0 — Review pack rebuilt to match the reviewer's window.** **Done 2026-08-20.** E39's
   amendment, outstanding since 2026-08-19, executed by
   `experiments/e28-expert-review/regenerate.py` (report.txt only; `prepare.py` would re-sample the
   pack and overwrite the forms). All twelve reports rebuilt from the **same 20 games the reviewer
   read**, 17–20 after hygiene. No Form B/C existed to invalidate. **8 of 12 now lead with a
   peer-relative finding** rather than a cost-pool one, and the most-named leading claim is 2/12
   against 3/12. **The reviewer's six annotated players should be re-graded against these**, since
   their Form A readings remain valid but the reports they will be judged against have changed.

0. **P0 — D15, defect (a): the five material claims that never become candidates** — now the only
   untouched part, and after E42 and E43 the largest remaining one. A detector-threshold question
   ([[experiments.e31-move-level-agreement]], [[experiments.e32-hanging-pawn-screen]]), not a
   ranking or gating one.

0. **~~P0 — D15, defects (a) and (b): now known to be the large ones~~ (b) done above)** *(new 2026-08-20)* →
   [[experiments.e41-cost-ranking]]. Ranking by cost instead of peer excess was
   tested against the reviewer's own notes and **refused** — 0 of 6, worse overlap than the shipping
   rule. The refusal is what located the defect: **5 of 12 material claims never become candidates**,
   7 more are above the peer rate and cost 6.3–15.1 wp/game yet are blocked by
   `FOCUS_GAMES_WITH_DATA = 20` meeting a **20-game window** and by `FOCUS_MARGIN = 1.25`, and in the
   cost pool they lose to `early_error` — which covers more distinct mistakes, the containment
   reading having since been refuted. **(a)** is a detector-threshold question and **(b)** a gate
   question; neither is touched yet, and **(b) contaminates the expert review itself**, since a claim
   can be blocked purely because the reviewer read twenty games rather than twenty-five.

0. **~~P0 — D12: does `focus` need a magnitude floor?~~ Done 2026-08-05.** Yes, and it has one:
   `FOCUS_MARGIN = 1.25` on the point estimate, alongside the interval test. Chosen from the data —
   the smallest ratio among the swarm's 40 real findings is 1.40 — so it **removed nothing**, and
   re-measurement confirmed 19 advised / 13 kinds / 0.08 overlap unchanged. The defect was real and
   *latent*: no section had a large enough denominator to trip it until S5 (L-023).

0. **~~P0 — Stop adding sections; rebuild on the deep histories.~~ Done 2026-08-06** →
   [[experiments.e12-corpus-depth]]. Coverage **53 % → 83 %**, claim kinds 16 → 27, overlap 0.06 →
   0.05. Six sections had moved coverage 24 → 53 %; depth alone moved it further, in 45 minutes of
   mostly-cached engine time and with no new diagnostic capability (L-026).

0. **~~P0 — V1 skill assessment.~~ Done 2026-08-06** → [[experiments.e13-strength-signal]]. Rating
   estimated from blunder rate to **±103 points held-out**, reported as a range, with the rating
   hidden from the estimator.

0. **~~P0 — The context questions.~~ Done 2026-08-06.** Four questions before the analysis, every one
   skippable. Study time sizes the plan; the rest make the report honest, and `plays_elsewhere` turns
   an inherited blind spot into a stated one. D5 1 → 2, D12 2 → 3.

0. **~~P1 — V3 style profiling.~~ Done 2026-08-06** → [[experiments.e14-style-dimensions]]. One
   tendency of six candidates; four were strength wearing a style label, and the performance half is
   refused because players barely differ on it. **No scorecard dimension is at zero any more.**

0. **~~P1 — Expected-gain reasoning (D5).~~ Done 2026-08-06** → [[experiments.e15-expected-gain]].
   Not blocked by E03 after all: that asked whether a feature *predicts* errors, this sums what the
   *known* errors cost. Advice changed for **33 of 84 players**, claim kinds and sections unchanged,
   `advantage_error` 1 → 9 and `opening_disadvantage` 11 → 4. D5 2 → 3.

0. **P0 — The short-history plan is adopted and step 1 of 7 is built (2026-08-06)** →
   [[design.short-history-prioritisation]] § The solution. Five layers — supply, estimation,
   ranking, speaking, re-evaluation — sequenced so steps 1–4 need no new data and no architectural
   commitment, and the cheap screen deciding step 5's shape comes before step 5.
   **Step 1 done:** contaminated games excluded in `build_corpus` with the reasons counted and
   disclosed in the report (schema v10). 583 games (5.1 %), 55 of 84 players affected, worst case
   48.8 %. Coverage 70 → **69** advised and overlap 0.06 → **0.05**: it costs coverage and buys
   correctness, and `advantage_error` fell from 9 advised to 7 — the predicted berserk bias,
   confirmed, on the very claim E17 had flagged as over-selected.
   **Step 1b done** → [[experiments.e18-excluded-as-finding]], from the author's objection that
   excluding games throws away a finding. Right, and it splits: the **berserk habit** fails the cost
   screen (error rate only **1.04×** the player's own normal games — the habit varies, the harm does
   not) and is **disclosed rather than diagnosed**; the **time-budget chain** — clock spent early,
   mistakes twenty moves later — screens at **1.91×**, the best spread in the project, independent
   of `time_pressure_error` at **+0.204**, and is built as S2's fourth condition. 27 claim kinds now,
   2 players advised on it.
   **Step 2 done** → [[experiments.e19-blitz-stratum]]. **Answer: pool.** Blitz predicts a player's
   rapid behaviour as well as rapid predicts itself — **93 % of the reliability ceiling** — so step 5
   is one corpus with per-speed baselines, not three corpora with three references. It nearly went
   the other way: the raw blitz~rapid correlation is **+0.17**, which reads as "different construct"
   until rapid is correlated with *itself* at the same sample size and returns **+0.19** (L-031).
   The automaticity hypothesis is **refuted** — the gap's between-player variation is 2.39× against a
   2.08× noise floor.
   **Step 3 done.** The peer reference now carries cost per claim (peer schema v2, v1 still
   readable), `Measurement.peer_cost_per_game` and `excess_cost_per_game` exist (profile schema v11),
   and the arbiter ranks by the **excess** over peers rather than the raw cost. `advantage_error`
   lost 43 % of its advised slots (7 → 4). **Its definition of done was wrong**: E17's 70 %
   concentration was measured with the gates *forced open*, and production concentration was already
   13 % (L-032). The larger gain is in the report, which used to promise the whole cost back and now
   states what is recoverable — *"costing you 24.3 a game; players at your level lose 10.5, so
   roughly 13.8 is what fixing this could get back."* Still unverified: whether peer-relative
   severity keeps severity's 65 % stability gate-free.
   **Step 4 built, measured and WITHDRAWN** → [[experiments.e20-shrinkage]]. Replacing the interval
   test with a posterior shrunk toward the peers **halves** coverage at 24 games — 50 % of players
   spoken to becomes **26 %** against its own control — and costs on the deep corpus too (69 → 57
   advised). A Wilson bound uses the player's own games; a shrunk posterior pulls toward the
   population and is therefore *more* conservative, not less (L-033). Reverted. Kept:
   `chesscoach/shrinkage.py` with 29 tests, now the single shrinkage formula in the system since
   `expected_rate` calls it instead of doing the update by hand.
   **A 20-game minimum has lost the mechanism that was to justify it** and is an aspiration again.
   **Step 5 done, and it is the one that worked** → [[experiments.e21-pooled-speeds]]. Blitz is
   pooled into the corpus while the baseline stays per-speed, rebuilt for each player's own speed mix
   by direct standardisation, so E01's rule is kept rather than overruled. At **24 rapid games**:
   players advised **50 % → 79 %**, distinct claim kinds 20 → 25, overlap 0.08 → 0.09, groundedness
   113/113. More players *and* more claim variety, which is the opposite of buying coverage with
   generic output. **Three failures at the policy end and one success at the supply end** is now the
   strongest evidence in the project for where the constraint lives.
   **Step 6 done** → [[experiments.e22-accumulating-corpus]], and smaller than the plan implied. The
   corpus was **sliding**: at a fixed window twenty new games pushed twenty old ones out, so a
   returning player was diagnosed on no more evidence than the first time. `coach --previous` now
   grows the window to cover the old corpus plus the new games, capped at 300 for C1. **No game
   store was needed** — Lichess is the archive, so this was a request-size problem, not a storage
   one; and `check-progress` already measured over the new games only, so the harder half of that
   layer predated the plan proposing it. Measured warm: a **197-game pooled session costs 2.2 s**,
   2.9× the games for 1.6× the time, because a returning player's old games are exactly the ones
   already in the cache.
   **Step 7 refused on evidence** → [[experiments.e23-recency]]. Screened before building: games
   **over a year old** predict a player's recent claim rates about as well as games two months old
   (r +0.23 against +0.29, ceiling +0.19). Decay would have spent effective sample size — the
   binding constraint — for no measured gain. L-034: improvement changes a player's *level*, not the
   *shape* of their weaknesses, which is also why diagnosis against a peer population does not need
   to discount old games.

   **The plan is closed. Seven steps: four built, one withdrawn, one refused, one found already
   done.**

   | | |
   |---|---|
   | 1 exclude contaminated games | built — 583 games, coverage −1, correctness + |
   | 1b the time-budget claim | built — 1.91× spread, S2's fourth condition |
   | 2 blitz/rapid screen | **pool**, 93 % of the reliability ceiling |
   | 3 peer-relative severity | built — `advantage_error` 7 → 4 advised |
   | 4 shrinkage | **withdrawn** — halved coverage (E20) |
   | 5 pool the speeds | built — **50 % → 79 %** advised at 24 games |
   | 6 accumulate the corpus | built — and needed no game store |
   | 7 recency decay | **refused** — old games still describe the player |

   **The headline: a 24-game history now gets 79 % of players advised, against 50 % before, with
   more claim kinds and unchanged overlap.** Every gain came from the supply side; every attempt at
   the policy end failed.

0. **A live end-to-end session, 2026-08-08, and it found two defects.** `cli coach` run on a real
   player from a live fetch: 59 games, four context questions, strength, style, one finding, a plan,
   band notes, report — exit 0. **The player's 59 most recent games were entirely blitz**, which is
   step 5 working exactly as intended: before it they would have been diagnosed on stale rapid games
   from months earlier. Two defects the corpus could never have surfaced, because every corpus player
   has a rapid history (I-03, I-04): style compared an all-blitz player against the **rapid**
   population, and the report stated a rating estimate fitted on rapid games without qualifying it.
   Both fixed, and **the blitz refit is now done too** → [[experiments.e13-strength-signal]] § blitz:
   `1841.3 − 12045.1 × blunder_rate`, held out **±123** against rapid's ±103. Blitz is genuinely
   harder to read — a much flatter line, because blunder rate separates players less when everyone is
   rushing — and it still beats guessing the median (141) clearly. The estimate is **per speed and
   names its speed**, and `MIN_MOVES` applies within that speed, so a genuinely split player is
   refused rather than handed an average of two rating scales that sit ~80 points apart.
   The live player's estimate moved 1645 → **1594** against an actual blitz rating of ~1783 — so the
   refit went the *wrong way for them*, which is recorded rather than buried: one player is not
   evidence against a fit cross-validated on 81, and their blitz rating sits *above* their rapid one,
   the opposite of the population trend the line encodes.

0. **A band-level section, from the author's objection to peer-relative severity** →
   [[experiments.e25-shared-weaknesses]]. A weakness *everyone* at the level shares has almost no
   excess over peers, so it sinks and is never said — and `instant_move_error`, at **22.8 points of
   win probability a game, the most expensive claim measured anywhere in this project**, was advised
   to nobody for exactly that reason. E25 screened which shared claims are worth saying anyway:
   the median claim's correlation with rating is **−0.42**, but only **+0.15** once the player's
   overall error rate is divided out, so nearly all apparent learning is just general improvement.
   **Five of 27 survive** and only those appear, in a separate section worded as a statement about a
   population, capped at three, never becoming findings. The anti-pattern family is **identical**
   before and after — 66 advised, 25 kinds, overlap 0.09, 113/113 grounded.

0. **~~Outstanding: D9 needs re-timing.~~ Done 2026-08-06**, and the worry behind it was misplaced.
   Pooling speeds does **not** multiply a session's cost: `--games 60` still fetches 60 games, it
   changes *which* 60, and only `--previous` raises the count. Measured against an empty cache —
   a new player costs **~81 s** (5 s fetch, 76 s engine) and a returning one **1.5–3 s** plus
   whatever they have played since, at ~1.2 s per new game. D9 3 → 4.

0. **Superseded — the evaluation that produced the plan above** →
   [[design.short-history-prioritisation]]. A proposal to set the minimum history at 20 games and
   rank by an importance score (rate + severity + recency + game length) instead of gating.
   Measured rather than argued: scoring **does** degrade gracefully where gating cliffs, severity is
   the strong ingredient (**65 %** stable at 20 games) and occurrence rate ranks **at chance**
   (6 % against 4 %) — but severity alone names the same weakness for **70 %** of players (E17), so
   **E15's raw-cost ranking needs to become peer-relative**; that is a defect in work shipped the
   same day. Recency has nothing to act on for the median player (a 20-game window spans 23 days)
   and starting clock is inert on a corpus that is 74 % `600+0`. Cheapest real win found along the
   way: **8.0 % of games are berserked and 2.2 % abandoned**, unfiltered, biasing exactly the
   time-pressure signals under discussion.

   **Follow-up, and the biggest finding of the two:** the starting-clock weight is inert *because
   the fetch discards blitz*, and that filter costs a **median 82 % of a player's games** — measured
   over the same 84 players, who are the rapid-inclined end of the band to begin with. The swarm
   looks at roughly one game in five. That points at **admitting blitz stratified by time control**
   — never blended, so E01's objection stands — as the largest available lever on the binding
   constraint, with a cheap screen to run first: does a claim's blitz-versus-rapid gap vary *between
   players*, or is it a constant of chess (L-023, L-025)?

0. **P2 — Deferred by the author 2026-08-06: what to do about the 24-game user.** The swarm works on
   150-game histories and is silent for **43 %** of players at 24 (E16; E12 said 47 % on a different
   population). That is a constraint on *who it can help*, and it is deliberately parked until the
   system is complete rather than solved now. **E16 narrows the options**: every silent player has a
   median of **7** real patterns the corpus cannot confirm, so there is something to say and not
   enough evidence to say it. Relaxing `FOCUS_DISTINCT_GAMES` is now ruled out — it is 3 % of the
   problem. What remains: require a minimum history and say so; pool evidence across related claims
   to raise events per corpus; or report the unconfirmable patterns explicitly as *"suspected, not
   established"*, which is a change to the confidence vocabulary rather than to its thresholds.

0. **P1 — D12 reopens as a calibration question.** The magnitude floor was a safety net chosen to cut
   nothing; on deep corpora the finding distribution is **truncated exactly at it** (minimum ratio
   1.25, the floor). It now decides what the weakest advice sounds like — 11 advised findings sit
   below 1.4, against 1 before. Left at 1.25 because the arbiter's two-priority cap filters the
   weakest anyway, but the value should be revisited against real players rather than against the
   finding distribution.

0. **~~P1 — The binding constraint is `FOCUS_DISTINCT_GAMES = 5`.~~ Measured and wrong. Corrected
   2026-08-06** → [[experiments.e16-shallow-corpus]]. That was generalised from S6's experience
   without a census. Instrumenting every gate at 24 games: among silent players, the sole blocker was
   **the event occurring in fewer than 3 games (83 claims)** or **the interval failing to exclude the
   baseline (69)** — 96 % between them. `FOCUS_DISTINCT_GAMES` accounted for **5 claims, 3 %**.
   Moving that threshold would move almost none of the problem. The lever is **events per corpus**,
   which means games or better-pooled evidence — not looser thresholds, since the two gates that
   actually bind are the ones stopping the swarm inventing patterns from three data points.

0. **P0 — Answers from people who are not the author.** ~40 of them, labelled by someone else. This
   is the only thing standing between the prober and real use, and it is **not a modelling problem**:
   E07 settled the model (`llama3.1:8b-instruct-q6_K`, kappa 0.74, zero false-ignorance). What is
   weak is the *ground truth* — the answer set is written by me, labelled by me, and the figure is
   in-sample because the refusal split came after seeing which items failed. A better model cannot
   fix any of that. Until it is fixed, [[capacity.agents.prober]] § 4's gate stays shut and no probe
   may change a `gap_type` on real data.

1. **~~P0 — More predictions, so the constant can be calibrated at all.~~ Done 2026-08-03.**
   84 players, ~150 games each, 57 predictions. Fold spread 0.011; the constant is now estimated
   rather than guessed, and it moved 0.34 → 0.58 because the drift it corrects for was largely an
   artefact of the old sample's thinness (L-019).
2. **~~P0 — The constant is depth-dependent and the planner ignores that.~~ Done 2026-08-03 (D9).**
   Isolated properly: same players, outcome period whole, measurement period capped. Real, monotone,
   modest — fitted constant 0.488 → 0.594. **It also corrected L-019**, which had attributed a
   cross-corpus difference entirely to depth: 0.34 was never a fitted value, and drift at K=30 is
   +7.4 % rather than +11.2 %. Resolved by stating the measured **range (15–23 %)** in the output
   rather than fitting a curve through four points.
3. **~~P0 — The test's power is unknown.~~ Partly answered 2026-08-03 (D8)** →
   [[experiments.e06-progress-power]]. **The target is reachable** — improvers met it 25 % against
   8 %, and the regression confound is measurably absent. But p = 0.120 on 7 met events: suggestive,
   not established. Enough to justify building the prober, not enough to claim the swarm's targets
   detect improvement. Closing it properly needs a treated cohort (outside C1) or far more data.
2. **P1 — External validation of the detectors** against the CC0 puzzle themes. The strongest
   evidence available, because the labels are independent of me; E04 hand-checked only two motifs
   thoroughly. Needs the puzzle dump, for validation only.
2. **P1 — Implement evaluation metric D1 (inter-player divergence).** It would have caught M5's
   base-rate finding automatically instead of by eye, and it would have flagged the
   one-claim-kind problem above without a manual sweep.
3. **P2 — Validate the remaining confidence thresholds.** `PRIORITY_MARGIN` was set from measurement
   (L-013); the rest are still provisional and the split-half harness exists to check them.
4. **P3 — Widen the reference further and add time controls.** 38 players is workable for rapid;
   blitz and classical have no reference at all, and S2's time-pressure condition needs a shorter
   time control before it can be tested on real data.
4. **P3 — Peer reference rates.** Build the rating-band reference population once from the Lichess
   open database. Serves C6's remaining route *and* evaluation metric D2.
5. **P4 — Per-position parallelism** in the analysis core. The seam exists (the analyser is
   injected); E01 measured that per-game parallelism is dominated by the longest game. Not urgent —
   the current speed is already comfortable.
6. **P5 — Close M1's last item:** verify *My System*'s Part-2 chapter list against the text.

## Open questions

Full register with owners and resolution paths: **[[open-questions]]**.
Resolved this cycle: A1, A2, C5, D1, D2, E1, F1. Reframed: D4. Added: C7 constraint, and
**D8** (the progress check's power) and **D9** (the constant is depth-dependent) — both surfaced by
fixing the calibration, which is the usual pattern: resolving a question exposes the two behind it.
Author-owned and waiting: B1–B5.

## Blockers

None technical. B1–B3 are waiting on the thesis author, but P1 and P2 can proceed without them.
