"""NBL games from the public FIBA LiveStats (Genius Sports) JSON feed.

The feed is undocumented and unlicensed for redistribution (see docs/research/data-sources.md),
so:

* raw payloads are only ever stored in the local, git-ignored cache (ADR-0006);
* a finished game is fetched once; in-progress games are not cached;
* the mapping fails loudly on anything unexpected rather than guessing.

Feed conventions relied on here (verified against a 2026 NBL game):

* ``tm["1"]`` is the first-listed (home) team and ``tm["2"]`` the second (away) team.
* Period scores are ``p1_score``, ``p2_score``, ... and are ``null`` for unplayed periods.
* ``pbp`` is newest-first, and ``actionNumber`` is entry order, not game-time order: late
  corrections (e.g. an assist added afterwards) carry the original play's clock and score.
  Events are therefore sorted by period, then game clock, then ``actionNumber``.
* Player minutes are ``"MM:SS"`` strings, and the seconds can read ``60``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

import httpx
from pydantic import ValidationError

from nbl_media_desk.cache import GameCache
from nbl_media_desk.models import Game, PlayerLine, PlayEvent, Side, TeamGame
from nbl_media_desk.sources.base import GameNotFoundError, SourceError

DEFAULT_BASE_URL = "https://fibalivestats.dcd.shared.geniussports.com"
_GAME_ID = re.compile(r"^\d{1,12}$")
_MAX_PERIODS = 20
_TEAM_KEYS = {Side.HOME: "1", Side.AWAY: "2"}
_TNO_TO_SIDE = {1: Side.HOME, 2: Side.AWAY}

RawGame = Mapping[str, Any]


class LiveStatsSource:
    name = "livestats"

    def __init__(
        self,
        cache: GameCache,
        *,
        client: httpx.Client | None = None,
        base_url: str = DEFAULT_BASE_URL,
        user_agent: str = "nbl-media-desk",
        competition: str = "NBL",
        season: str = "",
    ) -> None:
        self.cache = cache
        self._client = client or httpx.Client(
            timeout=15.0, headers={"User-Agent": user_agent}, follow_redirects=False
        )
        self.base_url = base_url.rstrip("/")
        self.competition = competition
        self.season = season

    def get_game(self, game_id: str) -> Game:
        if not _GAME_ID.fullmatch(game_id):
            msg = f"LiveStats game IDs are numeric, got {game_id!r}"
            raise GameNotFoundError(msg)
        raw = self.cache.get(self.name, game_id)
        if raw is None:
            raw = self._fetch(game_id)
            if is_final_raw(raw):
                self.cache.put(self.name, game_id, raw)
        return map_game(raw, game_id=game_id, competition=self.competition, season=self.season)

    def _fetch(self, game_id: str) -> dict[str, Any]:
        url = f"{self.base_url}/data/{game_id}/data.json"
        try:
            response = self._client.get(url)
        except httpx.HTTPError as exc:
            msg = f"could not reach LiveStats for game {game_id}: {exc}"
            raise SourceError(msg) from exc
        if response.status_code == httpx.codes.NOT_FOUND:
            msg = f"LiveStats has no game {game_id}"
            raise GameNotFoundError(msg)
        if response.status_code != httpx.codes.OK:
            msg = f"LiveStats returned HTTP {response.status_code} for game {game_id}"
            raise SourceError(msg)
        try:
            data = response.json()
        except ValueError as exc:
            msg = f"LiveStats returned invalid JSON for game {game_id}"
            raise SourceError(msg) from exc
        if not isinstance(data, dict):
            msg = f"LiveStats returned a non-object payload for game {game_id}"
            raise SourceError(msg)
        return data


def is_final_raw(raw: RawGame) -> bool:
    return any(
        e.get("actionType") == "game" and e.get("subType") == "end" for e in raw.get("pbp", [])
    )


def parse_minutes(value: object) -> float:
    """Convert ``"MM:SS"`` to decimal minutes. Tolerates the feed's ``"14:60"`` quirk."""
    if value in (None, ""):
        return 0.0
    text = str(value)
    match = re.fullmatch(r"(\d+):(\d{1,2})", text)
    if not match:
        msg = f"unexpected minutes format: {text!r}"
        raise SourceError(msg)
    minutes, seconds = int(match.group(1)), int(match.group(2))
    return round(minutes + seconds / 60, 2)


def _int(value: object) -> int:
    if value in (None, ""):
        return 0
    if isinstance(value, bool) or not isinstance(value, int | str):
        msg = f"expected an integer, got {value!r}"
        raise SourceError(msg)
    return int(value)


def _full_name(record: Mapping[str, Any]) -> str:
    full = f"{record.get('firstName', '')} {record.get('familyName', '')}".strip()
    return full or str(record.get("name", "")).strip()


def _map_player(raw: Mapping[str, Any]) -> PlayerLine:
    return PlayerLine(
        name=_full_name(raw),
        shirt_number=str(raw.get("shirtNumber", "")),
        starter=bool(_int(raw.get("starter"))),
        minutes=parse_minutes(raw.get("sMinutes")),
        points=_int(raw.get("sPoints")),
        field_goals_made=_int(raw.get("sFieldGoalsMade")),
        field_goals_attempted=_int(raw.get("sFieldGoalsAttempted")),
        threes_made=_int(raw.get("sThreePointersMade")),
        threes_attempted=_int(raw.get("sThreePointersAttempted")),
        free_throws_made=_int(raw.get("sFreeThrowsMade")),
        free_throws_attempted=_int(raw.get("sFreeThrowsAttempted")),
        rebounds=_int(raw.get("sReboundsTotal")),
        assists=_int(raw.get("sAssists")),
        steals=_int(raw.get("sSteals")),
        blocks=_int(raw.get("sBlocks")),
        turnovers=_int(raw.get("sTurnovers")),
    )


def _map_team(raw: Mapping[str, Any]) -> TeamGame:
    periods: list[int] = []
    for i in range(1, _MAX_PERIODS + 1):
        value = raw.get(f"p{i}_score")
        if value in (None, ""):
            break
        periods.append(_int(value))
    players = tuple(_map_player(p) for p in raw.get("pl", {}).values())
    return TeamGame(
        name=str(raw["name"]),
        code=str(raw.get("code", "")),
        period_scores=tuple(periods),
        final_score=_int(raw.get("full_score", raw.get("score"))),
        players=players,
    )


def _map_event(raw: Mapping[str, Any]) -> PlayEvent:
    tno = _int(raw.get("tno"))
    player = _full_name(raw) if raw.get("player") else None
    return PlayEvent(
        sequence=_int(raw.get("actionNumber")),
        period=_int(raw.get("period")),
        clock=str(raw.get("gt", "")),
        home_score=_int(raw.get("s1")),
        away_score=_int(raw.get("s2")),
        side=_TNO_TO_SIDE.get(tno),
        player=player or None,
        action=str(raw.get("actionType", "")),
        sub_type=str(raw.get("subType", "")),
        success=bool(_int(raw.get("success"))),
        scoring=bool(_int(raw.get("scoring"))),
    )


def map_game(raw: RawGame, *, game_id: str, competition: str = "NBL", season: str = "") -> Game:
    """Map one raw LiveStats payload to the canonical model, or raise `SourceError`."""
    try:
        teams = raw["tm"]
        events = sorted((_map_event(e) for e in raw.get("pbp", [])), key=lambda e: e.game_time_key)
        attendance = raw.get("attendance")
        return Game(
            game_id=game_id,
            source=LiveStatsSource.name,
            synthetic=False,
            competition=competition,
            season=season,
            attendance=_int(attendance) if attendance not in (None, "", 0) else None,
            home=_map_team(teams[_TEAM_KEYS[Side.HOME]]),
            away=_map_team(teams[_TEAM_KEYS[Side.AWAY]]),
            events=tuple(events),
        )
    except (KeyError, TypeError, ValidationError) as exc:
        msg = f"LiveStats game {game_id} does not match the expected shape: {exc}"
        raise SourceError(msg) from exc
