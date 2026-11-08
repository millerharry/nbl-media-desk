"""Integrity checks for the synthetic golden set: every total must add up."""

import json
from pathlib import Path
from typing import Any

import pytest

GOLDEN = Path(__file__).resolve().parents[2] / "evals" / "golden"
GAMES = sorted(p for p in GOLDEN.iterdir() if p.is_dir())
VERDICTS = {"verified", "contradicted", "unsupported", "opinion"}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("game_dir", GAMES, ids=lambda p: p.name)
def test_scores_add_up(game_dir: Path) -> None:
    game = _load(game_dir / "game.json")
    assert game["synthetic"] is True
    for side in ("home", "away"):
        team = game[side]
        assert sum(team["quarter_scores"]) == team["final_score"]
        assert sum(p["points"] for p in team["players"]) == team["final_score"]
        for p in team["players"]:
            expected = (
                2 * (p["field_goals_made"] - p["threes_made"])
                + 3 * p["threes_made"]
                + p["free_throws_made"]
            )
            assert p["points"] == expected, p["name"]
            assert p["field_goals_made"] <= p["field_goals_attempted"]
            assert p["threes_made"] <= p["threes_attempted"]
            assert p["free_throws_made"] <= p["free_throws_attempted"]


@pytest.mark.parametrize("game_dir", GAMES, ids=lambda p: p.name)
def test_expectations_are_well_formed(game_dir: Path) -> None:
    exp = _load(game_dir / "expectations.json")
    assert exp["game_id"] == _load(game_dir / "game.json")["game_id"]
    assert exp["must_mention"]
    assert exp["correct_sentences"]
    assert {m["expected_verdict"] for m in exp["mutations"]} <= VERDICTS
