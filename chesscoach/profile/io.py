"""Reading and writing player profiles as JSON.

Profiles are JSON documents rather than database rows so a reviewer can read
exactly what the system believed about a player on a given date, and so test
fixtures are files (ADR-0007).

Serialisation is deterministic -- sorted keys, fixed formatting -- because the
evaluation plan's B4 test requires identical output for identical input.
Conversion is written out explicitly rather than reflected over: it is longer,
and it fails loudly when the schema changes instead of silently producing
something that nearly round-trips.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from chesscoach.profile.models import (
    SCHEMA_VERSION,
    Claim,
    Confidence,
    ConfidenceTier,
    CorpusRef,
    DeterminedBy,
    Evidence,
    Finding,
    GapType,
    GapTypeHypothesis,
    HistoryEntry,
    Measurement,
    Plan,
    PlanStep,
    PlayerContext,
    PlayerProfile,
    PlayerRef,
    ProbeRecord,
    ProfileHistoryEntry,
    Provenance,
    StepOutcome,
    Strength,
    StyleTendency,
)


# Versions this loader will accept. A version belongs here only when the step up
# from it is additive -- new optional fields, new enum members that old data
# cannot contain. Anything that changes the meaning of an existing field needs a
# real migration, not an entry.
#
#   v2 -> v3  added PlanStep.target_rate, CorpusRef.game_ids, Plan.outcomes
#   v3 -> v4  added GapTypeHypothesis.FRAGILE and four ProbeRecord audit fields
#   v4 -> v5  added ProbeRecord.classifier_status, so "the model was not running"
#             stops being indistinguishable from "the player was vague"
#   v5 -> v6  added PlayerProfile.strength -- what the games say about the
#             player's standard, as opposed to what they are filed under (V1)
#   v6 -> v7  added PlayerContext.already_tried and .plays_elsewhere, the two
#             context questions the schema did not have a home for
#   v7 -> v8  added PlayerProfile.style -- measured tendencies, which are not
#             findings and must not compete for a player's two priorities (V3)
#   v8 -> v9  added Measurement.cost_wp -- what a claim actually costs, where its
#             instances are mistakes and the question can be answered (D5)
#   v9 -> v10 added CorpusRef.excluded -- games the player brought that were not
#             diagnosed, and why, so the report can say so
#  v10 -> v11 added Measurement.peer_cost_per_game -- what the same claim costs a
#             player at this level, which turns a raw cost into a recoverable one
#
# One honest consequence of admitting v2: its plan steps carry no `target_rate`,
# so their progress signs describe a number the step does not hold and cannot be
# checked. That is not corrupted data -- it is accurately "this plan predates
# falsifiable targets", and the progress check already treats a missing target as
# not measurable rather than as failure.
READABLE_SCHEMA_VERSIONS = frozenset({2, 3, 4, 5, 6, 7, 8, 9, 10, SCHEMA_VERSION})


def to_dict(profile: PlayerProfile) -> dict[str, Any]:
    """Render a profile as plain JSON-compatible data."""
    return {
        "schema_version": profile.schema_version,
        "player": {
            "source": profile.player.source,
            "username": profile.player.username,
            "ratings": dict(profile.player.ratings),
            "band": profile.player.band,
        },
        "corpus": {
            "corpus_id": profile.corpus.corpus_id,
            "n_games": profile.corpus.n_games,
            "time_controls": list(profile.corpus.time_controls),
            "date_range": list(profile.corpus.date_range) if profile.corpus.date_range else None,
            "game_ids": list(profile.corpus.game_ids),
            "excluded": [[reason, count] for reason, count in profile.corpus.excluded],
        },
        "context": _context_to_dict(profile.context),
        "strength": _strength_to_dict(profile.strength),
        "style": [
            {
                "name": t.name,
                "share": t.share,
                "peer_share": t.peer_share,
                "moves": t.moves,
            }
            for t in profile.style
        ],
        "findings": [_finding_to_dict(f) for f in profile.findings],
        "probes": [_probe_to_dict(p) for p in profile.probes],
        "plan": _plan_to_dict(profile.plan),
        "history": [
            {"date": h.date, "corpus_id": h.corpus_id, "finding_count": h.finding_count}
            for h in profile.history
        ],
    }


def from_dict(payload: dict[str, Any]) -> PlayerProfile:
    """Rebuild a profile, refusing any schema version we do not understand.

    Older versions are read only where the difference is provably additive. v3
    became v4 by adding the `fragile` gap type and four optional `ProbeRecord`
    fields, so every v3 payload already *is* a valid v4 profile and refusing it
    would discard real analysis for no gain in safety.

    The result is stamped with the current version, because what comes back is a
    current-shaped object -- writing it out as v3 would claim it cannot carry
    probes, which it now can.
    """
    version = payload.get("schema_version")
    if version not in READABLE_SCHEMA_VERSIONS:
        raise ValueError(
            f"unsupported schema_version {version!r}, "
            f"readable: {sorted(READABLE_SCHEMA_VERSIONS)}"
        )

    corpus = payload["corpus"]
    date_range = corpus.get("date_range")
    player = payload["player"]

    return PlayerProfile(
        player=PlayerRef(
            source=player["source"],
            username=player["username"],
            ratings=dict(player.get("ratings") or {}),
            band=player.get("band"),
        ),
        corpus=CorpusRef(
            corpus_id=corpus["corpus_id"],
            n_games=corpus["n_games"],
            time_controls=tuple(corpus.get("time_controls") or ()),
            date_range=tuple(date_range) if date_range else None,
            game_ids=tuple(corpus.get("game_ids") or ()),
            # Absent before v10, where every game the player brought was
            # analysed -- an empty tuple is the honest upgrade, not a guess.
            excluded=tuple((reason, count) for reason, count in corpus.get("excluded") or ()),
        ),
        strength=_strength_from_dict(payload.get("strength")),
        style=tuple(StyleTendency(**t) for t in payload.get("style") or ()),
        findings=tuple(_finding_from_dict(f) for f in payload.get("findings") or ()),
        probes=tuple(_probe_from_dict(p) for p in payload.get("probes") or ()),
        context=_context_from_dict(payload.get("context")),
        plan=_plan_from_dict(payload.get("plan")),
        history=tuple(
            ProfileHistoryEntry(
                date=h["date"], corpus_id=h["corpus_id"], finding_count=h["finding_count"]
            )
            for h in payload.get("history") or ()
        ),
        schema_version=SCHEMA_VERSION,
    )


def save_profile(profile: PlayerProfile, path: Path | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(to_dict(profile), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def load_profile(path: Path | str) -> PlayerProfile:
    return from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


# --- findings ---------------------------------------------------------------


def _finding_to_dict(finding: Finding) -> dict[str, Any]:
    return {
        "id": finding.id,
        "section": finding.section,
        "claim": {
            "kind": finding.claim.kind,
            "subject": finding.claim.subject,
            "direction": finding.claim.direction,
            "context": finding.claim.context_dict,
        },
        "measurement": {
            "instances": finding.measurement.instances,
            "distinct_games": finding.measurement.distinct_games,
            "games_with_data": finding.measurement.games_with_data,
            "rate": finding.measurement.rate,
            "peer_rate": finding.measurement.peer_rate,
            "baseline_rate": finding.measurement.baseline_rate,
            "ci95": list(finding.measurement.ci95) if finding.measurement.ci95 else None,
            "cost_wp": finding.measurement.cost_wp,
            "cost_per_game": finding.measurement.cost_per_game,
            "peer_cost_per_game": finding.measurement.peer_cost_per_game,
            "excess_cost_per_game": finding.measurement.excess_cost_per_game,
            "lift_vs_peer": finding.measurement.lift_vs_peer,
            "lift_vs_baseline": finding.measurement.lift_vs_baseline,
        },
        "provenance": {
            "engine": finding.provenance.engine,
            "depth": finding.provenance.depth,
            "corpus_id": finding.provenance.corpus_id,
            "analysed_at": finding.provenance.analysed_at,
        },
        "confidence": {
            "tier": finding.confidence.tier.value,
            "replicated": finding.confidence.replicated,
            "reasons": list(finding.confidence.reasons),
        },
        "gap_type": {
            "hypothesis": finding.gap_type.hypothesis.value,
            "determined_by": finding.gap_type.determined_by.value,
            "probe_ids": list(finding.gap_type.probe_ids),
        },
        "evidence": [
            {
                "game_id": e.game_id,
                "ply": e.ply,
                "fen": e.fen,
                "move_played": e.move_played,
                "better_move": e.better_move,
                "loss_wp": e.loss_wp,
                "note": e.note,
            }
            for e in finding.evidence
        ],
        "status": finding.status,
        "history": [
            {"date": h.date, "tier": h.tier.value, "rate": h.rate} for h in finding.history
        ],
    }


def _finding_from_dict(payload: dict[str, Any]) -> Finding:
    claim = payload["claim"]
    measurement = payload["measurement"]
    provenance = payload["provenance"]
    confidence = payload["confidence"]
    gap_type = payload["gap_type"]
    ci95 = measurement.get("ci95")

    return Finding(
        section=payload["section"],
        claim=Claim.of(
            kind=claim["kind"],
            subject=claim["subject"],
            direction=claim.get("direction", "own"),
            context=claim.get("context") or {},
        ),
        measurement=Measurement(
            instances=measurement["instances"],
            distinct_games=measurement["distinct_games"],
            games_with_data=measurement["games_with_data"],
            rate=measurement["rate"],
            peer_rate=measurement.get("peer_rate"),
            baseline_rate=measurement.get("baseline_rate"),
            ci95=tuple(ci95) if ci95 else None,
            cost_wp=measurement.get("cost_wp"),
            peer_cost_per_game=measurement.get("peer_cost_per_game"),
        ),
        provenance=Provenance(
            engine=provenance["engine"],
            depth=provenance["depth"],
            corpus_id=provenance["corpus_id"],
            analysed_at=provenance["analysed_at"],
        ),
        confidence=Confidence(
            tier=ConfidenceTier(confidence["tier"]),
            replicated=confidence.get("replicated", False),
            reasons=tuple(confidence.get("reasons") or ()),
        ),
        gap_type=GapType(
            hypothesis=GapTypeHypothesis(gap_type["hypothesis"]),
            determined_by=DeterminedBy(gap_type["determined_by"]),
            probe_ids=tuple(gap_type.get("probe_ids") or ()),
        ),
        evidence=tuple(
            Evidence(
                game_id=e["game_id"],
                ply=e["ply"],
                fen=e["fen"],
                move_played=e.get("move_played"),
                better_move=e.get("better_move"),
                loss_wp=e.get("loss_wp"),
                note=e.get("note"),
            )
            for e in payload.get("evidence") or ()
        ),
        status=payload.get("status", "candidate"),
        history=tuple(
            HistoryEntry(date=h["date"], tier=ConfidenceTier(h["tier"]), rate=h["rate"])
            for h in payload.get("history") or ()
        ),
    )


# --- smaller parts ----------------------------------------------------------


def _probe_to_dict(probe: ProbeRecord) -> dict[str, Any]:
    return {
        "id": probe.id,
        "finding_id": probe.finding_id,
        "fen": probe.fen,
        "asks": probe.asks,
        "conditions": probe.conditions,
        "player_move": probe.player_move,
        "player_reason": probe.player_reason,
        "engine_best": probe.engine_best,
        "verdict": probe.verdict,
        "inference": probe.inference,
        "asked_at": probe.asked_at,
        "expected_reason": probe.expected_reason,
        "move_correct": probe.move_correct,
        "reason_matched": probe.reason_matched,
        "classifier": probe.classifier,
        "classifier_status": probe.classifier_status,
    }


def _probe_from_dict(payload: dict[str, Any]) -> ProbeRecord:
    return ProbeRecord(**payload)


def _strength_to_dict(strength: Strength | None) -> dict[str, Any] | None:
    if strength is None:
        return None
    return {
        "rating": strength.rating,
        "typical_error": strength.typical_error,
        "moves": strength.moves,
        "method": strength.method,
        "extrapolated": strength.extrapolated,
    }


def _strength_from_dict(payload: dict[str, Any] | None) -> Strength | None:
    return Strength(**payload) if payload else None


def _context_to_dict(context: PlayerContext | None) -> dict[str, Any] | None:
    if context is None:
        return None
    return {
        "goals": context.goals,
        "weekly_study_hours": context.weekly_study_hours,
        "self_reported_weaknesses": list(context.self_reported_weaknesses),
        "already_tried": context.already_tried,
        "plays_elsewhere": context.plays_elsewhere,
    }


def _context_from_dict(payload: dict[str, Any] | None) -> PlayerContext | None:
    if payload is None:
        return None
    return PlayerContext(
        goals=payload.get("goals"),
        weekly_study_hours=payload.get("weekly_study_hours"),
        self_reported_weaknesses=tuple(payload.get("self_reported_weaknesses") or ()),
        already_tried=payload.get("already_tried"),
        plays_elsewhere=payload.get("plays_elsewhere"),
    )


def _plan_to_dict(plan: Plan | None) -> dict[str, Any] | None:
    if plan is None:
        return None
    return {
        "created": plan.created,
        "steps": [
            {
                "finding_id": s.finding_id,
                "action": s.action,
                "why": s.why,
                "progress_sign": s.progress_sign,
                "check_after_games": s.check_after_games,
                "target_rate": s.target_rate,
                "time_estimate_days": s.time_estimate_days,
            }
            for s in plan.steps
        ],
        "outcomes": [
            {
                "finding_id": o.finding_id,
                "status": o.status,
                "target_rate": o.target_rate,
                "previous_rate": o.previous_rate,
                "observed_rate": o.observed_rate,
                "games_since": o.games_since,
                "checked_at": o.checked_at,
            }
            for o in plan.outcomes
        ],
    }


def _plan_from_dict(payload: dict[str, Any] | None) -> Plan | None:
    if payload is None:
        return None
    return Plan(
        created=payload["created"],
        steps=tuple(PlanStep(**step) for step in payload.get("steps") or ()),
        outcomes=tuple(StepOutcome(**outcome) for outcome in payload.get("outcomes") or ()),
    )
