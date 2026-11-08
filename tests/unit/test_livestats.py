import copy
from pathlib import Path
from typing import Any

import httpx
import pytest

from nbl_media_desk.cache import GameCache
from nbl_media_desk.sources import GameNotFoundError, GameSource, LiveStatsSource, SourceError
from nbl_media_desk.sources.livestats import is_final_raw, map_game, parse_minutes


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("30:15", 30.25), ("14:60", 15.0), ("0:00", 0.0), ("", 0.0), (None, 0.0), ("5:3", 5.05)],
)
def test_parse_minutes(raw: object, expected: float) -> None:
    assert parse_minutes(raw) == expected


def test_parse_minutes_rejects_garbage() -> None:
    with pytest.raises(SourceError):
        parse_minutes("thirty")


def test_maps_teams_players_and_overtime(livestats_raw: dict[str, Any]) -> None:
    game = map_game(livestats_raw, game_id="900001")
    assert game.home.name == "Coastline Comets"
    assert game.away.code == "VAL"
    assert game.home.period_scores == (5, 2, 0, 3, 3)
    assert game.periods == 5
    assert game.attendance == 1200
    assert game.synthetic is False
    mia = game.home.player("Mia Park")
    assert mia is not None
    assert (mia.points, mia.minutes, mia.threes_made) == (9, 15.0, 2)
    zoe = game.home.player("Zoe Hart")
    assert zoe is not None
    assert not zoe.played


def test_events_sorted_into_game_time_with_late_correction(livestats_raw: dict[str, Any]) -> None:
    game = map_game(livestats_raw, game_id="900001")
    sequences = [e.sequence for e in game.events]
    assert sequences == [1, 2, 3, 9, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15]
    assert game.events[0].player == "Ava Stone"
    assert game.events[-1].action == "game"
    assert game.is_final


def test_shape_change_raises_source_error(livestats_raw: dict[str, Any]) -> None:
    broken = copy.deepcopy(livestats_raw)
    del broken["tm"]["2"]
    with pytest.raises(SourceError, match="expected shape"):
        map_game(broken, game_id="1")


def test_inconsistent_totals_raise_source_error(livestats_raw: dict[str, Any]) -> None:
    broken = copy.deepcopy(livestats_raw)
    broken["tm"]["1"]["full_score"] = 99
    with pytest.raises(SourceError):
        map_game(broken, game_id="1")


def test_non_integer_stat_raises(livestats_raw: dict[str, Any]) -> None:
    broken = copy.deepcopy(livestats_raw)
    broken["tm"]["1"]["pl"]["1"]["sPoints"] = 4.5
    with pytest.raises(SourceError, match="integer"):
        map_game(broken, game_id="1")


# --- fetching and caching --------------------------------------------------------------------


def make_source(tmp_path: Path, handler: Any, calls: list[str] | None = None) -> LiveStatsSource:
    def wrapped(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append(str(request.url))
        response: httpx.Response = handler(request)
        return response

    client = httpx.Client(transport=httpx.MockTransport(wrapped))
    return LiveStatsSource(GameCache(tmp_path), client=client, base_url="https://feed.test")


def test_fetches_and_caches_final_game(tmp_path: Path, livestats_raw: dict[str, Any]) -> None:
    calls: list[str] = []
    source = make_source(tmp_path, lambda _: httpx.Response(200, json=livestats_raw), calls)
    assert isinstance(source, GameSource)
    first = source.get_game("900001")
    second = source.get_game("900001")
    assert first == second
    assert calls == ["https://feed.test/data/900001/data.json"]
    assert (tmp_path / "livestats" / "900001.json").is_file()


def test_in_progress_game_not_cached(tmp_path: Path, livestats_raw: dict[str, Any]) -> None:
    live = copy.deepcopy(livestats_raw)
    live["pbp"] = [e for e in live["pbp"] if e["actionType"] != "game"]
    assert not is_final_raw(live)
    calls: list[str] = []
    source = make_source(tmp_path, lambda _: httpx.Response(200, json=live), calls)
    source.get_game("900001")
    source.get_game("900001")
    assert len(calls) == 2
    assert not (tmp_path / "livestats").exists()


@pytest.mark.parametrize(
    ("status", "error"), [(404, GameNotFoundError), (500, SourceError), (403, SourceError)]
)
def test_http_errors(tmp_path: Path, status: int, error: type[Exception]) -> None:
    source = make_source(tmp_path, lambda _: httpx.Response(status))
    with pytest.raises(error):
        source.get_game("1")


def test_invalid_json_raises(tmp_path: Path) -> None:
    source = make_source(tmp_path, lambda _: httpx.Response(200, text="<html>"))
    with pytest.raises(SourceError, match="invalid JSON"):
        source.get_game("1")


def test_non_object_json_raises(tmp_path: Path) -> None:
    source = make_source(tmp_path, lambda _: httpx.Response(200, json=[1]))
    with pytest.raises(SourceError, match="non-object"):
        source.get_game("1")


def test_network_error_raises_source_error(tmp_path: Path) -> None:
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down", request=request)

    with pytest.raises(SourceError, match="could not reach"):
        make_source(tmp_path, boom).get_game("1")


@pytest.mark.parametrize("game_id", ["abc", "../1", "1/2", ""])
def test_non_numeric_ids_rejected_without_network(tmp_path: Path, game_id: str) -> None:
    calls: list[str] = []
    source = make_source(tmp_path, lambda _: httpx.Response(200, json={}), calls)
    with pytest.raises(GameNotFoundError):
        source.get_game(game_id)
    assert calls == []


def test_serves_cache_without_network(tmp_path: Path, livestats_raw: dict[str, Any]) -> None:
    GameCache(tmp_path).put("livestats", "900001", livestats_raw)

    def no_network(request: httpx.Request) -> httpx.Response:
        raise AssertionError("network must not be used")

    game = make_source(tmp_path, no_network).get_game("900001")
    assert game.home.final_score == 13
