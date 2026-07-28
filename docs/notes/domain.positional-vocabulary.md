---
id: cas-domain-positional
title: Positional Vocabulary
desc: 'The positional concept catalogue from the free primary literature, each rated for machine detectability.'
updated: 1785255500000
created: 1785255500000
---

# Positional Vocabulary

The strategic counterpart to [[domain.puzzle-themes]]. Tactics arrive pre-labelled from a CC0
dataset; strategy does not, so this note assembles the vocabulary from the free primary literature
(constraint C7, [[decisions.0004-free-research-materials]]) and rates each concept for **machine
detectability**, using what E02 actually established.

Feeds M2 directly: these are the candidate positional sections.

## Sources

| Source | Availability | Status |
|---|---|---|
| Nimzowitsch, *My System* (1925–27) | archive.org; a structured free version exists as a [Lichess study](https://lichess.org/study/D8ZjNNQt/9ObmpRZm) | **Part-1 structure verified**; Part-2 chapter list recalled, not yet verified against the text |
| Capablanca, *Chess Fundamentals* (1921) | [Project Gutenberg #33870](https://www.gutenberg.org/ebooks/33870), held in `docs/pdf/` | read for structure and study order |
| Silman's imbalances | via secondary sources | `expert-consensus`, widely used framing |

*My System* is organised in three parts: **The Elements**, **Positional Play**, and illustrative
games. The Elements are the ones Nimzowitsch treats as the irreducible units of strategy — which is
exactly the decomposition M2 needs.

## The catalogue

**Detectability** ratings come from [[experiments.e02-positional-detectors]], which showed geometric
properties are cheap to compute while relational/intentional ones are not:

- **Proven** — a detector exists and was hand-verified
- **Straightforward** — same geometric character; expected to work with the same technique
- **Hard** — needs engine support or a definition that does not reduce to board geometry
- **Open** — no credible mechanical definition yet

### Nimzowitsch's Elements *(structure verified)*

| Concept | Detectability | Note |
|---|---|---|
| The centre | straightforward | occupation and control are countable; *centre type* (open/closed/fixed) is a classifiable structure |
| Open files | **proven** (E02) | including the semi-open distinction; base rate is very high, so presence alone is not a signal |
| Seventh and eighth ranks | straightforward | rook/queen on the 7th is a trivial geometric test |
| Passed pawns | straightforward | classic definition, purely geometric; protected/outside/connected variants also computable |
| The pin | **proven — already a tactical tag** | overlaps [[domain.puzzle-themes]]; Nimzowitsch treats it as strategic, which is a useful reminder that the tactics/strategy split is our convenience, not the game's |
| Discovered check | proven (tactical tag) | same overlap |
| Exchanging | hard | the *decision* to exchange is intentional; the act is countable, its correctness is not |
| The pawn chain | straightforward | chain identification is geometric; identifying the correct *base to attack* needs judgement |

### Positional Play *(chapter list recalled — verify against the text)*

| Concept | Detectability | Note |
|---|---|---|
| Prophylaxis | **hard** | requires knowing the opponent's intention and whether it was prevented. Engine-assisted approximation: did the move reduce the opponent's best available gain? |
| Overprotection | open | counting defenders of a key square is easy; identifying *which* square is strategically key is not |
| Isolated queen's pawn | **proven** (E02) | present in a very high share of positions; the coaching content is which *side* of it the player is on and whether they play it correctly |
| Hanging pawns | straightforward | two adjacent friendly pawns with no neighbours; geometric |
| Weak squares / holes | straightforward | squares no enemy pawn can ever cover — the same computation as the outpost detector's condition 3 |
| Outposts | **proven** (E02) | base rate 7 %, usably informative |
| Backward pawns | **proven** (E02) | base rate 21 %, the best-behaved of the four tested |
| Doubled pawns | straightforward | trivially geometric |
| The two bishops | straightforward | material configuration; its *value* depends on structure openness, itself computable |
| Good vs. bad bishop | straightforward | count own pawns on the bishop's colour complex |
| Restraint / blockade | hard | blockading piece in front of a passed pawn is geometric; "restraint" as a plan is not |
| Piece activity / worst-placed piece | hard | needs a mobility metric or engine support; no crisp definition |
| Piece harmony, coordination | open | no mechanical definition; likely needs the language layer, if it can be done at all |

## What this tells M2

1. **Roughly two thirds of the positional vocabulary is mechanically detectable**, and the detectable
   parts are the *structural* ones — pawn structure, squares, files, material configuration. That is
   a substantial, buildable section of the swarm, and it was the part in doubt.
2. **The undetectable third is a coherent group**: prophylaxis, restraint, harmony, activity — all
   concepts about *intention and relation* rather than arrangement. They will need engine-derived
   proxies or the language layer, and they should be scheduled late, after the structural sections
   prove the pipeline.
3. **The tactics/strategy boundary is ours, not the game's.** Nimzowitsch lists the pin and
   discovered check among his Elements while Lichess tags them as tactical motifs. M2 should not
   split sections along that seam just because our two source vocabularies happen to.
4. **Detectability is necessary, not sufficient** (L-007). Every concept above still needs
   relevance-weighting (open question C6) before it becomes coaching rather than description.

## Outstanding

- Verify *My System*'s Part-2 chapter list against the text rather than from recall — it is the one
  unverified structural claim in this note.
- Capablanca's contribution is pedagogical order rather than vocabulary; his concepts are largely a
  subset of the above, taught earlier and more simply.
