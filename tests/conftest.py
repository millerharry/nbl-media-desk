"""Shared fixtures. Tests marked `live` (network or Claude API) only run with `--run-live`."""

import json
from pathlib import Path
from typing import Any

import pytest

from nbl_media_desk.models import Game
from nbl_media_desk.sources import FixtureSource

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "evals" / "golden"
LIVESTATS_FIXTURE = ROOT / "tests" / "fixtures" / "livestats" / "synthetic-ot-final.json"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--run-live", action="store_true", help="run tests that hit the network")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-live"):
        return
    skip = pytest.mark.skip(reason="needs --run-live")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip)


@pytest.fixture
def golden_game() -> Game:
    return FixtureSource(GOLDEN).get_game("game-001")


@pytest.fixture
def golden_expectations() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(
        (GOLDEN / "game-001" / "expectations.json").read_text(encoding="utf-8")
    )
    return data


@pytest.fixture
def livestats_raw() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(LIVESTATS_FIXTURE.read_text(encoding="utf-8"))
    return data
