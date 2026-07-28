---
id: cas-domain-sources
title: Sources
desc: 'Sources used for the domain knowledge, each with an evidence-quality note.'
updated: 1785254500000
created: 1785254500000
---

# Sources

Every source used in [[domain.chess-concepts]], [[domain.coaching]] and [[domain.signals]], with an
honest note on its quality. Evidence classes per [[capacity.knowledge]]:
`measured` · `expert-consensus` · `single-expert` · `folklore`.

**Caveat on this pass:** M1's first research pass used web search over publicly available chess
sites. That is adequate for mapping the *landscape* and for tooling facts, but much of it is
commercial content marketing of variable rigour. Before anything from here appears in the thesis as
a claim about chess pedagogy, it needs corroboration from primary sources (books by recognised
coaches, peer-reviewed work). Flagged as an open item in [[state]].

## Chess improvement / curriculum by level

| Source | Used for | Class | Quality note |
|---|---|---|---|
| [TheChessWorld — study plan by rating level](https://thechessworld.com/articles/chess-how-tos/how-to-get-better-at-chess-study-plan-for-different-rating-levels/) | band table, study-time allocation | expert-consensus | coach-authored site; consistent with other sources |
| [ChessMood — roadmaps 1500–2000 and 2000+](https://chessmood.com/chess-study-plans/for-advanced-players) | higher-band priorities | expert-consensus | GM-run platform; commercial interest in opening courses — note the bias |
| [Chess.com — WGM Dina Belenkaya, 1000–1400 study guide](https://www.chess.com/article/view/wgm-dina-belenkayas-beginner-intermediate-study-guide-1000-1400-elo) | low-band priorities, motif list | single-expert | titled author, clearly attributed |
| [BetterChess — what actually moves your rating (2026)](https://betterchess.co/guides/chess-improvement-tools) | band framing ("blunder-reduction band", personalisation at 1400–1800) | single-expert | useful framing; commercial site |
| [RagChess — improvement guide by rating (under 2000)](https://www.ragchess.com/chess-improvement-guide-based-on-your-rating/) | corroboration of band advice | folklore→expert-consensus | unattributed authorship |
| [Chess.com forum — structured learning 1000→1800](https://www.chess.com/forum/view/for-beginners/structured-learning-1000-to-1800) | Steps Method structure (tactics-dominant early levels) | expert-consensus | forum, but describes a real published curriculum (Steps Method) worth acquiring directly |

## Coaching practice

| Source | Used for | Class | Quality note |
|---|---|---|---|
| [ChessWorld — what a chess coach does](https://www.chessworld.net/chessclubs/openingguide/chess-coach-role.asp) | assessment shape, "analyse your games", repetition over spectacle | expert-consensus | consistent across the site's coaching pages |
| [ChessWorld — lesson structure adviser](https://www.chessworld.net/chessclubs/openingguide/chess-lesson-structure.asp) | one diagnosis + one idea + one next step | expert-consensus | |
| [ChessWorld — how to coach chess](https://www.chessworld.net/chessclubs/openingguide/coach-and-trainer-guide.asp) | one-or-two priorities, weekly plan, checkpoints | expert-consensus | |
| [Chessverse — personalised coaching](https://www.chessverse.in/blog/personalized-chess-coaching-tailoring-lessons-per-student) | "first month spent diagnosing what the player doesn't know they don't know" | single-expert | coaching-software vendor; the observation is nonetheless load-bearing for V7 |
| [ChessWorld — playing styles guide](https://www.chessworld.net/chessclubs/openingguide/chess-playing-styles-guide.asp) | four style types, "practical grouping not an official rule" | folklore | style taxonomies are weakly evidenced — treated accordingly in [[domain.coaching]] § 6 |

## Chess content (concepts)

| Source | Used for | Class | Quality note |
|---|---|---|---|
| [ChessWorld — strategic & positional concepts](https://www.chessworld.net/chessclubs/openingguide/strategicconcepts.asp) | K4 concept inventory | expert-consensus | standard, uncontroversial material |
| [ChessWorld — middlegame principles](https://www.chessworld.net/chessclubs/openingguide/top50chessmiddlegameprinciples.asp) | prophylaxis, activity, harmony, structure | expert-consensus | |
| [AttackingChess — 100 middlegame principles](https://www.attackingchess.com/100-chess-middlegame-principles-and-strategies-every-player-should-know/) | corroboration | folklore | listicle; used only where it agrees with better sources |
| [ChessWorld — Kotov candidate moves](https://www.chessworld.net/chessclubs/kotovcandidatemoves.asp) | K3 calculation, candidate-move method, Kotov syndrome | single-expert | Kotov's method is itself contested — see [[domain.chess-concepts]] § E |
| [Wikipedia — candidate move](https://en.wikipedia.org/wiki/Candidate_move) | definition, de Groot vs. Kotov contrast | expert-consensus | |
| [Old School Chess — king and pawn endgames](https://oldschoolchess.com/learn/endgames/king-and-pawn-endgames) | K7 opposition, key squares, rule of the square | expert-consensus | standard theory |
| [Chess.com — basic rook endgames: Philidor and Lucena](https://www.chess.com/blog/vinniethepooh/basic-rook-endgames-philidor-and-lucena) | rook-ending priority, "50% of games reach rook endings" | expert-consensus | the 50% figure is widely repeated and **not verified** — mark as unverified if used |
| [ChessWorld — endgames trainer](https://www.chessworld.net/chess-endgames.asp) | endgame learning order | expert-consensus | |

## Cognitive science of chess expertise

| Source | Used for | Class | Quality note |
|---|---|---|---|
| [Gobet & Simon — Expert chess memory: revisiting the chunking hypothesis (PubMed)](https://pubmed.ncbi.nlm.nih.gov/9709441/) | chunking, pattern-based expertise | **measured** | peer-reviewed; the strongest evidence in this list |
| [Gobet — Chunking models of expertise: implications for education](https://onlinelibrary.wiley.com/doi/abs/10.1002/acp.1110) | why repetition-to-automaticity beats novelty | **measured** | peer-reviewed |
| [Gobet — Expert memory: a comparison of four theories (PDF)](https://cognitivearchaeologyblog.wordpress.com/wp-content/uploads/2015/11/1996-gobet.pdf) | theory background | measured | |
| [Chess.com — the cognitive psychology of chess](https://www.chess.com/article/view/the-cognitive-psychology-of-chess) | popular summary, deliberate-practice/starting-age findings | secondary | **used only as a pointer**; the underlying papers must be cited directly in the thesis |

| [Hambrick, Oswald, Altmann, Meinz, Gobet & Campitelli (2014), *Deliberate practice: Is that all it takes to become an expert?*, Intelligence 45, 34–45](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4101876/) | the deliberate-practice variance figure | **measured** | **D1 resolved 2026-07-28.** Deliberate practice accounts for about **one third of the reliable variance** in chess. Restricted to chess and music, the two domains with well-documented training activities. Note the wording: *reliable* variance, not total — check the exact phrasing against the PDF before quoting it in the thesis |
| [Macnamara, Hambrick & Oswald (2014), *Psychological Science*](https://journals.sagepub.com/doi/abs/10.1177/0956797614535810) | broader meta-analysis across domains | **measured** | corroborates the order of magnitude for games |

> **Resolved 2026-07-28 (D1).** The deliberate-practice figure was previously cited from memory. It
> is now attributed: ~one third of *reliable* variance in chess, from Hambrick et al. (2014). The
> honest statement for the thesis is that practice matters enormously **and** explains a minority of
> the differences between players — which is exactly why a coaching system must not promise rating
> gains it cannot evidence.

## Tooling & data

| Source | Used for | Class | Quality note |
|---|---|---|---|
| [lichess.org open database](https://database.lichess.org/) | puzzle CSV schema, CC0 licence, bulk games | **documentation** | authoritative |
| [Lichess API tips](https://lichess.org/page/api-tips) | rate limits, HTTP 429 back-off | documentation | authoritative |
| [Lichess game export & streaming (DeepWiki mirror)](https://deepwiki.com/lichess-org/api/5.3-game-export-and-streaming) | export parameters: `evals`, `accuracy`, `opening`, `division` | secondary documentation | third-party mirror — **verify against `lichess.org/api` before implementing** |
| [Pulling puzzles from Lichess — G. Marlow](https://mgmarlow.com/words/2025-02-03-pulling-puzzles-from-lichess/) | practical puzzle-DB handling | secondary | worked example |
| [FireChess — centipawn loss explained](https://www.firechess.com/blog/what-is-centipawn-loss) | ACPL definition | expert-consensus | |
| [Centipawn loss / Elo correlation analysis](https://medium.com/@enzo.leon/data-science-and-chess-centipawn-loss-elo-correlation-e06089efd8b8) | ACPL–rating relationship, its limits | single-analysis | one blog analysis; treat as a hypothesis to reproduce, not a result |
| [ianfab/chess-analysis](https://github.com/ianfab/chess-analysis) | quality-of-play metrics implementation | code | candidate for reuse |

## Prior art — existing LLM chess coaches (research & reuse)

Reviewed for the reuse-before-building rule. None of these is an adaptive multi-agent coach with
persistent player modelling, which is where this project's contribution sits — but each is worth
reading before building the equivalent component.

| Project | What it does | Relevance |
|---|---|---|
| [bleongcw/Arrakis_Engine](https://github.com/bleongcw/Arrakis_Engine) | Stockfish + LLM coaching with tactical-motif detection, time-pressure analysis, **recurring weakness escalation across games** | closest prior art to the diagnosis layer; read first |
| [Iamsdt/chess](https://github.com/Iamsdt/chess) | browser trainer, Stockfish + LLM explanations, puzzles, openings, endgames | UI/interaction reference |
| [renaissancebro/stockfish-coach](https://github.com/renaissancebro/stockfish-coach) | interactive position chat over engine lines | explanation-layer reference |
| [ai-chess-training/LLM-ChessCoach](https://github.com/ai-chess-training/LLM-ChessCoach) | analyses existing games, move-by-move commentary | pipeline reference |
| [akmenon1996/LLM-ChessCoach](https://github.com/akmenon1996/LLM-ChessCoach) | loads games from a chess site, feeds an LLM | minimal baseline |
| [official-stockfish/Stockfish wiki](https://github.com/official-stockfish/Stockfish/wiki/) | engine documentation | required reading before engine integration |

**Not yet done:** actually reading these repositories (licences, architecture, what to port). Queued
as the first action of the next cycle.
