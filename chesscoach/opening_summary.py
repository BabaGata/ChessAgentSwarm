"""Turning quoted sentences into a few that read naturally.

Design: [[decisions.0013-a-local-model-may-rephrase-what-it-cannot-assert]]

[[decisions.0012-quote-the-plans-rather-than-write-them]] established that the
system quotes and never writes. The quotes work, and they read like quotes:
three sentences from two publishers, in two registers, joined by nothing.

**The distinction this module rests on: rephrasing is not asserting.** A model
told *"say this more plainly"* is doing language work on supplied text. A model
told *"explain the Pirc"* is being asked what it believes about chess, which is
R-03's folklore. The first is checkable and the second is not, so only the first
is allowed — and every output is checked before it is kept.

    quotes  ->  Ollama rephrases  ->  grounding check  ->  accept or fall back

**Falling back is a normal outcome, not an error.** A rejected rewrite returns
the verbatim quotes, which is exactly what shipped before this module existed.
The system is never worse off for trying, and `Summary.accepted` records which
happened so the rate is measurable rather than assumed.

Nothing here is asked what the best move is or what a plan should be. As with
`classifiers.py`, the model is given the answer and asked about the words.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Protocol

from chesscoach.grounding import Grounding, check

OLLAMA_URL = "http://localhost:11434"

# Low but not zero. At temperature 0 the models tested reproduced the source
# sentences almost verbatim, which passes every check and defeats the purpose.
TEMPERATURE = 0.3
SEED = 7

# Three plain sentences cost about 60 tokens. The headroom is for models that
# preface an answer despite being told not to -- and 220 was too tight, which is
# how a reasoning model came back empty and looked like a bad model.
NUM_PREDICT = 400

PROMPT = """Rewrite the chess notes below as {sentences} short sentences for a \
club player rated about 1500.

Rules:
- Use ONLY information in the notes. Add nothing.
- Do not mention any square or move that is not in the notes.
- Plain words. No chess jargon the reader would have to look up.
- Say what the player should aim for, not what happened.
- Write only the sentences. No preamble, no heading, no list markers.

Notes about the {opening}:
{notes}
"""


class SummariserUnavailable(Exception):
    """The model could not be reached — which is not a bad rewrite.

    Raised rather than returning the fallback silently, because "Ollama is not
    running" and "the model wrote something ungrounded" need different actions
    and would otherwise look identical in the output (L-046).
    """


@dataclass(frozen=True)
class Summary:
    """What the player would read, and how it was arrived at."""

    text: str
    # False when the rewrite was refused and the quotes were kept instead.
    accepted: bool
    # "quoted" or "composed" -- the evidence class, carried into the report so a
    # reader is never told a model's phrasing is a publisher's.
    evidence_class: str
    model: str
    grounding: Grounding | None = None

    @property
    def rejected_for(self) -> str:
        return "" if self.grounding is None else self.grounding.reason


class Summariser(Protocol):
    name: str

    def summarise(self, opening: str, quotes: tuple[str, ...]) -> Summary:
        ...


@dataclass(frozen=True)
class QuoteSummariser:
    """The floor: join the quotes and change nothing.

    This is what shipped before, kept as a real implementation rather than as a
    special case, so the model has something to beat and the comparison is a
    measurement (the shape `classifiers.py` uses for the same reason).
    """

    name: str = "quotes"

    def summarise(self, opening: str, quotes: tuple[str, ...]) -> Summary:
        return Summary(
            text=" ".join(quotes),
            accepted=True,
            evidence_class="quoted",
            model="none",
        )


@dataclass
class OllamaSummariser:
    """A local model rephrasing supplied sentences, with its work checked."""

    model: str = "qwen2.5:3b"
    host: str = OLLAMA_URL
    sentences: int = 3
    # Reasoning models put their chain of thought in a separate `thinking` field
    # and spend the token budget on it: qwen3:8b used all 220 tokens thinking and
    # returned an EMPTY response, which scored as "the model wrote nothing
    # usable" when the truth was "the harness never let it answer". With
    # thinking off it answers the same question in 59 tokens.
    #
    # There is also nothing here for a model to reason about. It is rephrasing
    # supplied sentences, not solving anything -- deliberation is the cost
    # without the benefit.
    think: bool | None = False
    # Injected so the accept/reject logic can be tested without a model running.
    # The rules are what must be right; the HTTP is incidental.
    post: object | None = None
    name: str = field(init=False)

    def __post_init__(self) -> None:
        self.name = f"ollama/{self.model}"
        if self.post is None:
            self.post = _post

    def summarise(self, opening: str, quotes: tuple[str, ...]) -> Summary:
        source = " ".join(quotes)
        if not quotes:
            # Nothing to rephrase. Asking the model anyway is precisely the
            # request this design refuses.
            return Summary(text="", accepted=False, evidence_class="quoted",
                           model=self.name)

        body = {
            "model": self.model,
            "prompt": PROMPT.format(
                opening=opening, notes=source, sentences=self.sentences
            ),
            "stream": False,
            "options": {
                "temperature": TEMPERATURE,
                "seed": SEED,
                "num_predict": NUM_PREDICT,
            },
        }
        if self.think is not None:
            body["think"] = self.think
        try:
            payload = self.post(f"{self.host}/api/generate", body)
        except SummariserUnavailable:
            # Models with no thinking mode reject the field outright. Retrying
            # without it is the difference between "this model is unsupported"
            # and "this option is".
            if self.think is None:
                raise
            body.pop("think")
            payload = self.post(f"{self.host}/api/generate", body)

        text = _clean(payload.get("response", ""))
        grounding = check(text, source)
        if not text or not grounding.grounded:
            return Summary(
                text=" ".join(quotes), accepted=False,
                evidence_class="quoted", model=self.name, grounding=grounding,
            )
        return Summary(
            text=text, accepted=True, evidence_class="composed",
            model=self.name, grounding=grounding,
        )


def _clean(response: str) -> str:
    """Strip the scaffolding instruct models add however firmly they are told not to."""
    text = response.strip()
    # Reasoning models emit a think block; keep what comes after it.
    if "</think>" in text:
        text = text.split("</think>", 1)[1].strip()
    lines = [line.strip().lstrip("-*0123456789. ").strip() for line in text.splitlines()]
    kept = [
        line for line in lines
        if line and not line.rstrip().endswith(":") and not line.startswith("#")
    ]
    return " ".join(kept).strip()


def _post(url: str, body: dict) -> dict:
    """Raise rather than return empty when the backend cannot be reached."""
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise SummariserUnavailable(f"{url} -> HTTP {error.code}") from None
    except Exception as error:
        raise SummariserUnavailable(f"{url} -> {type(error).__name__}") from None
