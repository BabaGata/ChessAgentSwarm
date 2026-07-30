"""The engine and cache lifecycle, shared by every command.

Extracted in M6. Three CLI commands each opened a cache, opened an engine,
analysed, and closed both — the same sequence written three times, and the least
tested code in the project precisely because it lived in command handlers.

Keeping provenance construction here matters beyond tidiness: the engine name
and depth recorded on a finding must be the ones actually used, and reading them
off the live analyser is the only way to guarantee that.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterator

from chesscoach.analysis.cache import EvalCache
from chesscoach.analysis.engine import StockfishAnalyser
from chesscoach.ingest.pgn import GameRecord, parse_pgn_dir, parse_pgn_file
from chesscoach.profile.models import Provenance


@dataclass(frozen=True)
class CacheStats:
    """How much work the cache saved."""

    hits: int
    lookups: int
    rows: int

    @property
    def hit_rate(self) -> float:
        return self.hits / self.lookups if self.lookups else 0.0


class EngineSession:
    """An analyser and its cache, with the provenance they imply."""

    def __init__(self, analyser, cache: EvalCache | None) -> None:
        self.analyser = analyser
        self.cache = cache
        self._final_stats: CacheStats | None = None

    def provenance(self, corpus_id: str, analysed_at: str | None = None) -> Provenance:
        """Provenance describing the engine and depth actually in use."""
        return Provenance(
            engine=self.analyser.engine_name,
            depth=self.analyser.depth,
            corpus_id=corpus_id,
            analysed_at=analysed_at or date.today().isoformat(),
        )

    def cache_stats(self) -> CacheStats | None:
        """Cache usage, readable after the session has closed.

        Snapshotted on close, because the row count needs a live connection and
        callers naturally report these numbers once the work is finished.
        """
        if self._final_stats is not None:
            return self._final_stats
        if self.cache is None:
            return None
        return CacheStats(
            hits=self.cache.hits,
            lookups=self.cache.hits + self.cache.misses,
            rows=self.cache.size(),
        )


@contextmanager
def engine_session(
    engine_path: Path | str, depth: int, cache_path: Path | str | None = None
) -> Iterator[EngineSession]:
    """Open an engine and cache together, and close both whatever happens."""
    cache = EvalCache(cache_path) if cache_path else None
    analyser = StockfishAnalyser(engine_path, depth=depth, cache=cache)
    session = EngineSession(analyser, cache)
    try:
        yield session
    finally:
        session._final_stats = session.cache_stats()
        analyser.close()
        if cache is not None:
            cache.close()


def load_games(source: Path | str) -> tuple[GameRecord, ...]:
    """Read games from a PGN file or a directory of them."""
    source = Path(source)
    return parse_pgn_dir(source) if source.is_dir() else parse_pgn_file(source)
