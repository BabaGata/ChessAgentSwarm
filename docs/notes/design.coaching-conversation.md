---
id: cas-design-coaching-conversation
title: 'Design — The conversation the player actually has with the swarm'
desc: 'A front agent that greets, asks for a username, runs the analysis, says the few things that matter, answers "explain that" from the knowledge base, and commits the player to one weakness for a week. Every sentence it can say is already computed; the model never supplies chess.'
updated: 1788888822570
created: 1788818400000
---

# Design — The coaching conversation

**Status:** **built 2026-09-08** · **Mission step:** M7 · Serves **V9** · `chesscoach/conversation.py`, `cli talk`

## What the author asked for

> *"This should be built, together with the main agent that will be used for conversation between the
> player and the system. So this agent after the system gets started should write some intro message
> and ask the player for his lichess username to do the analysis, then after the report is done, the
> agent should present the findings to the user. There shouldnt be to many statistics and some
> additional info as I saw it in report when I checked it last, it should have information about
> detected weaknesses and some simple comparison. Then there should start the conversation where
> agent will ask the user if he wants something to be more clearly explained and what does he wants to
> focus on for the start, then the agent give additional information if asked and once the agent gets
> information on what the player wants to focus on then the agent tells the user some exercises for
> what he wants and tells him to focus on that for a week and just then start with another weakness."*

Seven things, in order: **greet → ask username → analyse → say the few things that matter → offer to
explain → take a focus → give exercises for it and only it, for a week.**

## The one rule this design turns on

**The agent never supplies chess.** Every sentence it can say is already computed by something
deterministic:

| what the player asks for | where the words come from |
|---|---|
| the findings | `explainer` / `phrasing` — the same statements the report uses |
| the comparison | `Measurement.rate` against `baseline_rate`, already on the finding |
| *"explain that"* | `KnowledgeBase.for_player(key)` — endorsed entries, with their sources |
| the evidence | `Finding.evidence` — the player's own games, with links |
| exercises | `planner._action(finding)` — the step already written for that claim |
| what would show it worked | `PlanStep.progress_sign` and `target_rate` |

So the model is not in the content path at all. This is the `prober` boundary again
([[capacity.agents.prober]] § 3), and for the same reason: R-03 and hard rule 7 forbid LLM-generated
chess, and a conversation is exactly where a model would produce its most confident nonsense.

**Where a model may be used, and it is optional.** Mapping a free-text reply onto one of the choices
already on the table — *"the fork thing"* → `allowed_motif.fork` — is the same shape of job the
prober's classifier does: a closed question with the answer set known in advance. It must degrade to
a numbered menu when no model is reachable, and the menu is the primary interface, not the fallback.

## What the player sees, and what they do not

The author's complaint is specific: *"There shouldnt be to many statistics."* The full report stays
as the durable artefact — it is what step 7 of [[architecture.interaction]] promises and what the
player returns to. **The conversation shows a different, shorter thing**: the one or two weaknesses,
one comparison each, and the area map from [[design.report-by-aspect]]. Not the cost arithmetic, not
the confidence tiers, not the limits section, not the band notes.

| in the conversation | in the written report only |
|---|---|
| the 1–2 weaknesses, in a sentence each | cost in win probability, recoverable cost |
| one comparison: your rate against the standard | confidence tier and its reasons |
| the area map, one line each | the full evidence list, band notes, limits, what-could-not-be-assessed |

## One weakness, for a week

The author is explicit: *"tells him to focus on that for a week and just then start with another
weakness."* This is already the project's position rather than a new one — `arbiter` caps priorities
because *"here are your nine weaknesses"* is the recorded anti-pattern (R-12,
[[domain.coaching]] § 4). The conversation makes the cap **felt**: the player picks one, is given the
exercise for that one, and the others are explicitly deferred rather than listed again.

**A week is a duration and the plan measures games**, which are not the same thing and must not be
silently equated. `PlanStep.check_after_games` is the falsifiable part and stays; the week is the
human framing around it. The agent says both: *"for the next week — about N games — …"*.

## Definition of done

- [ ] `chesscoach/conversation.py`: a turn-taking agent with no I/O of its own, so it is testable
      without a terminal — it takes the player's line and returns what to say next
- [ ] greeting and username prompt; `cli talk` wires it to stdin/stdout and to `coach`'s pipeline
- [ ] the short presentation: weaknesses, one comparison each, the area map
- [ ] *"explain X"* serves `for_player(key)` and says so when there is nothing endorsed to serve
- [ ] a focus choice yields the planner's exercise for that claim, the week framing with its game
      count, and an explicit deferral of the rest
- [ ] no sentence about chess originates in the agent — asserted by a test over its whole vocabulary
- [ ] works with no model at all

## Alignment (phase 2)

- **V9** directly; **V8** because every line it says traces to the player's games or to an endorsed
  entry; **C1** because the model is optional and local.
- **Scorecard**: D12 dialogue is at 0 and this is the first thing to move it. D4 gap-detection is
  unaffected — no new detection.
- **Cheaper alternative considered**: printing the report and stopping, which is what exists.
  Rejected because the author's proposition, and shape D's *"expand on request"*, both rest on the
  conversation being where prioritisation happens.
- **Forecloses** nothing: the agent is a layer over existing output and deleting it leaves the report.

## The risk, named

**A conversational shell invites the model into the content.** The next person to touch this will be
tempted to let it paraphrase a finding "more naturally", and that is the failure R-03 exists to
prevent — a fluent sentence with no evidence under it. The test asserting the agent's vocabulary is
bounded is the guard, and it is the load-bearing part of this design rather than a nicety.


---

## Built

`chesscoach/conversation.py` holds the agent and no I/O; `cli talk` is the terminal around it. The
whole dialogue is therefore tested without a terminal — 24 tests, and the one that matters is
`TestTheAgentNeverSuppliesChess`.

### What the guard actually checks

The first version of that test read the module's source and forbade chess words anywhere. It failed
on its **own comments** — explaining why the knowledge lookup is keyed the way it is requires writing
`endgame_error` down. A test that polices comments rather than behaviour is worse than none, so it now
parses the AST, drops docstrings, and checks **only the string constants the module can print**. Under
that rule the agent is clean: `pawn`, `bishop`, `knight`, `rook`, `queen`, `castl`, `endgame`,
`tempo`, `outpost`, `sacrifice`, `fork` and `pin` appear in nothing it can say.

### Three things the build changed about the design

**The knowledge base is keyed by the thing, not by the claim.** Its 18 keys are motif names and claim
kinds, so `for_player("allowed_motif.fork.own")` misses every time — the agent said *"I have no
checked explanation"* for a claim the project has an endorsed entry for. It now tries the subject then
the kind.

**The exercise comes from the plan step, not from `planner._action`.** Both are the planner's work,
but the step is the artefact the player keeps; recomputing gives a second answer that can drift from
the written plan.

**A week and a game count are not the same horizon.** `check_after_games` reached **78** for a real
player, and the first draft said *"For the next 7 days, about 78 games"* — nobody plays 78 games in a
week. The week is when to stop thinking about anything else; the count is when the sign can be
checked, and it is only said in the sign.

Two smaller ones: the progress sign's trailing bookkeeping is trimmed before a player sees it (*"the
share of players who reach this without changing anything has not been recalibrated…"* is written for
the record, not for someone being coached), and a number is matched anywhere in the reply, because
*"explain 1"* is how people actually ask.

## Still not built

**The context questions.** `talk` sets `--no-questions`, so it does not yet ask what the player wants
or how much time they have, and the plan is not sized to them. The design says the conversation should
ask; today it asks only for a username.

**Return sessions through the conversation.** `check-progress` exists and the agent's closing line
promises it — *"run this again and I will check whether the sign showed up"* — but `talk` does not yet
take a previous profile and open with the verdict.

**The optional classifier.** Free text is matched literally against the numbered choices, which works
with no model at all. Nothing yet reads *"the fork thing"*; the menu is the interface and the design
says it stays that way unless the literal match proves too thin in use.