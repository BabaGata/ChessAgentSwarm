---
id: cas-domain-signals
title: Computable Signals & Free Tooling
desc: 'What can be extracted automatically from a player games, with which free tools, and what cannot.'
updated: 1785254500000
created: 1785254500000
---

# Computable Signals & Free Tooling

First-pass answer to questions 11–13 of [[mission.step-01-foundations]]. This note decides how much
of the coaching diagnosis can be done by **deterministic computation** rather than by LLM calls —
which is the single biggest lever on constraint C1 (free/near-free).

## 1. Free tooling inventory

| Tool | What it gives | Cost | Notes |
|---|---|---|---|
| **Stockfish** | position evaluation, best move, multi-PV | free, local, CPU | the workhorse; depth/time is the tunable cost knob |
| **python-chess** | PGN parsing, board logic, UCI engine driver | free | the standard glue library |
| **Lichess API** (`lichess.org/api`) | user games as PGN/NDJSON, ratings, with `evals`, `accuracy`, `opening`, `division` (phase markers) parameters | free | rate-limited; back off a full minute on HTTP 429 |
| **Lichess cloud eval** | evaluations of already-analysed positions | free | avoids local compute for common positions |
| **Lichess open database** (`database.lichess.org`) | bulk games; **puzzle CSV** with `PuzzleId, FEN, Moves, Rating, RatingDeviation, Popularity, NbPlays, Themes, GameUrl, OpeningTags` | free, **CC0** | zstd-compressed; themes are machine-generated tags |
| **Lichess opening explorer** | move frequencies and results by position/rating band | free | for repertoire and deviation analysis |
| **Chess.com public API** | games for chess.com users | free, read-only | needed since many players are there |

**Key finding: the Lichess puzzle database is CC0 and carries motif theme tags.** That gives a free,
large, labelled dataset that maps directly onto the K2 motif vocabulary in
[[domain.chess-concepts]] — usable both as training material to prescribe and as a labelled corpus
for building/validating a motif classifier. This is the most valuable single asset found in M1.

## 2. Signals computable per game / per player

### Error signals (engine-derived)
- Centipawn loss per move → **ACPL**, and the distribution (mean hides everything)
- Counts of inaccuracy / mistake / blunder; accuracy %
- **Phase-wise error profile** — opening / middlegame / endgame (Lichess `division` markers, or a
  computed phase heuristic)
- Eval-swing turning point per game: the move where the game was actually decided
- Winning-position conversion rate (games reaching ≥ +2 that were not won)
- Losing-position resilience (games saved from ≤ −2)

### Pattern signals (the diagnostically valuable ones)
- **Missed tactics**: positions where a forcing win existed and was not played. This is exactly the
  logic Lichess uses to *generate* puzzles from analysed games — so it is a proven, reproducible
  technique on free tooling.
- **Motif classification of errors**: what the refutation actually used (fork, pin, back rank,
  deflection…). This turns "you blunder" into "you miss knight forks against your queen" — the level
  of specificity a coach operates at.
- Which piece is hung most often; from which squares; in which structures
- Opponent-threat blindness: errors where the opponent's *previous* move created the threat that was
  ignored (a K9 process-gap signature, not a knowledge gap)

### Process signals (clock-derived; needs `%clk` in PGN)
- Time per move; instant moves in critical positions; time-trouble frequency
- Error rate as a function of remaining time → separates skill gaps from time-pressure gaps
- Long-think-then-bad-move (the Kotov-syndrome signature)

### Repertoire signals
- ECO/opening frequency, score per opening, move at which the player leaves book
- Structures actually reached, and score by structure
- How often the player is punished before move 15 (tests the "openings don't matter" claim
  *for this player* rather than asserting it — see [[domain.chess-concepts]] § E)

### Style signals (for V3, operationalised)
- Early queen-trade rate; castling side; opposite-side castling frequency
- Sacrifice rate; average material imbalance; pawn-storm frequency
- Average position sharpness (e.g. spread between best and 3rd-best engine move, or count of
  non-losing moves) — a proxy for how forcing the positions they enter are
- Open vs. closed structures reached; average game length; endgame frequency
- **Performance split by all of the above** — tendency and performance are different things, and the
  useful recommendation lives in the gap between them

## 3. What is NOT computable from games

These require **asking the player** or **probing** them, and this is the boundary that determines
the swarm's interaction design:

| Not computable | Why | Possible mechanism |
|---|---|---|
| Knowledge vs. luck | a correct move may be played for the wrong reason | **probe positions**: show a position, ask for the move *and the reason* |
| Knowledge gap vs. skill gap | absence of correct play is weak evidence of ignorance | probe under no time pressure; if they find it slowly, it is a skill/time gap, not knowledge |
| Whether a concept is *understood* | pattern-matching can imitate understanding | ask for the plan in a typical structure, not the move |
| Goals, available study time, motivation | not in the data | ask directly |
| Psychological state, tilt causes | only weak proxies (result streaks, clock) | ask + corroborate with proxies |
| Over-the-board vs. online differences | different data source entirely | ask |

**Design consequence:** the swarm needs an *active assessment* capability (probe positions), not only
passive game analysis. This is a real addition to the architecture and was not obvious before M1 —
it feeds V2 (knowledge assessment) and V4 (gap detection) far better than game analysis alone.
Recorded as a lesson in [[learning.lessons]].

## 4. Methodological warnings

These are the ways an automated chess-diagnosis system produces confident nonsense:

1. **ACPL is not comparable across positions or time controls.** Sharp positions produce higher
   centipawn loss for equal skill; bullet and classical are different games. Always segment by time
   control, and prefer within-player comparisons over cross-player ones.
2. **Sample size.** "You blunder in rook endings" from three rook endings is noise. Every diagnosis
   needs a minimum-sample rule and a confidence statement.
3. **Engine depth changes the labels — measured, not theoretical.** [[experiments.e01-engine-throughput]]
   found depth 15 and depth 18 agreeing on only 73.6 % of error labels and 83.7 % of blunders
   (depth 12: 61.3 % / 69.2 %). Consequences: **store the analysis depth with every derived signal**,
   never merge profiles built at different depths, and never present a single move's label as a bare
   fact — only aggregates survive (L-006).
4. **Opponent strength confound.** Error rates rise against stronger opponents; rating-adjust before
   claiming a trend.
5. **Selection bias in "recent games".** A losing streak of blitz games is not a representative
   sample of the player's chess.
6. **Correlation is not causation for improvement claims.** The system may state "these are your most
   frequent error types"; it may not state "fixing this will gain you 200 points" without evidence.

## 5. Consequence for the cost architecture (C1)

Practically everything in § 2 is **deterministic computation** — engine + parsing + statistics — with
zero marginal cash cost. The LLM is then needed only for:

- explaining findings in natural language,
- conducting the probe dialogue and interpreting free-text answers,
- planning the coaching path from a structured diagnosis,
- and possibly classifying positional (non-tactical) features, where no labelled dataset exists.

This is a strong argument for an architecture where **agents compute first and speak last**: a
deterministic analysis core producing a structured player profile, with language models operating on
the *summary* rather than on the raw games. That keeps token volume roughly constant per player
instead of scaling with the number of moves analysed. → to be recorded as an ADR in M3.

## Open items

- Verify current Lichess API parameter names/limits against the live docs before implementing.
- Measure: how long does Stockfish analysis of 50 games take on the target laptop, at what depth?
  This number sets the whole system's feasibility and is currently unknown.
- Determine whether a positional-motif classifier is feasible at all without labelled data (the main
  asymmetry: tactics are machine-labelled, strategy is not).
- Check the Lichess puzzle-generation methodology in detail — it is effectively the reference
  implementation of "find the missed tactic".
