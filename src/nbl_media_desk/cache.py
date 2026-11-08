"""Local, git-ignored cache for raw third-party feeds (ADR-0006).

A finished game is fetched once and then served from disk, which keeps us polite to the
upstream feed and makes runs reproducible.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

_SAFE_KEY = re.compile(r"^[A-Za-z0-9_.-]+$")


class GameCache:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, source: str, game_id: str) -> Path:
        for part in (source, game_id):
            if not _SAFE_KEY.fullmatch(part) or part in {".", ".."}:
                msg = f"unsafe cache key: {part!r}"
                raise ValueError(msg)
        return self.root / source / f"{game_id}.json"

    def get(self, source: str, game_id: str) -> dict[str, Any] | None:
        path = self._path(source, game_id)
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            msg = f"cached payload for {source}/{game_id} is not a JSON object"
            raise ValueError(msg)
        return data

    def put(self, source: str, game_id: str, payload: Mapping[str, Any]) -> Path:
        """Write atomically so a crash never leaves a half-written file behind."""
        path = self._path(source, game_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh)
            Path(tmp).replace(path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
        return path
