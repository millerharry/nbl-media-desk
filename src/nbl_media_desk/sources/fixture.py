"""Committed synthetic games stored as canonical JSON (tests, CI and public evals)."""

import re
from pathlib import Path

from pydantic import ValidationError

from nbl_media_desk.models import Game
from nbl_media_desk.sources.base import GameNotFoundError, SourceError

_GAME_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


class FixtureSource:
    """Reads `<root>/<game_id>/game.json`, already in the canonical shape."""

    name = "fixture"

    def __init__(self, root: Path) -> None:
        self.root = root

    def get_game(self, game_id: str) -> Game:
        path = self.root / game_id / "game.json"
        if not _GAME_ID.fullmatch(game_id) or not path.is_file():
            msg = f"no fixture game {game_id!r} under {self.root}"
            raise GameNotFoundError(msg)
        try:
            return Game.model_validate_json(path.read_text(encoding="utf-8"))
        except ValidationError as exc:
            msg = f"fixture {game_id!r} is invalid: {exc}"
            raise SourceError(msg) from exc

    def list_games(self) -> list[str]:
        return sorted(p.parent.name for p in self.root.glob("*/game.json"))
