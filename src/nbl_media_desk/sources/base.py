"""The adapter contract every game source implements (ADR-0001)."""

from typing import Protocol, runtime_checkable

from nbl_media_desk.models import Game


class SourceError(RuntimeError):
    """The source returned data we could not map into the canonical model."""


class GameNotFoundError(SourceError):
    """The source has no game with this ID."""


@runtime_checkable
class GameSource(Protocol):
    name: str

    def get_game(self, game_id: str) -> Game:
        """Return the game in canonical form, or raise `GameNotFoundError` / `SourceError`."""
        ...
