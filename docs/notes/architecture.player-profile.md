---
id: cas-arch-profile
title: Player Profile
desc: 'The structured artefact every agent reads and writes — the load-bearing design decision of the whole system.'
updated: 1785256100000
created: 1785256100000
---

# Player Profile

Resolves **C1** in [[open-questions]]. This is the system's blackboard, its memory, and the contract
between every component. Get it wrong and every agent is wrong together — which is why it is
specified before any agent is built.

## Design rules

1. **Claims are typed, never prose.** A finding is a record with fields, not a sentence. Prose
   appears in exactly two places: the free-text note attached to a piece of evidence, and the
   player's own words in a probe answer. Everything else is data. This is what makes findings
   comparable across sessions, testable, ablatable and cheap to feed to a language model.
2. **Every claim carries its evidence.** A finding without positions attached cannot be made (V8).
3. **Every claim carries its provenance** — engine, depth, date, corpus. E01 showed labels shift
   with analysis depth, so a finding measured at depth 12 and one at depth 18 are different
   measurements and must never be merged.
4. **Every claim carries its uncertainty** — sample size, interval, peer comparison, and whether it
   replicated on held-out games. E03 showed why (L-008).
5. **Context is part of the claim, not a footnote.** E03 found relevance is conditional: a feature
   that says nothing overall can say something within a phase. `"backward pawns"` is not a claim;
   `"backward pawns, in endgames, in rapid"` is.
6. **The profile persists across sessions.** V7 needs history; all five prior-art projects are
   stateless per analysis, which is why none of them can track progress.

## The Finding

The atomic unit. Everything the swarm believes about a player is a Finding.

```jsonc
{
  "id": "S1.missed_motif.fork.middlegame",   // deterministic: section + claim key
  "section": "S1",                            // owning agent — enables ablation (B3)

  "claim": {
    "kind": "missed_motif",                   // enum, not free text
    "subject": "fork",
    "direction": "own",                       // own weakness vs. conceded to opponent
    "context": { "phase": "middlegame", "time_control": "rapid" }
  },

  "measurement": {
    "instances": 14,
    "distinct_games": 9,                      // the statistically meaningful count
    "games_with_data": 47,
    "rate": 0.19,
    "ci95": [0.11, 0.31],
    "peer_rate": 0.11,                        // rating-band reference population
    "lift_vs_peer": 1.7
  },

  "provenance": {
    "engine": "Stockfish 18", "depth": 15,
    "corpus_id": "sha256:…",                  // exactly which games produced this
    "analysed_at": "2026-07-28"
  },

  "confidence": {
    "tier": "focus",                          // none | watch | focus | priority
    "replicated": true,                       // held-out split check (L-008)
    "reasons": ["distinct_games>=5", "peer_lift>1.5", "split_half_agreement"]
  },

  "gap_type": {
    "hypothesis": "skill",                    // knowledge | skill | process | psychological | unknown
    "determined_by": "probed",                // inferred | probed  — never silently assumed
    "probe_ids": ["p_0031"]
  },

  "evidence": [                               // capped, and RANDOMLY sampled — see below
    { "game_id": "abc123", "ply": 47, "fen": "…",
      "move_played": "Rfe8", "better_move": "Nxd5",
      "loss_wp": 34.2, "note": "knight fork on d5 available, queen and rook" }
  ],

  "status": "active",                         // candidate | active | addressed | dismissed
  "history": [ { "date": "2026-06-01", "tier": "watch", "rate": 0.24 } ]
}
```

### Two details that matter more than they look

**Evidence is randomly sampled, not cherry-picked.** The obvious implementation shows the worst
examples. That produces a coach who exaggerates, and it makes the evidence unrepresentative of the
claim's actual rate. Sample uniformly from the instances, with a fixed seed for reproducibility.

**`determined_by` must be explicit.** The difference between "we inferred this gap is a skill gap"
and "we asked and confirmed it" is the entire justification for V9. If the field is allowed to
default, the distinction quietly disappears and the swarm goes back to guessing (L-002).

## The Profile

```jsonc
{
  "schema_version": 1,
  "player": {
    "source": "lichess", "username": "…",
    "ratings": { "rapid": 1612, "blitz": 1548 },
    "band": "1400-1800"
  },
  "corpus": {
    "corpus_id": "sha256:…", "n_games": 47,
    "time_controls": ["rapid"], "date_range": ["2026-05-02", "2026-07-26"]
  },
  "context": {                                 // only obtainable by asking (V9)
    "goals": "…", "weekly_study_hours": 3, "self_reported_weaknesses": ["endgames"]
  },
  "findings": [ /* Finding[] */ ],
  "probes":   [ /* ProbeRecord[] */ ],
  "plan": {
    "created": "2026-07-28",
    "steps": [
      { "finding_id": "S1.missed_motif.fork.middlegame",
        "action": "…", "why": "…",
        "time_estimate_days": 14,
        "progress_sign": "missed-fork rate below 0.10 over the next 20 rapid games",
        "check_after_games": 20 }
    ]
  },
  "history": [ { "date": "2026-06-01", "corpus_id": "…", "finding_count": 11 } ]
}
```

**Every plan step must carry a `progress_sign` and a `check_after`.** A step without them cannot be
falsified, cannot be tracked, and is therefore not allowed to exist (V6, V7, R-02). This single
required field is what turns advice into something the system can be wrong about.

## Probe records

```jsonc
{ "id": "p_0031", "finding_id": "S1.missed_motif.fork.middlegame",
  "fen": "…", "asks": "move_and_reason",      // move_and_reason | plan | recall
  "conditions": "untimed",
  "player_move": "Nxd5", "player_reason": "it forks the queen and rook",
  "engine_best": "Nxd5", "verdict": "correct",
  "inference": "skill_not_knowledge",          // found it untimed → knows it, fails under clock
  "asked_at": "2026-07-28" }
```

The logic that makes probes worth their cost: **found untimed but missed in games ⇒ skill or process
gap, not a knowledge gap** — and the remedy differs completely ([[domain.coaching]] § 2).

## What this schema prevents

| Failure | Prevented by |
|---|---|
| Unfalsifiable advice (R-02) | mandatory `evidence`; mandatory `progress_sign` |
| Statistical overclaiming (R-13) | `distinct_games`, `ci95`, `replicated` |
| True-but-useless output (R-14) | `peer_rate` / `lift_vs_peer` — a claim true of everyone has lift ≈ 1 |
| Generic advice (R-12) | findings are per-player measurements; two players cannot produce the same profile |
| Merging incomparable analyses (L-006) | `provenance.depth` on every finding |
| Silent gap-type guessing (L-002) | `gap_type.determined_by` |
| Undetectable agent freeloading | `section` on every finding makes ablation mechanical (B3) |

## Open

- The `claim.kind` enum is deliberately not fixed yet — it grows as sections are built, and freezing
  it now would be guessing. Rule: a new kind is added only with a section that emits it and a test
  that exercises it.
- Schema version 1 will be wrong somewhere. Migration is a plain JSON transform, and profiles are
  regenerable from the corpus, which is the reason to keep the analysis cache separate.
