---
id: cas-design-report-by-aspect
title: 'Design — A report organised by aspect, with a standard per aspect'
desc: 'The authors proposal: openings, tactics, endgames, style and time each reported in the way that suits them, with the comprehensive report as a reference point and the focus chosen in conversation. Reviewed against R-12, with the failure modes and three alternatives.'
updated: 1788886394095
created: 1788732000000
---

# Design — A report organised by aspect

**Status:** **built 2026-09-08**, as shape **D**. `explainer._by_area`.

## The author's proposition

Report each aspect of the game in the way that suits it — openings not known, tactics frequently
missed, endgame types not known (and whether the player even *reaches* endgames), style — and stop
requiring a peer comparison everywhere:

> *"not all information has to be evaluated in comparison with peers, this comparison was done just
> so that not all players get the same response. The comprehensive report would just be the reference
> point for the user and then it can be discussed with the user what aspect should be focused on."*

## Review

**The insight is right.** Peer comparison is one way to make a claim non-trivial, not the only one,
and treating it as universal is what left 21 claims unusable
([[design.better-claims]]).

**It collides with R-12** — *"asked to coach, a model lists many weaknesses and recites generic
advice"* — and with [[domain.coaching]] § 4, which names *"here are your nine weaknesses"* as the
anti-pattern. The arbiter's cap of two exists for that reason.

**The proposal answers R-12, because of one clause**: the report is a *reference point* and the focus
is chosen in conversation. That puts a human in the prioritisation slot instead of an algorithm — V9,
which is already a vision capability. Dumping weaknesses without prioritising is the anti-pattern; a
map that is then talked through is not.

**What the framing understates.** The peer comparison also establishes that a thing is *worth
mentioning at all*. Removed with nothing in its place, every player is told "you miss forks", because
everyone does. Each aspect needs its own **standard**:

| aspect | standard replacing peers |
|---|---|
| openings | book depth against **the line's own theory depth** |
| endgames | positions lost **from winning** |
| tactics | **cost in win probability**, and the player's own rate across conditions |
| time | the player's own distribution |
| style | none — descriptive, and not coached |

## Alternatives

| | shape | risk |
|---|---|---|
| **A** the proposal | full per-aspect report, conversation picks focus | is the anti-pattern if the conversation never happens |
| **B** headline + browsable detail | keeps the 1–2 priorities, categories underneath | the categories become dead weight nobody opens |
| **C** conversation-first, no report | agent asks what to work on | **the player does not know what they do not know** |
| **D** tiered | one headline, one line per aspect, expand on request | none serious — recommended shape, with A's content |

## How it fails

| failure | inevitable? |
|---|---|
| report becomes the product, conversation never happens | **manageable** — open with a recommendation rather than close with one |
| filler in empty aspects | **manageable** — `for_player` already returns None for "nothing to say"; render that |
| **losing the standard peer comparison enforced** | **manageable, and the real risk** — it fails silently, so each aspect's standard must be written before it ships |
| cognitive load against "one diagnosis, one idea, one next step" | manageable by collapsing |
| an aspect with genuinely nothing to say | **not avoidable, and fine** — "tactics: nothing unusual" is honest |

**Nothing here is inevitable.** The third is the one that sinks it quietly.


---

## What was built

Shape **D**, on the author's instruction. `BY AREA OF THE GAME` sits **after** the ranked headline and
**before** the plan, labelled *"A map, not a to-do list — the plan above is what to act on."* The
ranked one or two priorities are untouched, so R-12's *"here are your nine weaknesses"* is answered by
position rather than by omission: the map is a reference point, which is the role the author asked
for.

Areas are ordered by the prerequisite chain in `domain.chess-concepts` § C, so it reads
foundations-first. **`chesscoach/domains.py` had been loaded only into the knowledge graph until
now**; this is the first thing a player sees that uses it.

### The third state, and why the schema moved

The note's failure table called filler in empty aspects *"manageable"*. It is worse than that: with
findings alone there is no way to tell *"measured, nothing unusual"* from *"never measured"*, and
collapsing them tells a player their endgames are fine when they reached no endgames — the empty case
answering like a real one (L-046).

So `PlayerProfile.coverage` (schema **16**) records every claim key a section measured, whatever the
gate then did with it, and the map has three states:

| state | line |
|---|---|
| a finding | names it |
| measured, nothing found | *"nothing stood out"* |
| a detector exists, nothing came up | listed under *"Nothing came up in these games"* |
| **no detector at all** | listed under *"Not measured by this system at all"* |

The last row is the one that matters most and is not about the player: **K1 Fundamentals, K3
Calculation, K5 Planning and K10 Meta-learning have no detector in this system**. Saying "nothing
stood out" there would be a claim about the player drawn from a gap in the software.

### What is not built

**The per-aspect standards are not finished**, and the note is explicit that this is the failure that
sinks the shape quietly. Two arrived on their own while the detectors were being corrected —
`out_of_book` judges against the line's own theory depth, `opening_pawn_error` against the player's
other opening moves — and the rest still rest on the peer comparison. The map therefore does **not**
say *"for your level"* on its lines, because that would be wrong for the two that no longer use it.

Shape D's *"expand on request"* half is also not built: there is no way to ask for one area in depth.
That needs V9, and the conversation it needs is the same one the author's proposition rests on.