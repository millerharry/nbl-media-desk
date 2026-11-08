from pathlib import Path

import pytest

from nbl_media_desk.sources import FixtureSource, GameNotFoundError, GameSource, SourceError
from tests.conftest import GOLDEN


def test_loads_golden_game() -> None:
    game = FixtureSource(GOLDEN).get_game("game-001")
    assert game.home.final_score == 94


def test_satisfies_protocol() -> None:
    assert isinstance(FixtureSource(GOLDEN), GameSource)


@pytest.mark.parametrize("game_id", ["missing", "../game-001", "game-001/../game-001"])
def test_missing_or_escaping_ids_not_found(game_id: str) -> None:
    with pytest.raises(GameNotFoundError):
        FixtureSource(GOLDEN).get_game(game_id)


def test_invalid_fixture_raises_source_error(tmp_path: Path) -> None:
    (tmp_path / "bad").mkdir()
    (tmp_path / "bad" / "game.json").write_text('{"game_id": "bad"}')
    with pytest.raises(SourceError, match="invalid"):
        FixtureSource(tmp_path).get_game("bad")


def test_list_games() -> None:
    assert "game-001" in FixtureSource(GOLDEN).list_games()
