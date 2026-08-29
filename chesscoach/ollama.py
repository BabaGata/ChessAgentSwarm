"""One way to talk to a local model, so three modules do not each invent one.

Design: [[decisions.0013-a-local-model-may-rephrase-what-it-cannot-assert]]

Nothing here decides anything. It posts a prompt and returns text, raising when
the backend cannot be reached — because *"Ollama is not running"* and *"the model
answered badly"* need different actions and must never look identical (L-046).

**Answers are constrained by a JSON Schema where one fits.** Ollama's `format`
field restricts decoding at the token level, so the model cannot emit `NONE`
where a list of integers is required, cannot answer `"3, NONE"`, and cannot
return prose that a number-scraper then misreads as indices — every one of which
was a measured failure in E51 and E52.

**The text parsers stay as a fallback and are not deleted.** A schema is a
request, not a guarantee: support varies by model, and Ollama Cloud does not
support structured outputs at all. So the order is: ask with a schema, parse the
JSON, and fall back to reading the prose if that fails. A model that ignores the
schema behaves exactly as it did before rather than breaking.

`classifiers.py` predates this and keeps its own client; it is left alone rather
than refactored in the same cycle as a feature — and deliberately, since its
agreement with the author is measured at kappa 0.74 (E07) and changing how its
answer is read would put that figure back in question.
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
    schema: dict | None = None,
    transport=None,
) -> str:
    """One completion, with the thinking field disabled by default.

    `schema` is a JSON Schema passed to Ollama's `format`, which constrains
    decoding rather than asking politely. The raw text still comes back — the
    caller decides whether to read it as JSON — so a model that ignores the
    schema is not a crash.

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
    if schema is not None:
        body["format"] = schema
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


def as_json(text: str, expect: type = dict):
    """Read a schema-constrained answer, or `None` if it is not one.

    **`None` means "not JSON", never "the model said nothing useful."** The
    caller falls back to reading the prose, which is what every agent did before
    schemas existed, so an unsupported model degrades instead of failing.

    A fenced block is tolerated because a model told to answer in JSON sometimes
    wraps it in markdown even under a schema.
    """
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        _, _, stripped = stripped.partition("\n")
    if not stripped:
        return None
    try:
        found = json.loads(stripped)
    except (ValueError, TypeError):
        return None
    return found if isinstance(found, expect) else None


def ints(data: dict | None, key: str, limit: int) -> tuple[int, ...]:
    """Integers from a parsed answer, bounded and deduplicated.

    The same contract as `indices` and for the same reason: an out-of-range
    index is a hallucination rather than a near miss, so it is dropped. A schema
    can require integers; it cannot know how many sentences were offered.
    """
    if not data:
        return ()
    found: list[int] = []
    for value in data.get(key) or ():
        if isinstance(value, bool) or not isinstance(value, int):
            continue
        if 0 <= value < limit and value not in found:
            found.append(value)
    return tuple(found)


def strings(data: dict | None, key: str) -> tuple[str, ...]:
    """Non-empty strings from a parsed answer, in order."""
    if not data:
        return ()
    return tuple(
        value.strip() for value in (data.get(key) or ())
        if isinstance(value, str) and value.strip()
    )


def array_of(item_type: str) -> dict:
    """The schema for a bare list, which is most of what is asked for here."""
    return {"type": "array", "items": {"type": item_type}}


def schema_of(**properties: dict) -> dict:
    """An object schema with every property required.

    Required by default because an optional field is how a model returns half an
    answer, and half an answer is what schemas are here to prevent.
    """
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
    }
