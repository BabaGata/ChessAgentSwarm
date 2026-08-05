"""Deciding whether a player's sentence names a given reason.

Spec: docs/notes/capacity.agents.prober.md § 3-4

Three implementations of the same one-method Protocol, so they can be swapped
and — more importantly — **measured against each other**. Which one ships is an
empirical question (§ 9), not a matter of taste:

* `KeywordFloor`      — the floor. Fails exactly where the agent note says it
                        will: a player who understands pins and never says the
                        word is scored as ignorant.
* `EmbeddingBaseline` — semantic similarity, no generation, deterministic. This
                        is the thing a language model has to **beat** to earn
                        its cost, and it handles the vocabulary problem the
                        floor does not.
* `OllamaClassifier`  — a local instruct model. Free and offline (C1, C3).

All three return `None` for "cannot tell", which is a real outcome and is
recorded rather than resolved by guessing.

Nothing here is ever asked what the best move is, or to evaluate a position, or
to produce chess advice. The reason to check against is supplied by a detector.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field

# Motif names are camelCase Lichess theme keys; players do not write them that
# way, so each carries the words someone might actually use. Not a definition of
# the tactic — a description dense enough for a similarity comparison.
REASON_DESCRIPTIONS: dict[str, str] = {
    "pin": "a piece cannot move because a more valuable piece behind it would be captured",
    "fork": "one piece attacks two or more enemy pieces at the same time, a double attack",
    "skewer": "a valuable piece is attacked and when it moves the piece behind it is captured",
    "discoveredAttack": "moving one piece uncovers an attack from another piece behind it",
    "hangingPiece": "a piece is undefended and can simply be captured for free",
    "trappedPiece": "a piece has no safe squares to escape to and will be won",
    "backRankMate": "the king is mated on its back rank because its own pawns block escape",
    "capturingDefender": "capturing the piece that was defending something, removing the defender",
}

# Words that give the concept away without the term. Used only by the floor.
REASON_KEYWORDS: dict[str, tuple[str, ...]] = {
    "pin": ("pin", "pinned", "pins"),
    "fork": ("fork", "forks", "forked", "double attack"),
    "skewer": ("skewer", "skewers", "skewered"),
    "discoveredAttack": ("discover", "discovered", "uncover", "uncovers"),
    "hangingPiece": ("hanging", "hangs", "undefended", "free piece", "en prise"),
    "trappedPiece": ("trap", "trapped", "no squares", "nowhere to go"),
    "backRankMate": ("back rank", "back-rank", "backrank", "eighth rank"),
    "capturingDefender": ("defender", "defence", "defense", "guard", "guarding"),
}

# Answers that decline rather than explain. Checked before any classifier runs,
# because "did the player offer a reason" is a property of the utterance and not
# of its chess content — and the inference table treats *declined* and *named the
# wrong tactic* as opposite cases, so a classifier asked to decide both at once
# collapses them. E07 measured every classifier failing this identically.
#
# Deterministic and therefore brittle: it will miss phrasings not listed here.
# That is the accepted trade for now, and the first thing real player answers
# should be used to check (D10).
DECLINING_PHRASES = (
    "don't know",
    "dont know",
    "no idea",
    "not sure",
    "no clue",
    "intuition",
    "looked good",
    "looked right",
    "seemed good",
    "just played it",
    "engine said",
    "guess",
)

OLLAMA_URL = "http://localhost:11434"
REQUEST_TIMEOUT_S = 60


class ClassifierUnavailable(RuntimeError):
    """The backend could not be reached.

    Deliberately **not** the same thing as a verdict of "unclear". Conflating
    them means a probe session run against a model that is not running is
    indistinguishable, in the stored profile, from one where the player was
    vague — and the second is evidence about the player while the first is
    evidence about the infrastructure.
    """

# The whole prompt. It supplies the reason and asks one closed question about
# the text; it never asks the model anything about chess it could get wrong in a
# way that would matter.
PROMPT = """You are marking one short answer from a chess student.

The student was shown a position and asked what they would play and why.
The reason the position actually turns on is: {reason} ({description}).

The student wrote: "{answer}"

Does the student's explanation refer to that reason? They may describe it in
their own words, informally, or in imperfect English — that still counts as yes.
Naming a different tactic, or giving an unrelated reason, is no.
If they declined to give a reason at all, or said they did not know, answer
unclear.

Reply with one word only: yes, no, or unclear."""


def declines_to_answer(text: str) -> bool:
    """Did the player decline to give a reason, rather than give a wrong one?

    Kept out of the classifiers so that all of them — including a future one —
    treat refusal the same way, and so this can be replaced without touching
    them when it proves too brittle.
    """
    stripped = text.strip().casefold()
    if not stripped or stripped in {"?", "-", "n/a", "idk"}:
        return True
    return any(phrase in stripped for phrase in DECLINING_PHRASES)


@dataclass(frozen=True)
class KeywordFloor:
    """Substring matching. Present to be beaten, not to be used."""

    name: str = "keyword-floor/v1"

    def classify(self, answer: str, expected_reason: str) -> bool | None:
        if declines_to_answer(answer):
            return None
        text = answer.strip().casefold()
        keywords = REASON_KEYWORDS.get(expected_reason, (expected_reason,))
        return any(word in text for word in keywords)


@dataclass
class EmbeddingBaseline:
    """Cosine similarity between the answer and a description of the reason.

    Deterministic and generation-free, so it costs a fraction of a model call
    and cannot hallucinate. Its weakness is that it cannot tell *naming the
    wrong tactic* from *naming none*: both simply score low.
    """

    model: str = "mxbai-embed-large"
    threshold: float = 0.62
    host: str = OLLAMA_URL
    name: str = field(init=False)

    def __post_init__(self) -> None:
        self.name = f"embed/{self.model}@{self.threshold}"

    def classify(self, answer: str, expected_reason: str) -> bool | None:
        if declines_to_answer(answer):
            return None
        description = REASON_DESCRIPTIONS.get(expected_reason)
        if description is None:
            return None

        answer_vector = self._embed(answer)
        reason_vector = self._embed(description)
        if answer_vector is None or reason_vector is None:
            return None
        return _cosine(answer_vector, reason_vector) >= self.threshold

    def _embed(self, text: str) -> list[float] | None:
        """None only when the backend replied without an embedding; an
        unreachable backend raises, so the two stay distinguishable."""
        payload = _post(f"{self.host}/api/embed", {"model": self.model, "input": text})
        embeddings = payload.get("embeddings") or []
        return embeddings[0] if embeddings else None


@dataclass
class OllamaClassifier:
    """A local instruct model, at temperature 0 so a verdict is reproducible."""

    model: str = "llama3.1:8b-instruct-q6_K"
    host: str = OLLAMA_URL
    name: str = field(init=False)

    def __post_init__(self) -> None:
        self.name = f"ollama/{self.model}"

    def classify(self, answer: str, expected_reason: str) -> bool | None:
        if declines_to_answer(answer):
            return None
        description = REASON_DESCRIPTIONS.get(expected_reason)
        if description is None:
            return None

        payload = _post(
            f"{self.host}/api/generate",
            {
                "model": self.model,
                "prompt": PROMPT.format(
                    reason=expected_reason, description=description, answer=answer
                ),
                "stream": False,
                # Reproducibility is not optional: a stored gap_type has to be
                # re-derivable, and this is the only non-deterministic component
                # in the whole system.
                "options": {"temperature": 0, "seed": 7, "num_predict": 8},
            },
        )
        return _verdict(payload.get("response", ""))


def _verdict(text: str) -> bool | None:
    """Read a one-word answer, and refuse to guess at anything else."""
    word = text.strip().casefold().lstrip("*_ ").split()
    if not word:
        return None
    return {"yes": True, "no": False}.get(word[0].strip(".,:!"), None)


def _post(url: str, body: dict) -> dict:
    """Raise rather than return None when the backend cannot be reached.

    It used to return None, which the caller could not tell apart from a model
    that replied "unclear" — so a session run against a stopped Ollama produced
    a profile full of clean-looking `unknown` verdicts that were never actually
    asked. The prober still degrades rather than fails: `interpret` catches this
    and records `classifier_status: unavailable`, so the difference survives into
    the profile instead of being flattened there.
    """
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_S) as response:
            return json.loads(response.read())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
        raise ClassifierUnavailable(f"{url}: {error}") from error


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = (sum(x * x for x in a) ** 0.5) * (sum(y * y for y in b) ** 0.5)
    return dot / norm if norm else 0.0
