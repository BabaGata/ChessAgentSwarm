"""Turning text into a vector, through the model Ollama already hosts.

Design: docs/notes/design.graph-knowledge-base.md § "Vector search belongs in the
same database"

The knowledge base has to match *"defined in a similar manner multiple times but
not worded the same"* -- the author's words, and the exact problem
[[experiments.e65-real-phrases]] hit, where "outpost" and "hole" are one idea
under two names and a keyword search finds neither from the other.

`chesscoach/classifiers.py` already embeds through Ollama for the prober's
baseline. This lifts that into something the graph can use without importing a
classifier, and keeps the one property that matters: **an unreachable backend
raises rather than returning nothing.** A retrieval layer that silently returns
no passages when Ollama is down would make a stopped service look exactly like a
question the shelf cannot answer.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

DEFAULT_MODEL = "mxbai-embed-large"
DEFAULT_HOST = "http://localhost:11434"

# `mxbai-embed-large` returns 1024 floats. Named because the vector index has to
# be created with the right width and a mismatch is a confusing error much later.
DIMENSIONS = 1024


class EmbeddingUnavailable(RuntimeError):
    """The embedding backend could not be reached, or gave nothing usable."""


def embed(text: str, model: str = DEFAULT_MODEL, host: str = DEFAULT_HOST) -> list[float]:
    """One vector for one string.

    Raises rather than returning `None` or `[]`: every caller here is storing or
    searching, and both are meaningless with a missing vector. The empty case
    must not be able to masquerade as a real answer (L-046).
    """
    return embed_all([text], model=model, host=host)[0]


def embed_all(
    texts: list[str], model: str = DEFAULT_MODEL, host: str = DEFAULT_HOST
) -> list[list[float]]:
    """Vectors for many strings in one request.

    Batched because 607 passages at one HTTP round trip each is a minute of
    latency for no reason, and the shelf is only going to grow.
    """
    if not texts:
        return []
    body = json.dumps({"model": model, "input": texts}).encode("utf-8")
    request = urllib.request.Request(
        f"{host}/api/embed", data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = json.loads(response.read())
    except (urllib.error.URLError, OSError, ValueError) as error:
        raise EmbeddingUnavailable(f"{host}: {error}") from error

    vectors = payload.get("embeddings") or []
    if len(vectors) != len(texts):
        raise EmbeddingUnavailable(
            f"asked for {len(texts)} embeddings and got {len(vectors)}"
        )
    return vectors
