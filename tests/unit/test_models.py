from typing import Any

import pytest
from pydantic import ValidationError

from nbl_media_desk.models import Game, PlayerLine, PlayEvent, Side, TeamGame


def line(**overrides: Any) -> PlayerLine:
    base: dict[str, Any] = {
        "name": "Test Player",
        "shirt_number": "1",
        "starter": True,
        "minutes": 30.0,
        "points": 9,
        "field_goals_made": 3,
        "field_goals_attempted": 6,
        "threes_made": 1,
        "threes_attempted": 2,
        "free_throws_made": 2,
        "free_throws_attempted": 2,
        "rebounds": 4,
        "assists": 3,
        "steals": 1,
        "blocks": 0,
        "turnovers": 2,
    }
    return PlayerLine(**(base | overrides))


def team(name: str = "Team A", periods: tuple[int, ...] = (2, 3, 2, 2)) -> TeamGame:
    return TeamGame(
        name=name, code=name[:3].upper(), period_scores=periods, final_score=9, players=(line(),)
    )


def test_points_must_match_shooting() -> None:
    with pytest.raises(ValidationError, match="implied by shooting"):
        line(points=10)


@pytest.mark.parametrize(
    "overrides",
    [
        {"field_goals_made": 7, "field_goals_attempted": 6, "points": 15},
        {"threes_made": 3, "threes_attempted": 2, "points": 11},
        {"free_throws_made": 3, "free_throws_attempted": 2, "points": 10},
    ],
)
def test_made_cannot_exceed_attempted(overrides: dict[str, Any]) -> None:
    with pytest.raises(ValidationError, match="made"):
        line(**overrides)


def test_threes_cannot_exceed_field_goals() -> None:
    with pytest.raises(ValidationError, match="threes made exceeds"):
        line(field_goals_made=1, field_goals_attempted=6, threes_made=2, points=8)


def test_negative_stats_rejected() -> None:
    with pytest.raises(ValidationError):
        line(rebounds=-1)


def test_period_scores_must_sum_to_final() -> None:
    with pytest.raises(ValidationError, match="period scores sum"):
        TeamGame(name="A", code="A", period_scores=(1, 1, 1, 1), final_score=9, players=(line(),))


def test_player_points_must_sum_to_final() -> None:
    with pytest.raises(ValidationError, match="player points sum"):
        TeamGame(
            name="A",
            code="A",
            period_scores=(3, 3, 3, 3),
            final_score=12,
            players=(line(),),
        )


def test_duplicate_player_names_rejected() -> None:
    p = line(points=0, field_goals_made=0, threes_made=0, free_throws_made=0)
    with pytest.raises(ValidationError, match="duplicate"):
        TeamGame(name="A", code="A", period_scores=(2, 3, 2, 2), final_score=9, players=(line(), p))


def test_models_are_immutable() -> None:
    with pytest.raises(ValidationError):
        line().points = 3  # type: ignore[misc]


def test_unknown_fields_rejected(golden_game: Game) -> None:
    data = golden_game.model_dump()
    data["surprise"] = 1
    with pytest.raises(ValidationError):
        Game.model_validate(data)


def test_periods_must_match_between_teams() -> None:
    with pytest.raises(ValidationError, match="different number of periods"):
        Game(
            game_id="g",
            source="test",
            synthetic=True,
            competition="c",
            season="s",
            home=team(),
            away=team("Team B", (2, 3, 2, 2, 0)),
        )


def event(seq: int, period: int, clock: str, home: int, away: int, **kw: Any) -> PlayEvent:
    defaults: dict[str, Any] = {"action": "2pt", "scoring": True, "success": True}
    return PlayEvent(
        sequence=seq,
        period=period,
        clock=clock,
        home_score=home,
        away_score=away,
        **(defaults | kw),
    )


def game_with(events: tuple[PlayEvent, ...]) -> Game:
    return Game(
        game_id="g",
        source="test",
        synthetic=True,
        competition="c",
        season="s",
        home=team(),
        away=team("Team B"),
        events=events,
    )


def test_events_must_be_in_game_time_order() -> None:
    with pytest.raises(ValidationError, match="game-time order"):
        game_with((event(1, 2, "05:00", 2, 0), event(2, 1, "05:00", 4, 0)))


def test_late_entries_are_ordered_by_clock_not_sequence() -> None:
    # sequence 9 is a late correction for a first-quarter play: valid in game-time order
    game = game_with((event(9, 1, "05:00", 2, 0), event(3, 2, "04:00", 4, 0)))
    assert [e.sequence for e in game.events] == [9, 3]


def test_final_event_score_must_match() -> None:
    with pytest.raises(ValidationError, match="last event score"):
        game_with((event(1, 4, "00:00", 8, 9, action="game", sub_type="end", scoring=False),))


def test_clock_format_validated() -> None:
    with pytest.raises(ValidationError):
        event(1, 1, "5 minutes", 0, 0)


def test_game_helpers(golden_game: Game) -> None:
    assert golden_game.winner is Side.HOME
    assert golden_game.team(Side.AWAY).name == "Inland Rivers Rams"
    assert golden_game.periods == 4
    assert golden_game.is_final  # no events: static data counts as final
    assert Side.HOME.other is Side.AWAY
    assert golden_game.home.player("Jalen Okafor") is not None
    assert golden_game.home.player("Nobody") is None


def test_in_progress_game_is_not_final() -> None:
    game = game_with((event(1, 1, "09:00", 2, 0),))
    assert not game.is_final


def test_tied_game_has_no_winner() -> None:
    game = game_with(())
    assert game.winner is None
