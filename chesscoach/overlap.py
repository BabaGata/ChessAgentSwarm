"""When two claims turn out to be about the same moves.

Screen: docs/notes/experiments.e42-claim-overlap.md

Sections measure in isolation and communicate only through the profile, which is
what keeps them independently testable — and means none of them can notice that
it is describing the same mistakes as another from a different angle. An error in
the opening is counted by `early_error`; if a piece was hanging it is counted
again by `missed_motif.hangingPiece`; if it was played in two seconds it is
counted a third time by `instant_move_error`.

`drop_redundant_aggregates` handles the one case a convention can express — a
pooled parent against its own subdivision, inside one section. Across sections
there is no shared vocabulary to key on, and writing a table of which claim
contains which would be invented pedagogy: unfalsifiable, and wrong the first
time a section changed what it counts.

So this decides it by measurement. Every claim reports `instances_at`, and
containment becomes an observable.

**The threshold is calibrated rather than chosen.** E42b measured coverage on
exactly the pairs the project *already* deletes by convention and found them at
60-69 %. Setting the cross-section rule at 60 % means it deletes nothing the
codebase would not already delete if the two claims happened to share a kind.

**And it is worth being honest about how little this does.** E42 measured 501
cross-section pairs across twelve real players: the median coverage is 3 %, the
90th percentile is 15 %, and exactly **one pair** reaches this threshold. The
claims really are about different moves. This exists because that one pair is a
genuine waste of one of three slots, not because the swarm was full of
duplicates — it was not, and an earlier reading of E41 that said otherwise was
wrong.
"""

from __future__ import annotations

from chesscoach.profile.models import ConfidenceTier, Finding

# Calibrated in E42b against the pairs `drop_redundant_aggregates` already
# removes. Their weakest tenth sits here.
REDUNDANT_COVERAGE = 0.60

# Which tiers may be said out loud. A claim below these cannot replace one above
# them, however much of it they share.
_ASSERTABLE = (ConfidenceTier.FOCUS, ConfidenceTier.PRIORITY)


def coverage(wide: Finding, narrow: Finding) -> float:
    """Share of `wide`'s instances that `narrow` also claims.

    Zero when either side does not report its moves. Empty means **not
    recorded**, never "no instances", so an unwired claim must not read as fully
    covered and be deleted for it.
    """
    w = frozenset(wide.measurement.instances_at)
    n = frozenset(narrow.measurement.instances_at)
    if not w or not n:
        return 0.0
    return len(w & n) / len(w)


def drop_covered_claims(
    asserted: tuple[Finding, ...], watched: tuple[Finding, ...]
) -> tuple[tuple[Finding, ...], tuple[Finding, ...]]:
    """Remove claims that mostly restate a narrower one, across both pools.

    The **narrower** claim is kept, for the same reason the within-section rule
    keeps the subdivision: it names the same problem and says where to look.

    Two guards, both learned rather than assumed:

    * **A claim is only replaced by one at least as assertable as itself.**
      Across pools this is what stops the rule deleting something the player can
      be told about in favour of something they cannot, which would leave them
      with nothing where they previously had a priority.
    * **Removal is decided against the original set, not applied in sequence.**
      A covers B covers C would otherwise cascade until nothing is left.
    """
    everything = tuple(asserted) + tuple(watched)
    if len(everything) < 2:
        return tuple(asserted), tuple(watched)

    rank = {f.id: 0 if f.confidence.tier in _ASSERTABLE else 1 for f in everything}
    size = {f.id: len(frozenset(f.measurement.instances_at)) for f in everything}

    removed: set[str] = set()
    for wide in everything:
        for narrow in everything:
            if wide.id == narrow.id or narrow.id in removed:
                continue
            # Strictly narrower, so two identical claims cannot delete each
            # other and the outcome cannot depend on iteration order.
            if size[narrow.id] >= size[wide.id]:
                continue
            if rank[narrow.id] > rank[wide.id]:
                continue
            if coverage(wide, narrow) >= REDUNDANT_COVERAGE:
                removed.add(wide.id)
                break

    return (
        tuple(f for f in asserted if f.id not in removed),
        tuple(f for f in watched if f.id not in removed),
    )
