"""The ten knowledge domains, what gates what, and which claims land where.

Source: docs/notes/domain.chess-concepts.md § A (the domains) and § C (the
partial order). Evidence class `expert-consensus`, recorded in that note.

**Why this exists.** `chesscoach/arbiter.py` has carried a hole since it was
written:

    "On prerequisite ordering. The spec lists it as a ranking criterion, and it
    is deliberately not implemented yet... among the claim kinds that currently
    exist, tactical and process weaknesses have no defensible ordering between
    them. Inventing one would be fabricated pedagogy."

The blocker was never the data structure. It was that nobody had written down
which concept gates which **with a source**, in a form code could read. § C is
that structure, in prose. This is the same structure as data.

**Two different kinds of statement live here, and only one is chess knowledge.**

The domains and their order are a claim *about chess pedagogy*, sourced to the
note and through it to the literature. The claim-to-domain map is a statement
about **what our own detectors measure** -- `allowed_motif.fork` counts a
tactical motif, so it belongs to K2 by the definition of K2 -- and that is the
same kind of statement as a `Claim` node itself, which needs no endorsement.

**Where a claim's domain is genuinely arguable it is left out.** `late_castling`
is an opening principle (K6) and a practical habit (K9) depending on why the
player did it, and picking one would be exactly the fabricated pedagogy the
arbiter refused to invent. `domain_of` returns `None` there, and callers must
treat that as *unknown* rather than as *unrelated*.
"""

from __future__ import annotations

from dataclasses import dataclass

SOURCE = "docs/notes/domain.chess-concepts.md § A, § C"
EVIDENCE_CLASS = "expert-consensus"


@dataclass(frozen=True)
class Domain:
    """One of the ten knowledge domains."""

    key: str
    name: str
    covers: str


DOMAINS: tuple[Domain, ...] = (
    Domain("K1", "Fundamentals",
           "rules, notation, basic checkmates, piece values, hanging pieces"),
    Domain("K2", "Tactics", "motifs and mating patterns — the pattern vocabulary"),
    Domain("K3", "Calculation & visualisation",
           "candidate moves, forcing-move scans, depth, stopping criteria"),
    Domain("K4", "Positional judgement",
           "imbalances, structure, square and piece quality"),
    Domain("K5", "Planning", "turning an evaluation into a plan"),
    Domain("K6", "Openings",
           "principles, repertoire, structures reached, move order"),
    Domain("K7", "Endgames", "elementary mates, K+P theory, rook endings, technique"),
    Domain("K8", "Attack & defence",
           "king attack patterns, sacrifices, prophylaxis, defensive resources"),
    Domain("K9", "Practical process",
           "time management, blunder-checking, converting won positions"),
    Domain("K10", "Meta-learning",
           "how to train: puzzle practice, game review, study balance"),
)

# The partial order, exactly as § C draws it. `(a, b)` means **a gates b**.
#
# K9 and K10 appear in no pair on purpose: the note calls them "cross-cutting,
# teachable at any level", so they gate nothing and nothing gates them. An
# absent edge here means *unknown or unordered*, never *unrelated*.
PREREQUISITES: tuple[tuple[str, str], ...] = (
    ("K1", "K2"),
    ("K1", "K7"),
    ("K1", "K6"),
    ("K1", "K4"),
    # "Calculation depends on the tactical pattern vocabulary. You cannot
    # generate good candidate moves for patterns you do not know." -- § C's
    # first structural claim, stated there as load-bearing.
    ("K2", "K3"),
    ("K3", "K8"),
    ("K3", "K5"),
    ("K4", "K5"),
    ("K5", "K6"),
)

# Which domain a claim measures. **Only where it is not arguable.**
#
# This is a statement about our own detectors, not about chess: a fork is a
# tactical motif by K2's own definition. Claims whose domain depends on *why*
# the player did the thing are deliberately absent -- see the module docstring.
CLAIM_DOMAINS: dict[str, str] = {
    # Motifs are the pattern vocabulary, which is what K2 is.
    "allowed_motif": "K2",
    "missed_motif": "K2",
    "executed_motif": "K2",
    "moved_into_attack": "K2",
    "miscounted_exchange": "K2",
    # Endgames.
    "endgame_error": "K7",
    # The clock and the habit of checking: K9's own list.
    "long_think_error": "K9",
    "time_pressure_error": "K9",
    "instant_move_error": "K9",
    "time_budget_error": "K9",
    # Structure and square quality is what K4 evaluates.
    "concedes_weakness": "K4",
    "allows_square": "K4",
    # King attack and defensive resources.
    "allows_pressure": "K8",
    "sacrificed_for_attack": "K8",
    # Opening theory and what the player knows of it.
    "out_of_book": "K6",
    "opening_disadvantage": "K6",
}

# Named rather than left implicit, because "we have not decided" and "there is
# nothing to decide" must not look the same. Each of these is arguable in a way
# the ones above are not.
UNMAPPED_ON_PURPOSE: dict[str, str] = {
    "late_castling": "an opening principle (K6) or a practical habit (K9), "
                     "depending on why the player delayed",
    "slow_development": "the same ambiguity as late_castling",
    "repeat_move": "the same ambiguity as late_castling",
    "pawn_error": "a pawn move judged by the engine — K4 if it is structure, "
                  "K3 if it is calculation, and the detector cannot tell",
    "early_error": "any error inside the opening window, so it spans every "
                   "domain an error can belong to",
}


def domain_of(claim_kind: str) -> str | None:
    """Which domain this claim measures, or None for *unknown*.

    None means the mapping was not made, **never that the claim belongs
    nowhere**. Five claim kinds are unmapped on purpose and `UNMAPPED_ON_PURPOSE`
    says why for each.
    """
    return CLAIM_DOMAINS.get(claim_kind)


def gates(first: str, second: str) -> bool | None:
    """Does `first` gate `second`? True, False, or None for unknown.

    **Three answers, not two.** The arbiter refused to rank on prerequisites
    because inventing an order is fabricated pedagogy, and a function that
    returned `False` for "we do not know" would let it do exactly that while
    looking careful. Unknown is the common answer and is meant to be.
    """
    known = {d.key for d in DOMAINS}
    if first not in known or second not in known:
        return None
    if (first, second) in PREREQUISITES:
        return True
    if _reaches(first, second):
        return True
    if _reaches(second, first):
        return False
    # Both are real domains and neither reaches the other: K2 and K9, say.
    # That is not "no", it is "the order was never stated".
    return None


def _reaches(start: str, goal: str) -> bool:
    """Is there a chain of prerequisites from `start` to `goal`?"""
    seen: set[str] = set()
    stack = [start]
    while stack:
        here = stack.pop()
        for gate, gated in PREREQUISITES:
            if gate != here or gated in seen:
                continue
            if gated == goal:
                return True
            seen.add(gated)
            stack.append(gated)
    return False


def claim_gates(first_kind: str, second_kind: str) -> bool | None:
    """The same question asked about two claims rather than two domains."""
    first, second = domain_of(first_kind), domain_of(second_kind)
    if first is None or second is None:
        return None
    return gates(first, second)
