"""Canonical, source-agnostic game model (ADR-0001).

Every adapter maps its raw feed into these types, and everything downstream (fact engine, MCP
server, agent, fact-checker) depends only on them. Validation is strict on purpose: if a feed
changes shape or its totals stop adding up, we want a loud failure at ingest, not a wrong
number in a published recap.
"""

from __future__ import annotations

from datetime import date as Date  # noqa: N812 - avoids shadowing the `date` field below
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Side(StrEnum):
    HOME = "home"
    AWAY = "away"

    @property
    def other(self) -> Side:
        return Side.AWAY if self is Side.HOME else Side.HOME


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class PlayerLine(_Frozen):
    """One player's box-score line for one game."""

    name: str = Field(min_length=1)
    shirt_number: str
    starter: bool
    minutes: float = Field(ge=0)
    points: int = Field(ge=0)
    field_goals_made: int = Field(ge=0)
    field_goals_attempted: int = Field(ge=0)
    threes_made: int = Field(ge=0)
    threes_attempted: int = Field(ge=0)
    free_throws_made: int = Field(ge=0)
    free_throws_attempted: int = Field(ge=0)
    rebounds: int = Field(ge=0)
    assists: int = Field(ge=0)
    steals: int = Field(ge=0)
    blocks: int = Field(ge=0)
    turnovers: int = Field(ge=0)

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        pairs = (
            ("field_goals", self.field_goals_made, self.field_goals_attempted),
            ("threes", self.threes_made, self.threes_attempted),
            ("free_throws", self.free_throws_made, self.free_throws_attempted),
        )
        for label, made, attempted in pairs:
            if made > attempted:
                msg = f"{self.name}: {label} made ({made}) > attempted ({attempted})"
                raise ValueError(msg)
        if self.threes_made > self.field_goals_made:
            msg = f"{self.name}: threes made exceeds field goals made"
            raise ValueError(msg)
        expected = (
            2 * (self.field_goals_made - self.threes_made)
            + 3 * self.threes_made
            + self.free_throws_made
        )
        if self.points != expected:
            msg = f"{self.name}: points {self.points} != {expected} implied by shooting"
            raise ValueError(msg)
        return self

    @property
    def played(self) -> bool:
        return self.minutes > 0


class TeamGame(_Frozen):
    """One team's side of a game. `period_scores` holds Q1-Q4 then any overtimes."""

    name: str = Field(min_length=1)
    code: str = Field(min_length=1)
    period_scores: tuple[int, ...] = Field(min_length=4)
    final_score: int = Field(ge=0)
    players: tuple[PlayerLine, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_totals(self) -> Self:
        if sum(self.period_scores) != self.final_score:
            msg = (
                f"{self.name}: period scores sum to {sum(self.period_scores)}, "
                f"final is {self.final_score}"
            )
            raise ValueError(msg)
        player_points = sum(p.points for p in self.players)
        if player_points != self.final_score:
            msg = f"{self.name}: player points sum to {player_points}, final is {self.final_score}"
            raise ValueError(msg)
        names = [p.name for p in self.players]
        if len(names) != len(set(names)):
            msg = f"{self.name}: duplicate player names"
            raise ValueError(msg)
        return self

    def player(self, name: str) -> PlayerLine | None:
        return next((p for p in self.players if p.name == name), None)


class PlayEvent(_Frozen):
    """One play-by-play event.

    `clock` is the time remaining in the period (``"MM:SS"``). `sequence` is the feed's own
    entry number, which is *not* game-time order: scorers enter corrections late.
    """

    sequence: int = Field(ge=0)
    period: int = Field(ge=1)
    clock: str = Field(pattern=r"^\d{1,2}:\d{2}$")
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)
    side: Side | None = None
    player: str | None = None
    action: str
    sub_type: str = ""
    success: bool = False
    scoring: bool = False

    @property
    def remaining_seconds(self) -> int:
        minutes, seconds = self.clock.split(":")
        return int(minutes) * 60 + int(seconds)

    @property
    def game_time_key(self) -> tuple[int, int, int]:
        """Sort key for true game-time order: period, time elapsed, then entry number."""
        return (self.period, -self.remaining_seconds, self.sequence)


class Game(_Frozen):
    """A finished (or in-progress) game in canonical form."""

    schema_version: int = 1
    game_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    synthetic: bool
    competition: str
    season: str
    date: Date | None = None
    venue: str | None = None
    attendance: int | None = Field(default=None, ge=0)
    home: TeamGame
    away: TeamGame
    events: tuple[PlayEvent, ...] = ()

    @model_validator(mode="after")
    def _check_game(self) -> Self:
        if len(self.home.period_scores) != len(self.away.period_scores):
            msg = "home and away have a different number of periods"
            raise ValueError(msg)
        if self.events:
            keys = [e.game_time_key for e in self.events]
            if keys != sorted(keys):
                msg = "events must be in game-time order (see PlayEvent.game_time_key)"
                raise ValueError(msg)
            last = self.events[-1]
            if self.is_final and (last.home_score, last.away_score) != (
                self.home.final_score,
                self.away.final_score,
            ):
                msg = "last event score does not match the final score"
                raise ValueError(msg)
        return self

    def team(self, side: Side) -> TeamGame:
        return self.home if side is Side.HOME else self.away

    @property
    def periods(self) -> int:
        return len(self.home.period_scores)

    @property
    def is_final(self) -> bool:
        """True when the feed has a game-end event, or when no events exist (static data)."""
        if not self.events:
            return True
        return any(e.action == "game" and e.sub_type == "end" for e in self.events)

    @property
    def winner(self) -> Side | None:
        if self.home.final_score == self.away.final_score:
            return None
        return Side.HOME if self.home.final_score > self.away.final_score else Side.AWAY
