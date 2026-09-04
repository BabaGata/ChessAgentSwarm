"""Flat, or merely too rare to tell? These need different remedies.

A claim failing the dispersion screen has two very different explanations:

  (a) players really do share one rate -- the claim describes chess, not a player
  (b) the events are so rare that no realistic difference could have been seen

Only (a) is a reason to stop asserting something. (b) is a sample-size problem.

For a beta-binomial, dispersion relates to real between-player spread by
    phi = 1 + (n - 1) * rho,     rho = var(p) / (p * (1 - p))
so the smallest dispersion the test could have rejected converts into the
smallest *between-player spread in the rate* the data could have revealed.
Expressed as a ratio -- how many times commoner a player one SD above the mean
is than one at the mean -- it says what the screen was blind to.
"""
from __future__ import annotations
import json, math
from pathlib import Path
from overdispersion import counts, dispersion, peers

FLAT = ["allowed_motif.backRankMate.own", "allowed_motif.fork.own",
        "allowed_motif.skewer.own", "allows_square.rook_seventh.own",
        "concedes_weakness.isolated.own", "executed_motif.discoveredAttack.own",
        "missed_motif.discoveredAttack.own", "missed_motif.fork.own",
        "missed_motif.trappedPiece.own", "slow_development.own"]


def chi2_crit(df: int) -> float:
    """Wilson-Hilferty inverse at the 0.95 point, as a ratio to df."""
    z = 1.6449
    return (1 - 2 / (9 * df) + z * math.sqrt(2 / (9 * df))) ** 3


print("COULD THE SCREEN HAVE SEEN A REAL DIFFERENCE IF ONE EXISTED?\n" + "=" * 94)
print("\n  MDE = smallest between-player spread detectable at p<0.05, as a ratio:")
print("  a player one SD above the mean against one at the mean.\n")
print(f"  {'claim':<34}{'players':>8}{'rate':>8}{'opp/player':>12}{'phi':>7}{'phi*':>7}{'MDE':>9}")
print("  " + "-" * 90)

for claim in FLAT:
    obs = counts(claim)
    p, phi, tail = dispersion(obs)
    n = sum(n for _, n in obs) / len(obs)
    crit = chi2_crit(len(obs) - 1)
    rho = max(0.0, (crit - 1) / (n - 1)) if n > 1 else float("nan")
    sd = math.sqrt(rho * p * (1 - p))
    mde = (p + sd) / p
    print(f"  {claim[:33]:<34}{len(obs):>8}{p:>8.3f}{n:>12.0f}{phi:>7.2f}{crit:>7.2f}{mde:>8.2f}x")

print("\n" + "=" * 94)
print("""
  phi   = measured dispersion (1.0 = players interchangeable)
  phi*  = dispersion the test would have needed to reject the null
  MDE   = the real difference that corresponds to, in rate terms

  A small MDE with phi near 1 means the claim is genuinely flat: a difference
  that size would have shown, and did not. A large MDE means the screen was
  blind and the verdict is 'not shown', not 'not there'.
""")
