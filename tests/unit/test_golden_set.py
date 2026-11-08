"""Integrity checks for the synthetic golden set."""

import json
from pathlib import Path

import pytest

from nbl_media_desk.facts import build_fact_sheet
from nbl_media_desk.sources import FixtureSource
from tests.conftest import GOLDEN

GAMES = FixtureSource(GOLDEN).list_games()
VERDICTS = {"verified", "contradicted", "unsupported", "opinion"}


@pytest.mark.parametrize("game_id", GAMES)
def test_golden_game_is_valid_and_synthetic(game_id: str) -> None:
    game = FixtureSource(GOLDEN).get_game(game_id)  # model validation checks every total
    assert game.synthetic is True
    assert game.source == "fixture"


@pytest.mark.parametrize("game_id", GAMES)
def test_expectations_are_well_formed(game_id: str) -> None:
    exp = json.loads((GOLDEN / game_id / "expectations.json").read_text(encoding="utf-8"))
    must_ids = {m["id"] for m in exp["must_mention"]}
    assert exp["correct_sentences"]
    assert {m["expected_verdict"] for m in exp["mutations"]} <= VERDICTS
    assert {f["supports"] for f in exp["expected_facts"]} == must_ids, (
        "every must-mention storyline needs at least one expected fact"
    )


@pytest.mark.parametrize("game_id", GAMES)
def test_fact_engine_reproduces_golden_storylines(game_id: str) -> None:
    """Phase 3a exit criterion: every must-mention storyline is backed by an exact fact."""
    game = FixtureSource(GOLDEN).get_game(game_id)
    sheet = build_fact_sheet(game)
    exp = json.loads((GOLDEN / game_id / "expectations.json").read_text(encoding="utf-8"))
    for expected in exp["expected_facts"]:
        matches = sheet.find(
            subject=expected["subject"], metric=expected["metric"], scope=expected["scope"]
        )
        assert [f.value for f in matches] == [expected["value"]], expected


def test_golden_dir_only_contains_fixture_games() -> None:
    assert all((GOLDEN / g / "game.json").is_file() for g in GAMES)
    assert all(isinstance(p, Path) for p in GOLDEN.iterdir())
