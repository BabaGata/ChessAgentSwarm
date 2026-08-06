"""Cleaning what a person typed, before anything reads it.

Two places take free text from a human — the probe answers and the context
questions — and both were bitten by the same thing, which is why this is one
module rather than two private helpers.

A byte-order mark survives `str.strip()`, because Python does not classify it as
whitespace. It arrives on anything pasted or piped, it is invisible, and it does
real damage in both directions: it turned a correct move into a wrong one in the
prober (a knowledge gap the player did not have), and it appeared verbatim in a
report as `You want ﻿stop losing to my brother`.
"""

from __future__ import annotations

# Characters that carry no meaning and are not whitespace to Python: the BOM,
# zero-width space, zero-width non-joiner and joiner, and the word joiner.
INVISIBLE = "﻿​‌‍⁠"

_STRIPPABLE = INVISIBLE + " \t\r\n"


def clean(text: str) -> str:
    """Trim whitespace and invisible characters from both ends."""
    return text.strip(_STRIPPABLE)


def is_blank(text: str | None) -> bool:
    """Nothing a person actually said, whatever the byte count suggests."""
    return not text or not clean(text)
