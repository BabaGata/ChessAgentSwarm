---
id: cas-learning-risks
title: Risks, Issues & Prevention
desc: 'Known risks and encountered blockers, each with a prevention measure.'
updated: 1785254500000
created: 1785254500000
---

# Risks, Issues & Prevention

Two sections: **anticipated risks** (not yet materialised) and **encountered issues** (they did).
Every encountered issue must end with a prevention measure that changes something concrete — a rule
in [[process]], a check in the `adaptive-cycle` skill, a test, or a design constraint.

## Anticipated risks

| ID | Risk | Impact | Likelihood | Prevention / early warning |
|---|---|---|---|---|
| R-01 | **Cost creep** — the design quietly becomes LLM-call-heavy and violates C1 | high | high | Cost per operation is estimated at design time and measured in [[evaluation]]; D9 scorecard dimension makes it visible every cycle |
| R-02 | **Unfalsifiable coaching output** — the swarm produces plausible advice nobody can verify | high | high | V8 explainability is a vision capability, not a nice-to-have; every recommendation must cite evidence from the player's own games |
| R-03 | **Folklore laundering** — LLM-generated chess advice presented as expert knowledge | high | medium | Evidence-class marking in [[capacity.knowledge]]; sources recorded in [[domain.sources]] |
| R-04 | **Agent sprawl** — one agent per section produces a swarm too large to orchestrate or evaluate | medium | medium | M2 orders sections by priority; build agents in priority order and re-assess the swarm each M5 rather than building all of them |
| R-05 | **Scope drift into engine work** | medium | medium | Explicit non-goal in [[vision]]; use existing engines |
| R-06 | **Documentation rot** — notes describe an intended system, not the real one | high | medium | [[state]] is rewritten every cycle with evidence; the cycle does not close without it |
| R-07 | **Codebase getting out of hand** | medium | medium | Refactoring assessment is a mandatory step of every cycle before commit ([[process]]) |
| R-08 | **Thesis-time overrun** — infinite refinement of the loop instead of building | high | medium | Each mission step has a definition of done; C6 requires each step to end on something usable |
| R-09 | **Evaluation without ground truth** — no way to tell good coaching from bad | high | high | [[evaluation]] must define proxies (engine agreement, rating trajectory, expert review) before M4 builds anything |
| R-10 | **Player data privacy** — handling real players' games and profiles | medium | low | Use public games only; no personal data beyond public usernames; state this in the thesis |
| R-11 | **Weak source base** — chess-improvement web content is largely commercial marketing of variable rigour, and some of it sells the very thing it recommends studying | high | **materialised in M1** | Evidence class recorded per source in [[domain.sources]]; commercial bias noted inline; primary sources required before any claim enters the thesis |
| R-12 | **LLM coaching default is the anti-pattern** — asked to coach, a language model lists many weaknesses and recites generic level-appropriate advice, which is exactly what [[domain.coaching]] § 4 identifies as bad coaching | high | high | Design against it explicitly: the swarm must output **one or two** priorities with evidence; add this to the agent efficacy measures in [[evaluation]] |
| R-15 | **Regression to the mean makes any coaching system look effective** — a weakness is diagnosed because its rate was extreme, and re-measuring an extreme value returns a lower one whether or not anything was done | **critical** | **materialised and mitigated** | Measured in E05 at 92 % of targets met with no intervention. **Now 15 %, held out** (57 predictions, 84 players, cross-validated at 2 and 5 folds, spread 0.011). Targets are calibrated against the measured no-change distribution rather than the selected value, and every progress sign states how often doing nothing would suffice. **Two things keep this open.** The effect's *size* turned out to depend on how thinly the finding was measured — +11.2 points at 60-game histories, +4.8 at 150 (L-019) — so the constant is not a fixed property and must be refitted whenever the sample changes (**D9**). And only the false-positive side is measured: nothing shows a coached player could clear the bar (**D8**) |
| R-14 | **Correct but irrelevant output** — the swarm states things that are true, specific, evidence-backed and worthless. No correctness test catches this, because nothing is wrong | high | **materialised twice: E02 and M5** | Predicted from base rates in E02; **occurred on real data in M5**, where four of six players showed the same "weakness" at similar magnitude because the condition was selected by the thing causing the error (L-011). Mitigations now in force: selection-confounded conditions are withheld pending a peer baseline; the peer corpus is promoted to blocking; evaluation metric D1 (inter-player divergence) is promoted so the next instance is caught automatically rather than by eye |
| R-13 | **Statistical overclaiming** — declaring a weakness from a handful of games, or comparing ACPL across time controls and opponents | high | **materialised in E03 and caught** | Minimum-sample and confidence rules ([[domain.signals]] § 4, question C2). **Demonstrated:** E03's phase-stratified backward-pawn effect (lift 2.40) looked convincing, had a tidy mechanism, and reversed to 0.76 on held-out players. Mandatory control: every discovered association reproduces on a *different player set* before being written down (L-008) |

## Encountered issues

| ID | Date | Issue | Root cause | Fix | Prevention applied |
|---|---|---|---|---|---|
| — | — | none yet | | | |
