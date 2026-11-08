import json

import pytest

from nbl_media_desk import __version__
from nbl_media_desk.cli import main
from tests.conftest import GOLDEN


def test_main_without_args_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "facts" in capsys.readouterr().out


def test_version_flag_prints_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_facts_from_fixture(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["facts", "game-001", "--fixtures-dir", str(GOLDEN)]) == 0
    out = capsys.readouterr().out
    assert "F-003 | Harbour City Hawks beat Inland Rivers Rams 94-88 at home." in out


def test_facts_as_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["facts", "game-001", "--fixtures-dir", str(GOLDEN), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["game_id"] == "golden-001"
    assert data["facts"][0]["id"] == "F-001"


def test_facts_unknown_game(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["facts", "nope", "--fixtures-dir", str(GOLDEN)]) == 1
    assert "error:" in capsys.readouterr().err
