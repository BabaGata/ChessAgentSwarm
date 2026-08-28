"""One way to talk to a local model, so three modules do not each invent one.

Design: [[decisions.0013-a-local-model-may-rephrase-what-it-cannot-assert]]

Nothing here decides anything. It posts a prompt and returns text, raising when
the backend cannot be reached — because *"Ollama is not running"* and *"the model
answered badly"* need different actions and must never look identical (L-046).

`classifiers.py` predates this and keeps its own client; it is left alone rather
than refactored in the same cycle as a feature.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

OLLAMA_URL = "http://localhost:11434"

# A list item stands alone. Matching bare digits read the "5" out of "c5" and
# selected sentence five, so a model answering with prose about a pawn break
# silently became a selection -- exactly what answering by index is meant to
# prevent.
_NUMBERS = re.compile(r"(?<![A-Za-z0-9])\d{1,3}(?![A-Za-z0-9])")

# Deliberation is cost without benefit for every task here: the model is given
# text and asked about words. Left on, a reasoning model spent its whole token
# budget on a separate `thinking` field and returned nothing (E50).
THINK = False


class OllamaUnavailable(Exception):
    """The model could not be reached — which is not a bad answer."""


def post(url: str, body: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise OllamaUnavailable(f"{url} -> HTTP {error.code}") from None
    except Exception as error:
        raise OllamaUnavailable(f"{url} -> {type(error).__name__}") from None


def generate(
    model: str,
    prompt: str,
    *,
    host: str = OLLAMA_URL,
    think: bool | None = THINK,
    num_predict: int = 400,
    temperature: float = 0.3,
    seed: int = 7,
    transport=None,
) -> str:
    """One completion, with the thinking field disabled by default.

    A model that rejects `think` outright is retried without it, so an
    unsupported *option* is not mistaken for an unsupported *model*.
    """
    send = transport or post
    body = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "seed": seed,
            "num_predict": num_predict,
        },
    }
    if think is not None:
        body["think"] = think
    try:
        payload = send(f"{host}/api/generate", body)
    except OllamaUnavailable:
        if think is None:
            raise
        body.pop("think")
        payload = send(f"{host}/api/generate", body)
    return payload.get("response", "")


def indices(text: str, limit: int) -> tuple[int, ...]:
    """Read a list of numbers out of a model's answer, and refuse the rest.

    Models answer "2, 5, 7", "[2,5,7]", "2. 5. 7." and occasionally a sentence
    with the numbers embedded. Every integer in range is taken, in order, without
    duplicates — and anything out of range is dropped rather than clamped,
    because a hallucinated index is not a near miss.
    """
    found: list[int] = []
    for token in _NUMBERS.findall(text):
        value = int(token)
        if 0 <= value < limit and value not in found:
            found.append(value)
    return tuple(found)
