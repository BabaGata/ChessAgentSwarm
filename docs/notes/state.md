---
id: cas-state
title: State
desc: 'Where the project actually is right now, how far that is from the vision, and what comes next.'
updated: 1788706252840
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
   **145 boxes, 29 claims, stamped at HEAD**. **Regenerated 2026-09-01 after two defects that had been
   hiding claims from it** (I-09, I-10): a working-directory-relative book path and a peer-reference
   key spelled two ways. The sheet's vocabulary goes **50 → 57** and it now shows, for the first time,
   `out_of_book`, `pawn_error` and `late_castling` — three claims the author has never been able to
   check. E72 established the sheet is worth the evening; that argument is stronger now.

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

0. **DONE — seven detectors rebuilt against the author's marked sheet** *(2026-09-06)*.
   Round two of [[experiments.e86-detector-audit]], driven by the 33 `[n]` marks on
   `detection-sheet copy.txt` rather than by reading code. Every rejected firing was reconstructed
   from `expert-review/games/`, the mechanism found, and the fix verified twice — against the marks,
   and swept over all **47,932 positions** of the reviewed games.

   | detector | marks before | after | corpus firings |
   |---|---|---|---|
   | `pin` (both claims) | 20% / 40% | **5/5** | 2,015 → 806 |
   | `allowed_motif.hangingPiece` | 40% | **5/5** | 3,203 → 775 |
   | `allows_square` (both claims) | 60% / 60% | **10/10** | — |
   | `allows_pressure.king` | 40% | **5/5** | — |
   | `missed_motif.capturingDefender` | 25% | 6/8 | 1,729 → 149 |
   | `trappedPiece` (both claims) | 40% / 40% | 6/10, from 3/10 | 357 → 200 |

   **In six of seven the author's comment beside the rejection was the rule** — *"an exchange is not a
   hanging piece"*, *"it lasted there for 1 move because it was taken"*, *"the piece should be on the
   black side of the board"* — and each generalised to every rejection of that detector (L-057). A
   defect found on the way: `wins_material` answers **100** for a king square, so every capture beside
   the enemy king claimed the king as loot.

   **Two things are not fixed and are not claimed to be.** `capturingDefender` traded recall hard and
   loses two accepted cases that are two-move combinations a one-ply test cannot see; two alternative
   rules were measured and both scored worse. `trappedPiece` is still wrong 4 times in 10, and two of
   those the author diagnoses as a *different motif* — a naming problem, not a detector one.

   **`early_error` was deliberately not changed.** It counts any error inside 30 plies, split by
   colour, and nothing else — the author asked what it detects and the answer is: not opening
   understanding. Its three rejections are right about the *claim* and not about the detector, so the
   fix is phrasing or retirement, and that is the author's call. Both options are written up in E86.

   Five existing tests asserted the old behaviour and were corrected, each saying so where it changed;
   one of them was written earlier in the same session from my own reading of a shape the author had
   already rejected twice in writing.

0. **DONE — the opening ends when the king moves; style stops being measured** *(2026-09-06)*.

   **`ready_at` was keyed on castling and that is the wrong signal.** The author: *"sometimes the king
   had to move because of check or something else and is not possible to do the casteling again."*
   `goydorak/EHDkU9YW` proves it — White was forced to `Kxf2` on ply 7, could never castle, and walked
   to g1 by ply 19. **The damage was not only the citation**: `measure_development` closes its window
   at `ready_at`, so a game with no castle had *the whole game* as its opening window, and
   `moves_in_window` is the denominator of `slow_development`, `repeat_move` and `pawn_error`.

   | | before | after |
   |---|--:|--:|
   | windows that never closed | **140 (21 %)** | **57 (8 %)** |
   | largest `moves_in_window` | **89** | **33** |
   | never "developed" | 73 (11 %) | 29 (4 %) |

   `king_moved_at` (castling included) replaces `castled_at` in `ready_at`, and `DEVELOPED_MINORS = 3`
   of 4 replaces all four. `castled_at` is kept because `late_castling` is about castling.
   **Not changed:** `late_castling` still measures the castling ply, so a player whose king walked to
   safety is still judged on not castling — a separate decision.

   **Style is no longer measured.** `S10StyleTendencies` unhooked from `default_agents`, `cli._style`
   returns early behind `STYLE_MEASURED`. `queens_off` parsed a FEN per diagnosable move per player and
   nothing read the result. Module and tests kept whole.

   **Two more marks fixed:** `allows_square.outpost` is exempt in endgame positions (`ENDGAME_EXEMPT`;
   `rook_seventh` deliberately is **not** — a rook on the seventh is most dangerous there), and
   `concedes_weakness.backward` no longer counts an a/h-file pawn with an enemy pawn still on that
   file — **12,772 → 10,820 (−15 %)**.

   **`determined_by` explained and kept.** `GapType` is *knowledge or skill gap* (`hypothesis`) and
   *guessed or asked* (`determined_by`). Sections can only write `UNKNOWN`/`INFERRED` (L-002); only the
   prober writes `PROBED`, and `--apply` is off. Inert — planner and arbiter never read it, the report
   withholds it — but **unlike style it costs nothing to keep**: two constants in a frozen dataclass,
   not a walk over every move, and it is the field the prober would write into. Removing it means
   editing eight sections, the model and the serialiser for zero runtime saving.

   **Still open from the sheet, needing a decision rather than a fix:** `out_of_book` should perhaps be
   scoped to *"the main openings of the players ... that they play regularly"*; `pawn_error.any`'s value
   was questioned (*"I don't see any value from this kind information"*) and only its wording has been
   improved; `moved_into_attack` may need an opening exemption (*"could be a normal move in the
   opening"*); and `miscounted_exchange`'s *"away from the kings"* phrasing was queried.

0. **DONE — the opening claims corrected; style and gap type withheld** *(2026-09-06)*.

   **Withheld from the report**, both behind flags rather than deleted: **style**
   (`STYLE_IN_REPORT`) and **the prober's gap type** (`GAP_TYPE_IN_REPORT`), on the author's
   instruction. Measurements continue — `plays_queenless` still feeds the peer reference, probes are
   still recorded, `--collect` still grows D10's answer set. The gap-type flag also removes a live
   inconsistency: `--apply` is off by default, so `determined_by` is `INFERRED` on every real finding
   and the paragraph could not have appeared anyway.

   **`slow_development` cited checkmate as its evidence.** `ready_at` is `None` whenever the player
   never castled, and `at_ply` fell through to a fallback promising *"their last opening move"* while
   returning the last move of the **game** — `Rf7#` on move 36. Bounded to the opening window, it now
   cites move 5. The author's proposed cause (first rank read as home) was not it: `HOME_SQUARES`
   holds only the four minor-piece squares.

   **`slow_development` now fires only where development was on offer.** The drift test was built by
   analogy with `late_castling` and **measured out** — an accepted game at drift 0 against both
   rejections at 1, so no threshold separates. `engine_wanted_development`, which already gates the
   habit costs and `pawn_error`, separates **0/0 against 3/5/7**. **5/5** on the marks; 169 slow games
   become 157.

   **`out_of_book` charged 53 % of its instances to the wrong player.** A book walk stops at the first
   move outside the tree, so once anyone leaves it no later position is in it — and the claim never
   asked whose move left. Across the reviewed games the book ran out in 658 games and **the opponent
   left first in 377 (57 %)**, carrying **918 of 1,729 instances**. `1.e4 d5 2.exd5 Nf6 3.c3` is the
   author's own case: White deviates and *Black* is charged for the recapture and everything after.
   `left_book_themselves` now gates the game entirely — not an opportunity either, since a game where
   staying in book was impossible dilutes the rate rather than measuring it.

   **The coverage problem underneath is not fixed and is not claimed to be:** the book is thin on
   offbeat lines, so `3.Nc3 Nxd5` in the Scandinavian still counts as a departure. What went is the
   half of the claim that was never about the player.

0. **DONE — style withheld from the report; the prober's standing traced** *(2026-09-06)*.

   **Style is out of the report**, on the author's instruction — *"this is a functionallity that was
   not fully developed and tested"*. Behind `explainer.STYLE_IN_REPORT`, the shape the two earlier
   retirements set. **The measurement stays**: `S10StyleTendencies` still feeds `plays_queenless` into
   the peer reference and `style.describe` still computes the tendency, so the population figure keeps
   accumulating and turning the paragraph back on needs no rebuild. Three tests asserted it rendered;
   they lift the flag and say why, because if the missing half is ever finished this is the wording it
   must come back with — including the refusal, which is the part most easily lost.

   **The prober: built, measured, wired — and by default it changes nothing a player reads.**

   | | |
   |---|---|
   | runs end to end | yes — `cli probe` asks, checks the move deterministically, classifies the reason locally, writes `ProbeRecord`s |
   | consumed downstream | **only** by `explainer._gap_meaning`, and only when `determined_by is PROBED` |
   | `gap_type` rewritten | **no** — `--apply` is off by default |
   | planner / arbiter use it | **no** — zero references to `gap_type` in either |

   So with the shipped flags a probe is **recorded and inert**: it cannot change the ranking, the
   plan, or the report. The gate is shut deliberately, not by oversight — E07's kappa 0.74 is
   **in-sample**, on answers the author wrote and labelled, with the refusal fix made after seeing
   which items failed. What it needs is **~40 answers from people who are not the author**, which is
   what `--collect` accumulates.

   **What it would reach if opened**, measured over the twelve reviewed players at a 60-game window:
   `PROBEABLE_KINDS` is `allowed_motif`/`missed_motif`, which is **15 of 28 asserted findings**, and
   **8 of 12 players** have at least one. So the value is real and it is currently unbanked.

   **Its one unconditional value today**: the move check is deterministic and runs with no model at
   all, so *"played the right move"* versus *"did not"* is established either way, and an unreachable
   classifier records as **unavailable** rather than as the player being unclear (L-020, I-02).

0. **DONE — status check on the preference system, cost and wording** *(2026-09-06)*.

   **Preference system (V3, `plays_queenless`) — working, and its absence from the sheet is by
   design.** `S10StyleTendencies` **never emits a finding**: a tendency is not a weakness and routing
   it through the arbiter would make it compete for a priority slot. It reaches the report as a style
   line instead, so `plays_queenless.any.own` sits in the sheet's NEVER FIRED list correctly rather
   than as a broken detector. Measured for all 12 reviewed players (494–1,707 moves each, all past
   `MIN_MOVES`), **notable for 6** — Crossfire1983 at 1.50× the population, cademan and Hirsican at
   0.58–0.59×. The performance half stays refused, per E14.

   **Cost — both senses working.** Ranking (D5): a real run for `Crossfire1983` produces 3 priorities
   ranked on excess cost over peers, each with a falsifiable target — *"Costing you about 7.1 points
   of win probability a game. Players at your level lose about 3.3 to the same thing, so roughly 3.8
   a game is what fixing this could get back."* Runtime (D9): 60 games with a warm cache,
   **10,419 / 10,419 cache hits**, zero engine calls, zero cash.

   **Wording — the D8 defect was back, and is fixed.** Found by reading a real report rather than by
   any test. The five development and opening claims had **no phrasing at all**, so the headline read
   `pawn_error: any.` and the plan said `Work on any:`; splitting `out_of_book` per opening
   reintroduced it a second way, since only the pooled subject had a sentence. Sentences, plan
   phrases and actions added for all five, with `late_castling`/`slow_development` keyed by **basis**
   so *"later than is usual in the openings you play"* and *"later than you usually do"* stay
   distinct. `tests/test_phrasing.py` was **empty** and is now the guard.

   **Checked and not a defect:** two `out_of_book` findings with byte-identical statistics
   (`Bird Opening` and `Queen's Pawn Game`, both 21 instances over 6 games, 70.0 % against 49.2 %).
   The tallies are per-family and cite different games; the collision is small-integer arithmetic —
   6 games × a fixed window, 21 plies out of theory in each — and per-opening counts vary widely
   elsewhere on the sheet.

   **Still open, minor:** the plan's *why* line says *"against 3.9 % elsewhere"* for a self-baseline
   and *"for peers at your level"* for a peer rate. Both are accurate, the wording is inconsistent,
   and making them uniform would misstate which baseline was used — so it needs a phrasing decision
   rather than an edit.

0. **DONE — the sheet shows the motif's own move and the pieces that make it true** *(2026-09-06)*.
   For an `allowed_motif` claim the sheet showed the player's **losing** move, not the motif — the
   motif belongs to the opponent's reply, and that reply was stored in `tally.better_moves` and never
   rendered. So a reader judging *"is this a pin?"* was shown a move that is not the pin.
   `chesscoach/motif_evidence.py` names the squares and the sheet prints them:
   `punished by Qb5 -- pinner Qb5, pinned nc6, against ke8`. **53 of 53 motif examples carry it.**

   The first version re-stated each detector's conditions to locate the squares and restated them
   incompletely, disagreeing on **303 of 5,935 moves** in one game for `hangingPawn` alone and on six
   other motifs. The corpus test caught it; `evidence()` now defers to `detect_motifs` so the two
   agree by construction. **Same failure as `_still_there_later`** — a second implementation of a rule
   that already had one.

0. **DONE — `late_castling` conditioned on drift; 28 of 32 rejections resolved** *(2026-09-06)*.
   Every position the author marked `[n]` was reconstructed and re-run: **24 no longer fire**, 3 are
   moot (`early_error` retired), 1 is fixed by the castling gate below, **3 still fire**, and 1 is
   undiagnosed.

   **`late_castling` now asks whether the player was drifting while they were late**
   ([[design.castling-under-drift]]). `drift_before_castling` counts their errors after the book move
   and before castling that **no motif explains** — motif-explained errors are already charged to
   `allowed_motif`/`missed_motif`, and charging them twice is what `overlap.py` prevents. This gives
   the retired `early_error` the use its retirement note promised: it failed as a *claim* because "you
   go wrong early" names a circumstance, but as an **input** it was never wrong about what it counted.

   **5/5 on the marks**, with the rejected game at **drift 0** against 2/3/3/7 for the accepted ones.
   The separation is wide enough that `DRIFT_MOVES = 2` is not load-bearing — a bar of 1 gives the
   same answers — and the note says so rather than implying the number was calibrated. Across the
   reviewed games **168 late-castling games → 93 (55 % kept)**, with **33 at zero drift**: a fifth of
   the claim was firing on players who castled late while playing well.

   **Still firing, and all naming rather than detection problems:** `allowed_motif.trappedPiece`
   (`9biHZYZy` — the author says *"This is fork"*), `missed_motif.trappedPiece` (`5853VxPL`),
   `missed_motif.pin` (`xGJzDV3d`). Nothing in the vocabulary arbitrates between two motifs firing on
   one move.

   **`concedes_weakness` fixed, and the suspicion was right.** `_still_there_later`'s docstring said
   *"still on the same file"* and the code asked whether **any** file carried the weakness —
   `conceded()` returns feature names, so the caller never had a file to track. On the author's game
   Black was already doubled on **f**, `dxc5` doubled **c**, the c-file cleared on the very next move
   (*"It lasted for 1 move"*) and the unrelated f-file doubling held the concession alive.
   `created_files()` now returns the files the move made and the persistence test requires one of
   those to survive. **15/15 on every `concedes_weakness` mark**; across the corpus `isolated` 96 %,
   `backward` 96 %, `doubled` 90 % kept — narrow, as a fix aimed at one defect should be.

   **All 32 rejections are now accounted for**: 28 no longer fire, 1 retired, and the 3 remaining
   are **not a defect** — the author: *"If the position detects multiple motifs at the same time it is
   ok, they are valuable input for the general overview."* What was missing was the ability to see
   *why* a name was given, which round seven adds.

0. **DONE — the detection sheet reads 60 games, not 20** *(2026-09-06)*.
   `capturingDefender` was correct after the rebuild and still said nothing. The cause was the review
   window. **20 exists because a human read 20** ([[experiments.e39-review-window]]: the leading
   finding changes 75 % of the time between 20 games and the full corpus, so a ranked comparison
   against a reviewer must use their games). **That argument does not reach the detection sheet** —
   no box on it is ranked or compared against a human's ordering; each asks whether one claim is true
   of one position. E39 already named the cost of the narrow window: *"judging the swarm at its
   weakest operating point"*.

   Everything else says 60: `cli.py` defaults to 60 for `corpus` and `session`, `state.md` describes
   *"one player across ~60 games"*, every reviewed player has 60 on disk, and E43 measured 15 claims
   blocked at 20 and none at 60.

   | | window 20 | window 60 |
   |---|--:|--:|
   | claims with instances | 25 | **36** |
   | boxes to mark | 125 | 178 |

   **Twelve silent claims now fire** — `endgame_error.any` (23), `late_castling.own` (35),
   `time_budget_error.after_overspending` (38), `slow_development.own` (20),
   `missed_motif.trappedPiece` (9), `missed_motif.skewer` (4), `missed_motif.capturingDefender` (4)
   among them. **Marking cost barely moves** because `--examples` caps the sample at five per claim:
   53 more boxes buys eleven more claims.

   `capturingDefender` went from **1 instance in 6 opportunities (16.7 %)** to **8 in 24 (33.3 %)**
   against a 30.2 % peer rate. The detector was right and the corpus was too small to use it.

   Two claims stopped firing — `out_of_book.any` and `missed_motif.hangingPawn` — and both sat
   **below the peer rate at either window**, so the extra games confirmed the players are ordinary
   rather than hiding anything. At 20 they were reaching players on sampling noise.

   `--window` defaults to 60 in `detection_sheet.py` **only**; the other review experiments keep 20
   because they are the ranked comparison E39 was about. Sheet regenerated: **36 claims, 178 boxes**.

0. **DONE — `early_error` retired, `capturingDefender` rebuilt on the author's design** *(2026-09-06)*.

   **`early_error` retired** on the author's instruction — *"this is not valueable measure"*. It
   counted any error inside 30 plies split by colour and nothing else; the sentence built on it
   implied a cause it never established. Behind `EARLY_ERROR_RETIRED`, the shape
   `s3_endgame_technique.ADVANTAGE_ERROR_RETIRED` already set, so the tally survives for asking later
   whether opening-window errors are explained elsewhere. Its three claims go **63/85/129 → 0** on the
   sheet. `slow_development`, `late_castling`, `repeat_move` and `out_of_book` already carry the
   opening, and each names a behaviour.

   **`capturingDefender` rebuilt** on the design the author gave rather than on another correction:
   take the defender, **let them recapture**, then ask whether a piece it guarded can now be taken.
   The shipped rule asked a one-ply question; this is a two-ply one. Four readings were measured
   against the eight marks; two tied at 6/8 and the tie was broken by the author's own example —
   `Nxf6+ Nd7xf6 Bxe5`, *"I take a bishop, knight takes a bishop and then I can take another knight"*
   — which only the pieces-only reading finds, and which the one-ply rule could not see at all.
   Pawns are not targets (the line `_is_hanging_piece` draws) and every recapture is tried rather than
   the cheapest, because the recapture is theirs to choose. Corpus firings **1,729 → 149 → 80**.

   One branch needed a distinction the author's sentence does not make: whether the guarded piece may
   run turns on **who holds a move**. In their line the defender spends theirs recapturing, so an
   immediate exchange test is right; a capture nothing can answer leaves them a free move, so that
   branch asks whether the piece falls whatever they do.

   **Reference and register rebuilt again afterwards** — this is L-058's own discipline applied to
   itself, since two detectors changed. 821 → **803 cells**, `early_error` down to **zero cells**, and
   the register's 24 verdicts unchanged. Full suite green; sheet regenerated, 19 claims with
   instances, 125 boxes to mark.

   **`capturingDefender` is still silent for these twelve players**, and honestly so: at 80 firings
   across 47,932 positions it is too rare to reach the confidence gate on a 20-game window. The
   detector is now right and the corpus is too small to say anything with it — a different problem
   from the one it had.

   Two marks the design overrules, recorded rather than hidden: `Bxe6+` (**[y]**) guards only a pawn,
   and `Qxd8` (**[y]**) wins nothing under any of the four readings.

0. **DONE — the four silent claims were compared against the old detectors** *(2026-09-06)*.
   The author chose *"loosen the confidence gate"*. **The gate was not the cause.** Every section's
   `measure()` showed the detectors still producing instances — 19 for `allows_pressure.king`, 64 for
   `allowed_motif.pin`, 67 for `allowed_motif.hangingPiece`. They died on `rate <= baseline_rate` in
   `assign_tier`, and `peers-e84.json` was built at `c8ed84f`, **before the fixes**. Player rates fell
   60–91 %; the population rates did not move. Loosening the gate would have manufactured findings
   from a comparison whose two arms were computed by different code (**L-058**).

   **Reference rebuilt at HEAD** — six band/speed references, 262 player-slots, 348 → **821 cells**.

   | claim | peer rate before | after | sheet instances |
   |---|---|---|---|
   | `allowed_motif.pin` | 12.1 % | **4.8 %** | 16 → **23** |
   | `allowed_motif.hangingPiece` | 11.0 % | **5.2 %** | 14 → **20** |
   | `missed_motif.pin` | — | — | 8 → **11** |
   | `allows_square.outpost` | — | — | 6 → **10** |

   **No gate threshold was changed and none should be.**

   **`separation.py` was stale the same way** — it is generated from the reference. Regenerated,
   21 → 24 entries: the three `trappedPiece` claims get a peer comparison back, and
   `allows_pressure.king` and `missed_motif.pin` become flat. `allows_pressure.king` at dispersion
   **1.14, p = 0.23** over 50 players, so **S8 now asserts nothing at all** — the old detector counted
   pawns and the king as attackers, so what looked like players differing on king safety was largely
   how many endgames each played. Measured before accepting: asserted coverage is **identical** under
   both registers (12 claim-instances, 10 claims, 4 players); the regenerated one costs one
   sub-threshold claim.

   Twelve tests failed, none wrong about its own subject — each had borrowed a claim key that has
   since gone flat (`test_speed_strata` testing speed mixing, `test_arbiter`/`test_planner`/
   `test_explainer` testing ranking). All now use a subject absent from the register and say why.
   S8's five reporting tests lift the register entry for their duration; two new tests record what a
   player actually gets. **Full suite green.**

   Sheet: `experiments/e55-detector-precision/results/detection-sheet-2026-09-06-fixed-detectors.txt`,
   stamped `commit 64e1259`, 22 claims with instances. Neither marked sheet was overwritten.

   **Still open, and genuinely:** `capturingDefender` remains silent for honest reasons — one instance
   in seven opportunities for the missed claim, and the allowed claim sits *below* the player's own
   rate on other motifs. And `separation.py` states *"nothing here retires a detector"* while S8, having
   one claim and no sibling baseline, is retired by it. Recorded, not fixed.

0. **DONE — both detector defects fixed** *(2026-09-06)*.
   **`trappedPiece`** tested escape squares with `is_attacked_by` rather than an exchange: on **6,249
   real positions, 80 firings become 41** — 42 false positives removed, 3 added.
   **`fork`** excluded any target that *anything* friendly already attacked, when the author's rule is
   that both targets must be newly attacked **by the piece that moved**: **73 forks become 109**, 36
   real forks recovered and none lost, three checked by eye. This one was withdrawn once on a
   misreading of the written definition and reinstated when the author clarified it; the test now
   carries the clarification.
   **Neither needs a rebuild** — all three `fork` and all three `trappedPiece` claims are already
   withheld from peer comparison by the separation register.


0. **DONE — the knowledge base is endorsed and servable**
   → [[decisions.0010-assistant-endorsed-the-knowledge-base]] *(2026-09-06)*. **18 of 18 entries
   reviewed**, loaded into the graph, and `for_player` now returns text instead of `None` — the
   explanations reach a report for the first time. Endorsed **by the assistant under the author's
   explicit delegation**, and every note records that it was not a human reading.
   **Eight entries carry a recorded disagreement with the detector they describe**, including the two
   known defects: `trappedPiece` (E86 D-2, escape squares tested by attack rather than exchange) and
   `fork` (E86 D-1, misses a fork whose victim was already attacked). Both are endorsed as definitions
   of the *concept*, explicitly not as descriptions of the code.
   **For the author to check when there is time** — the ADR lists all eight and how to reverse any of
   them.


0. **DAY 1 DONE — clone-and-run proven, and one caveat found**
   → [[experiments.e91-fixed-depth-is-not-reproducible]] *(2026-09-06)*. A fresh clone renders a
   report with **no install, no engine and no model**, and a full `coach` run inside the clone from an
   **empty cache** produces a complete report. README rewritten with real prerequisites and the
   shipped reference; `docs/samples/sample-profile.json` demos instantly.
   **The caveat:** the same games analysed twice give slightly different findings, because a fixed
   depth is not a fixed answer — the same position scores **-5 cp** cold and **-24 cp** after the
   engine has searched others, since the transposition table carries state. Not a bug here and not
   worth engineering around; a fresh clone is self-consistent because it builds its cache in its own
   order. **Stated as a limitation.**


0. **THE SYSTEM WORKS, AND THE BLOCKER WAS NEVER A DEFECT** *(2026-09-06)*. Two days from the
   deadline, `coach` was run end to end and produces a complete coaching report: a strength estimate
   with an interval, prioritised findings with rates, cost in win probability, recoverable gain,
   **clickable links to the exact moves**, falsifiable progress signs, the openings played, and a
   limitations section. **Five of five corpus players produce a full report** — 29–30 games, three
   findings and three plan steps each, no crashes and no empty reports.

   **The blocker was that nothing under `data/` was committed**, so it ran on one machine and nobody
   else could reproduce a report. 4.6 MB now tracked: the peer reference, the opening book and norms,
   the shelf, the knowledge base. **Verified by cloning the repository and rendering a report with no
   install, no engine and no model.**

   **The loops that cost the time**, recorded so they are not re-entered: (a) verify → find a defect →
   verify the fix, with **no stopping rule anywhere that says good enough**; (b) correctness read as a
   precondition for use, although the report already states its own limitations and was designed to
   be honest about being imperfect; (c) the peer reference as a two-hour bottleneck that any claim
   change invalidates; (d) **the assistant proposing measurement every time it was asked what to do
   next, while `coach` sat available and unrun**.

0. **DEFERRED to after the deadline, all recorded, none required for a working system:** the two
   detector defects (E86 D-1/D-2), the fabrication guard, finishing the knowledge base, the report
   restructuring by aspect, per-aspect standards, prefetching candidate positions.
   **Do not demo `ask`** — it fabricates on topics the shelf does not cover and cites a real author
   while doing it. `coach` has no such failure mode.


0. **FINDING — where the variance is** → [[design.better-claims]] *(2026-09-06)*. Measured within
   band, **22 of 24 non-tactical claims separate players and only 10 of 30 tactical/positional ones
   do**, and the magnitudes are not close: habits and knowledge reach 8×, 14×, 36× where the best
   tactical claim reaches 2.1×. **A rating band is approximately a measure of tactical strength**, so
   conditioning on it removes exactly the variance tactical claims measure — structural, not a
   detector defect. The design error underneath: `endgame_error` splits by **knowledge** (rook, pawn,
   queen endings — 6 of 6 separate) while the motif claims split by **one skill** sliced thin (board
   vision), using the Lichess taxonomy of *what happened on the board* as a taxonomy of *what the
   player is missing*. **Direction:** split `out_of_book` per opening, `concedes_weakness` per
   structure; measure exposure as well as conditional rate; use the tactical detectors as *evidence*
   under a separating claim rather than as diagnoses.


0. **DONE — knowledge base regenerated, loaded, and retrieval tested**
   → [[experiments.e89-why-nothing-usable]], [[experiments.e90-retrieval]] *(2026-09-06)*.
   **Six defects fixed** between a good page and a stored definition — `hangingPawn` searched for a
   different concept, the plain phrase was never asked (so "undefended pawn chess" returned the
   Turochamp article), page markup reached the output as a definition, an existential "There" was
   read as a connective, the scout took a random three of a varying list, and the ordering fix had
   the truthiness bug it was fixing. **The knowledge base and the graph were separate stores** and
   no definition was ever retrievable; `load_definitions` closes that. **Retrieval: 10 of 10
   concepts return their own definition at rank 1.**

0. **P1 — the agent fabricates when asked what the shelf does not cover.** Asked for the Sicilian
   Najdorf it invented a descriptive-notation move list and **credited Howard Staunton**. Both
   existing guards were measured and neither catches it: a similarity floor cannot separate covered
   from uncovered (they overlap — Najdorf scores 0.8875 against a covered 0.8272), and `grounding
   .check` passes it because the model assembled real fragments from the retrieved passages. R-02 and
   R-03 in one output.

0. **P2 — four claims have no definition and may not be answerable.** `hangingPawn`,
   `allows_pressure`, `moved_into_attack`, `pawn_error` are this project's own error categories
   rather than terms the literature defines — E65 found nine of fourteen keys are jargon. Seeding
   them from a related authoritative definition, as the tactical motifs were seeded from Lichess, is
   the author's call.

0. **P2 — attribution is a guess for swarm-drafted entries.** `Entry` records a list of sources but
   not which one the quote came from, so the loader credits the first usable one. The outpost
   definition is Wikipedia's text credited to **Philidor**. Correct for seeded entries only.


0. **RECORDED — what the arc cost and what it bought** → [[experiments.e88-arc-cost-and-result]]
   *(2026-09-06)*. Candidate count predicted within **12 %** (62,600 against **69,844** measured from
   cache growth); **wall clock 4× out** — ≈19 min estimated, **77 min actual**, because `prefetch`
   only covers positions that occur *in the games* and a candidate is a reply that was never played,
   so candidates run **serially** at ~15/s while game positions run 18-wide at 55/s. E85 flagged the
   borrowed throughput figure and I did not act on it. **The arc's honest headline: 21 claims
   withheld before and after.** It bought correctness, not discrimination, and the design said so.

0. **P1 — prefetch candidate positions.** Four times the wall clock of every future rebuild, for a
   change that batches positions the code already enumerates. The `detect_motifs` sweep that finds
   them is free; only the evaluation is serial.


0. **DONE — the P1 was a non-finding, and the screen behind it is the defect**
   → [[experiments.e83-spread-rescreen]]. The 1.13x was the **10 wp row**, and the shipped threshold
   is `INACCURACY_WP = 5.0`; on 83 players rather than E33's 12, `allowed_motif` runs 1.32–2.88x.
   **Underneath it: p90/median is bounded by 1/median**, so it scored rarity as discrimination
   (r = **−0.53**), and E09's accept/reject column is *perfectly rank-ordered by base rate*.
   Replaced with overdispersion against a binomial null (r = **+0.12**). **Ten shipped claims do not
   separate players even under the optimistic independent null**, nine of them asserted — including
   `allows_square.rook_seventh`, E09's second accepted candidate. `long_think_error`, the claim that
   raised the alarm, separates fine at **2.69x**.

0. **DONE — the nine claims stop comparing, and `allowed_motif` gets a real denominator**
   → [[design.claims-that-do-not-separate]] *(2026-09-05)*. **D1:** `peer_rate()` returns None for
   claims players do not differ on and `_unusualness` returns neutral, so they keep competing on
   cost — which stays personal even where the rate is not. No detector removed; the author's
   instruction was that nothing is retired. **D2 was built and then reverted the same day** —
   measuring `allowed_motif.X` over the errors where X was *available* left the engine's move choice
   as the only thing varying, and it is a regression → [[experiments.e84-band-references]]. Only D1
   survives from this entry.

0. **DONE — three rating bands, and D2 reverted** → [[experiments.e84-band-references]]
   *(2026-09-05)*. The band guard's block is answered by building **1200-1600, 1400-1800 and
   1600-2000** rather than one band, so a 1900 player is compared against 1600-2000 instead of a
   population below them — the failure recorded for `maikel5` and for the three strongest review
   players. **D2 was measured on the result and reverted:** same band and speed, it cost three claims
   their separation, left two unmeasurable, and improved none. `allowed_motif` is back on the
   total-errors denominator, so E83's verdicts stand as measured and the schema returns to v2.

0. **DONE — reference rebuilt, and the within-band screen moved twelve verdicts**
   → [[experiments.e84-band-references]] *(2026-09-05)*. Three bands × two speeds, 80 players,
   denominator A, schema v2. Screened **within band** — the stratum a peer lookup is actually keyed
   on — **twelve claims lost their separation and none recovered**, which is a systematic effect
   rather than noise. **Eleven of the twelve are genuinely flat** at smallest-visible-differences of
   1.04–1.30×; only `sacrificed_for_attack` is underpowered and is marked inconclusive.
   **The register grows from 10 entries to 21, 16 of them asserted**, and is now *generated* by
   `register.py` rather than hand-typed. 27 claims still separate; 5 are too thin to say and are not
   withheld, because unmeasured is not a verdict.


0. **DONE — Option 3 + severity ordering built** → [[design.punishment-validity]] *(2026-09-05)*.
   `allowed_motif` now counts any reply that executes the motif **and was worth playing** — within
   `INACCURACY_WP` of the opponent's best — not only their single best reply. **+20 % more punished
   errors found**, at **1.69 candidate evaluations per error**, validating E85's 1.52 estimate.
   Severity ranks punishments by the win probability they reach, so **mate outranks material without
   a table saying so** and no chess judgement needs a source. It also fixes cost double-counting: one
   blunder leaving three motifs available was charged three times, and now pays once.
   **Option 3's second condition was dropped as unfireable** — a position's evaluation already assumes
   best play (median gap **8 cp**), so requiring a candidate to gain over "the position as it stands"
   asked it to beat the best move. The intent was already enforced statically by the detectors.
   **Reference rebuilt and register regenerated** *(2026-09-06)*: three bands x two speeds, 80
   players, schema v3; `allowed_motif.fork` 274 -> **317 instances** in 1400-1800 blitz. The register
   is **21 claims again, one in and one out** — **`allowed_motif.pin` recovered and now separates**,
   `allowed_motif.trappedPiece` no longer does. Pin is the claim E85 measured at **49 % of the engine
   budget** and that the circular "skip the flat ones" saving would have dropped; it is the one that
   recovered. **Net zero on servable claims** — the rule is more correct and the count did not
   improve, which is the distinction between correctness and discrimination stated at the outset.

0. **SUPERSEDED — author decision: which punishment-validity rule?** → [[design.punishment-validity]]
   *(planned 2026-09-05, options only)*. A fork the opponent *could* play is not the player's fault
   if playing it would have lost for the opponent; and a fork need not be the engine's single best
   move to be a real punishment. Four options are written up with their holes stated —
   **ε-optimal window**, **aspiration floor**, **both (C′)**, and a **short PV window** for the
   check-then-fork case — plus a severity rule so mate is prioritised without discarding the fork.
   Recommendation is C′ + severity ordering, with the PV window deferred until measured.
   **The blocking measurement is done** → [[experiments.e85-candidate-cost]]: the free filter removes
   **93 %** of replies, leaving **1.52 evaluations per error position** — ≈31,300 for the blitz and
   rapid reference, **about ten minutes** at E01's measured throughput, a 20–40 % addition to a
   rebuild that already takes fifty. **Cost is no longer a reason to defer this.** `pin` is 49 % of
   the bill and `trappedPiece` 25 %; the obvious saving — skipping the claims that do not currently
   separate — is circular and is refused (L-051).

0. **DONE — § A, every detector audited** → [[experiments.e86-detector-audit]] *(2026-09-05)*.
   **The knowledge base could not serve as the reference**: 14 entries, none endorsed, and `fork`'s
   stored definition is a definition of a *skewer*; 11 claims have no entry. Audited against Lichess's
   own theme text instead — the keys the code already commits to. **Two defects demonstrated on
   positions:** `fork` misses a fork when a victim was already attacked by another piece (adding an
   attacker makes it stop seeing the fork), and `trappedPiece` reports a safe piece as trapped because
   escape squares use `is_attacked_by` rather than an exchange — the naive test D17 replaced
   everywhere else. Also: `hangingPawn` is **not** a Lichess theme, so the stated plan to validate
   against the CC0 puzzle database does not cover it; and four value floors have no source.
   **No detector changed** — author's instruction while the rebuild runs.

0. **DONE — tactical definitions seeded, gate fixed** → [[experiments.e87-seed-lichess-themes]]
   *(2026-09-05)*. **Eight motifs seeded verbatim from Lichess's own theme file** — the keys
   `tactics.py` already commits to — because the shelf has no definition to extract (E64 measured
   `skewer` at zero occurrences). **The gate now discriminates** rather than matching a word: it
   rejects **12 of 14** stored entries, keeping exactly the two that are genuine definitions, and it
   rejected the seeds until they named their own subject. `NAMES` separates a concept's synonyms from
   its search terms, which is what let "king safety" pass the rule about moving into check as a
   definition of castling. **Nothing endorsed** — all 17 entries `reviewed: False`.

0. **P1 — the nine non-tactical entries still fail the gate.** `allows_pressure`, `allows_square`,
   `endgame_error`, `late_castling`, `long_think_error`, `moved_into_attack`, `pawn_error`,
   `slow_development`, `hangingPawn`. For the pawn-structure concepts the classical shelf **does**
   discuss them, so re-extraction is the right instrument; the others may need Wikipedia the way the
   tactics needed Lichess. `moved_into_attack` holds no quote and zero sources.

0. **P2 — author call: `hangingPawn` has no external definition.** Not a Lichess theme, so it can be
   neither seeded nor validated against the puzzle database — the stated reason for using these keys.
   It exists because E31 found **all 45 reviewer notes mentioning a pawn unnameable** without it.
   Which gives way, the key or the claim, is the author's.

0. **SUPERSEDED — re-extract the knowledge base, and it needs no agent redesign**
   → [[design.knowledge-re-extraction]] *(2026-09-05)*. Every entry is stamped **2026-08-30**, the
   naming gate was tightened **2026-09-01**, and today's gate rejects **6 of 14 including `fork`** —
   whose stored skewer definition is *the documented case the gate was written to stop*. Three things
   are actually needed, none of them a redesign: **(a)** re-run; **(b)** one small change, making the
   gate *discriminating* rather than presence-based — five survivors pass on a single ordinary word
   (`allows_pressure` on "king", from a pawn-ending passage); **(c)** a **sourcing decision**, because
   for the tactical motifs the shelf has no definition to find — E64 measured `skewer` at **zero**
   occurrences, and the classical books predate the vocabulary. **Lichess's own theme definitions are
   free, precise, and already the keys the code uses**, so the tactical half can be seeded directly
   rather than extracted. Also: `moved_into_attack` is an entry with no quote and zero sources.

0. **P2 — the rest of the detector audit** → [[design.detector-audit]]
   *(planned 2026-09-05, not started)*. The author read the detection sheet and reports **most
   detectors are bad** (time claims skipped); the sheet also shows **28 of 57 claims never fire**.
   Three parts, in order: audit each detector's board logic against the **sourced** definition in the
   knowledge graph; make detectors name **the pieces involved and the move that would execute an
   unplayed motif** (*"the g3 pawn could fork the knights on h5 and f5 with g4"* — V8 directly); then
   a **local reviewer that triages**, flagging implausible detections for the author. The reviewer
   may never mark anything correct — R-03 forbids LLM chess judgement as a source, so a false
   "plausible" would silently retire a real defect while a false "suspicious" costs one position to
   read.

0. **P2 — re-screen once any of this lands.** Both designs change what `allowed_motif` counts, so the
   generated separation register must be regenerated after either — one command,
   `experiments/e84-band-references/register.py`, but it is not optional: the register is evidence
   and drifts the moment the measurement under it moves.

0. **STAGE 4 BUILT — prerequisites** → [[experiments.e81-prerequisites]] *(2026-09-02)*. The partial
   order in `domain.chess-concepts` § C is now **10 Domain nodes and 9 PREREQUISITE_OF edges**, each
   carrying its source. `gates(a, b)` answers **True, False or None**, and across all 420 claim pairs
   **89 % are unknown** — which is the design note's own definition of done, not a shortfall. 16
   claim kinds mapped, **5 deliberately unmapped with the reason stored**.

0. **P1 — the arbiter still does not rank on prerequisites.** Stage 4's done-condition was that it
   *can ask*. Making the order actually reorder a plan is a coaching judgement rather than a wiring
   job, and only **24 of 420 pairs** answer yes, so as a ranking signal it is currently very thin.

0. **P2 — no shipped claim is K3, K5 or K10.** Calculation, planning and meta-learning have no
   detector, so most of § C's order is unreachable by anything the swarm measures. Worth knowing
   before the order is trusted to rank.


0. **THE COACH ANSWERS QUESTIONS** → [[experiments.e80-answering]] *(2026-09-01)*. `chesscoach ask
   "what is a backward pawn?"` returns a definition attributed to **Lasker, Philidor and Staunton**
   with three `book://` locators; *"how does a knight move?"* comes from the generated rule;
   *"why is the Sveshnikov Sicilian good?"* is **refused, citing nothing**. This is the goal the graph
   was built for and it closes stages 1-3 into something usable.

0. **DONE — the answer path corroborates** *(2026-09-02)*. Retrieved passages become
   Attestations and E79's rule decides: independent lineages agreeing in their own words, not
   distinct authors counted. Several books that do not agree closely now say so to the reader.

0. **P2 — which source the model actually used is not knowable.** Citations are what was put in front
   of it. Honest, and weaker than "this sentence came from that passage".


0. **STAGE 3 BUILT — extraction and corroboration** → [[experiments.e79-corroboration]]
   *(2026-09-01)*. 7 books, **6 independent lineages**, 1,159 passages. **16 concepts of 19 reach two
   independent voices**; the 3 refused — `skewer` (0 passages), `trappedPiece`, `hangingPiece` — are
   exactly the modern tactical vocabulary E64 predicted a pre-1929 shelf would lack. A first run
   reported **19 of 19 at every threshold** because the method was circular: retrieve for similarity,
   then measure similarity. The sweep is what exposed it.

0. **FIXED — the agreement half now discriminates** → [[experiments.e79-corroboration]]. Measured
   between the **sentences that name the concept** rather than whole passages: 15 servable at 0.50,
   14 at 0.60, 13 at 0.65, **8 at 0.80**, where before it was flat. `backRankMate` was a visible
   false positive — Philidor on piece values and Staunton on the opening setup, agreeing only on the
   word **"rank"** — fixed by treating rank and file as board furniture, like "square" already was.

0. **P1 — where the agreement threshold belongs is the author's judgement.**
   `experiments/e79-corroboration/results/agreement-sample.txt` holds the pairs: two sentences from
   two authors that the rule counted as agreeing. Mark them and the threshold follows from the marks
   rather than from my taste.

0. **P1 — the model judge refuses nothing.** `qwen3:8b`, given an explicit criterion and a refusal
   option, kept **15 of 15** passages, including one about "services rendered his countrymen" as an
   explanation of castling. E63 spent two prompt attempts on the same judgement; this run supplied
   the criterion E63 said was missing and the answer did not change. **A deterministic vocabulary
   gate does all the discrimination.** Worth writing up as a thesis result about small models as
   relevance judges.


0. **STAGE 1 BUILT — the graph knowledge base** → [[design.graph-knowledge-base]]
   *(2026-09-01)*. Neo4j 5.26.30 Community in a container, `docker-compose.yml` at the root with
   memory capped for a laptop that also hosts an 8B model. **The rules layer is loaded and queryable**:
   6 movement rules generated from `python-chess`, 6 outcome rules citing the predicate that
   implements each, 5 Lichess speeds read from `speed.py`. **Nothing authored, so nothing to endorse.**
   `python -m chesscoach.cli build-graph --reset`. Vector indexes verified working, so the
   single-store design holds.

0. **STAGE 2 BUILT — passages, vectors and the ablation** → [[experiments.e77-retrieval-ablation]].
   **607 passages** from three books embedded through `mxbai-embed-large` and stored with a vector
   index, in 96 s. **8 of 8 grounded answers cite a real locator; none invents one.** The clearest
   case: asked what counts as rapid, `phi4-mini:3.8b` alone gives a fluent, confident, platform-wrong
   answer; with retrieval it gives Lichess's actual rule and cites the node generated from the code
   that makes the classification. **The failure mode of a small model is confident generic
   plausibility, and that is what retrieval fixes.**

0. **RESOLVED — the shelf is seven books.** Gutendex stayed down but gutenberg.org's own search
   was up, so Bird, Philidor, Young and a second Edward Lasker were added: **6 independent lineages,
   1,159 passages.** This entry said three books for a day after that stopped being true.

0. **DONE — chunking follows paragraphs** → [[experiments.e78-rechunk]]. Passages starting
   mid-sentence fell from **165 of 544 to 11 of 529**, and *"why should I castle early"* stopped
   returning a passage about giving odds. **The books turned out to be double-spaced** — a wrapped
   line ends with two newlines and a paragraph with four — so splitting on a blank line cut every
   line and did nothing; the wrap is now detected rather than assumed. 28 stored citations
   re-anchored, 3 already correct, 1 straddles a new boundary and is reported rather than guessed at.

0. **P2 — overlapping passage windows.** Would have avoided the one straddled quote and are standard
   in retrieval; not done because they move locator semantics again and one case in fourteen did not
   justify it. Revisit if extraction produces many more.

0. **P2 — the books are in descriptive notation** (`P-K4`, `Kt-KB3`), which the embedder has little
   reason to relate to a question asked in modern terms. Measured as a weakness, not yet addressed.

0. **P0 — the peer corpus is 26 % out of band** *(new 2026-09-01)*. `declared_band_is_wrong` refuses
   **36 of 137** corpus players against 1400-1800 — 21 of 72 rapid, 15 of 65 blitz. Every peer
   baseline in the system is computed from that population, so the contamination E70 found on the
   *read* side is also in the reference itself. Rebuilding is blocked by the guard until the corpus is
   filtered, and filtering drops the reference from 137 players to 101, which is a judgement about the
   corpus rather than a maintenance task.

0. **DONE — five claims were invisible on the detection sheet** (I-09). A working-directory-relative
   book path silenced every claim that needs the opening book, so the four development claims and
   `out_of_book` never appeared on any sheet. Fixed, 3 tests; the sheet's vocabulary goes **50 → 57**.

0. **DONE — four shipped claims had a baseline nothing could find** (I-10). The peer reference spells
   the development claims `kind.subject` and everything else `kind.subject.own`; `20b1cef` normalised
   the section side and left the stored artefact behind. `PeerReference.canonical` now applies on write
   and on load. `late_castling` and `pawn_error` reach plans again; `slow_development` and
   `repeat_move` correctly stay quiet, because the players measured are better than the population.

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

0. **DONE — `slow_development` against `plies_in_book`** → [[experiments.e75-book-depth]]. The last
   unrun pair from E69's screen. Book depth is **reliable** (split-half **+0.81** over 84 players),
   **distinct** (−0.47 against `slow_development`, far under the 0.85 ceiling) and **not merely
   rating** (+0.37). **It survives — and redundancy was never the argument against 1a**, so this
   reopens the question rather than settling it: actionability and cost still favour the development
   signals, and the median player leaves theory after **5.3 plies, under move 3**.

0. **DONE — 1a is built** → [[experiments.e76-leaving-theory]]. The author settled it: *"It is
   coaching to tell the player that they don't know the opening"*. `chesscoach/book_depth.py`,
   15 tests, wired into S4, **measured for 7 of 12** review players and reaching one plan. The measure
   is the **share of early moves played outside theory** (reliable at **+0.83**) rather than a
   threshold on when theory ended (**+0.65** at its best). Its baseline is
   `data/openings/book-depth-norms.json` — rapid 43.5 %, blitz 50.0 % — kept out of the peer reference
   because book depth needs no engine.

0. **P1 — one number per band and speed is coarse for openings.** The baseline does not vary by
   opening, and a Najdorf player and a London player do not face the same book. Per-opening baselines
   are the obvious refinement and would reuse `development-norms.json`'s per-opening shape.

0. **P1 — the one player the claim reaches is the one whose baseline is most suspect.** cademan is
   1302 against a 1400-1800 baseline ([[experiments.e70-band-mismatch]]), so their 59 % against 46 %
   is partly the band mismatch. Worth re-reading once the read-side band decision is made.

0. **DONE — E31 and E44 re-run, and a third experiment was stale**
   → [[experiments.e82-move-number-rerun]]. `ply // 2 + 1` had been **copied into five files** and
   fixed in none; three of them joined the reviewer's own noted move numbers, not the two this entry
   named. **E44: 34 % → 29 % instant, and its one counterexample disappears** — cademan 1.25× → 0.77×,
   so every player is now below 1 and the note's conclusion is stronger than it could state.
   **E31: `bjagus` 80 %/10 % → 100 %/60 %**, but across six players 76 %/37 % against 76 %/35 % — the
   aggregate barely moves while the per-player numbers move both ways, because the off-by-one
   *shuffled* which notes matched rather than inflating them.

0. **DONE — `build_resource` is wired into the report.** A new section, *THE OPENING YOU PLAY*,
   showing the main line and the variants the player actually reaches with their own game counts.
   It is **separate from the approved brief and needs no approval**: the moves are CC0 reference data,
   so a player whose opening nobody has curated now gets something true about it, where before the
   section was empty. Plans still appear only with a reviewed guide to attribute them to.

0. **Found by wiring it — the "main line" could be a sideline.** `_pick_main_line` walked the
   Scandinavian to **`1. e4 d5 2. b3`**, because those are the only two rows the book names plainly
   "Scandinavian Defense" and one ply apart does not trip the big-jump guard. Correct-looking and
   unread since it was written; the moment it reaches a player it is this project printing a chess
   opinion nobody holds. Fixed by a measurement rather than taste — **a main line must be a prefix of
   at least one named subline**: `2. b3` continues into 0, `1. e4 d5` into 43, the Italian's `3. Bc4`
   into 177.

0. **Three more relative default paths fixed** (I-09's family): `guides.json`, `runs.db` and
   `skiplist.json` were all resolved against the working directory. Same class as the book path that
   had been silencing five claims.

0. **DONE — the precise `rook_seventh` rule** → [[experiments.e74-rook-seventh-precise]]. The two-ply
   search is written, wired into `squares.allowed` and measured over 72 players and 764 arrivals: it
   removes **29 % of what the cheap screen let through**, at **1.2 ms a search**, running only on
   arrivals that survived the screen. The claim now fires on **40 %** of arrivals where it once fired
   on all of them. 9 tests, and one fixture I was certain of turned out not to be checkmate.

0. **P1 — twelve `rook_seventh` positions to mark** *(author)*.
   `experiments/e74-rook-seventh-precise/results/removed-sample.txt` — positions the search newly
   **removes**, as FENs. E66 recorded that neither correction had been read against positions; this is
   the half that can be. The question is the author's own: *was there a real opportunity to block the
   rook?*

0. **P2 — should an arrival that loses the rook count as preventable?** The search asks whether the
   arrival was **possible**, not whether it was **good**: a rook that can only reach the seventh by
   being captured there is still called unpreventable. A practical reading would remove more, and
   deciding it needs an engine inside a section, which C1 does not allow. Recorded rather than
   settled.

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
