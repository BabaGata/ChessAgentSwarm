---
id: cas-exp-e92
title: 'E92 — A local model in the session: the check passes what a reader catches'
desc: 'Three ways of giving qwen2.5:3b the findings. The automatic check kept 18/20, 56/59 and 41/59; reading eight by hand found 3, several and 1 misstatements. Concept questions answered from the report came out wrong, so they are routed to the books. Practice positions work once moves are read on the board.'
updated: 1789862400000
created: 1789862400000
---

# E92 — A local model in the coaching session

**Answers:** the author's request to have the model write the results, take follow-up questions and
use the prober at the end ([[design.narrated-session]]) · **Code:** `chesscoach/narrator.py`,
`followup.py`, `exercise.py`, `after_report.py`; `experiments/e92-narrated-session/` ·
**Date:** 2026-09-19 · **Status:** done — **adopted, with the residue stated**

## Setup

20 in-sample rapid players (`data/raw/corpus-rapid`, band 1400–1800, peers E84), profiles built by
`coach` itself. Model `qwen2.5:3b` (E50's choice), temperature 0.2, local Ollama. The first full
run was killed by the system for low memory half way (Ollama, Neo4j, Stockfish and Word together);
the script now saves after every player and resumes.

## Summary — three ways of giving the model the facts

| input | kept by the check | hand-read (8 players) | per report |
|---|--:|---|--:|
| whole report | 18 / 20 reports | **5 correct, 3 wrong**: a cost moved to another finding; the rating caveat pinned on a finding; *missed* for *conceded* | 4–10 s |
| one finding's block of report text | 56 / 59 findings | cross-finding mixing gone; "64 % of the time" read as **"64 % of the games"**; labels copied ("Target:", "Below 3 % …") | 8 s |
| **one fact sheet per finding** (shipped) | **41 / 59 findings, 20 / 20 reports** | **6 correct, 1 embellished, 1 wrong**: *more often than your level* became *less often* | **8.3 s** |

The fact sheet is plain sentences built from the measurement ("This happened in 64 % of the times it
could have happened"), so the share is said in words. Shorter sources raise novelty, so more
sentences are rejected (18 of 59, almost all on novelty) — a finding whose sentence is rejected is
left out of the summary, never replaced.

**What no version fixes: a sentence made of the source's own numbers and words that reverses a
relation.** `grounding`'s docstring already names this residue for opening plans; E92 measured it in
the summary at 1 in 8 players on the shipped arm.

## Follow-up questions (6 players × 3 questions)

| question | answered from |
|---|---|
| *Why is my first weakness a problem for me?* | report 5, refused 1 (novelty 50 %) |
| *What should I practise first?* | report 6 |
| *What is a pin?* | books 6 |

Median 3.7 s, worst 18 s (first call loading the book model). **The first single-player run
answered "What is a pin?" from the report with a wrong definition, and it passed at 42 % novelty —
the same as a correct answer about the report (43 %).** Concept questions are therefore routed by
pattern (English and Croatian) and never reach the report path. The book answer itself is circular
("a tactic involving pins, where…") — that is `answering` and its shelf, unchanged here. In the
recorded demo a report answer again turned "44 % of the time" into "44 % of the games".

## Practice positions (the prober, as practice)

33 positions for 20 players; 19 of 20 get at least one. **Moves are stored as UCI (`c8g4`)** and the
report prints SAN, so the first version would have marked a player typing `Bg4` as wrong. Answers are
now read on the board (SAN, UCI and a lower-case piece letter all count) and the position is printed
as a board from the side to move. Nothing about the finding changes (D10 still open).

## Verdict

Adopted: the summary is labelled as the model's, checked against its own facts, and followed by the
full report; the questions are routed so that chess knowledge only comes from the books; the
practice is deterministic. **Not claimed:** that the summary is correct — the check guarantees no
invented number, move or unfamiliar vocabulary, and one reversed relation in eight got through.
