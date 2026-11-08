import pytest

from nbl_media_desk import __version__
from nbl_media_desk.cli import main


def test_main_without_args_succeeds() -> None:
    assert main([]) == 0


def test_version_flag_prints_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out
