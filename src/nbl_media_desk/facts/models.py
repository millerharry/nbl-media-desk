"""Fact sheet types (ADR-0003).

A fact is one checkable statement about a game, with a stable ID the writer must cite and the
fact-checker can verify against. Facts are produced only by deterministic code.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

FactValue = bool | int | float | str
SubjectType = Literal["game", "team", "player"]


class FactCategory(StrEnum):
    RESULT = "result"
    PERIOD = "period"
    FLOW = "flow"
    PLAYER = "player"
    LEADER = "leader"
    MILESTONE = "milestone"
    TEAM = "team"


class FactDraft(BaseModel):
    """A fact before it is numbered. Generators return these."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    category: FactCategory
    subject_type: SubjectType
    subject: str = Field(min_length=1)
    team: str | None = None
    metric: str = Field(min_length=1)
    value: FactValue
    scope: str = "game"
    text: str = Field(min_length=1)


class Fact(FactDraft):
    id: str = Field(pattern=r"^F-\d{3,}$")


class FactSheet(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    game_id: str
    facts: tuple[Fact, ...]

    def by_id(self, fact_id: str) -> Fact | None:
        return next((f for f in self.facts if f.id == fact_id), None)

    def find(
        self,
        *,
        subject: str | None = None,
        metric: str | None = None,
        scope: str | None = None,
        team: str | None = None,
        category: FactCategory | None = None,
    ) -> list[Fact]:
        """Return facts matching every filter that is given."""
        return [
            f
            for f in self.facts
            if (subject is None or f.subject == subject)
            and (metric is None or f.metric == metric)
            and (scope is None or f.scope == scope)
            and (team is None or f.team == team)
            and (category is None or f.category == category)
        ]

    def to_prompt_lines(self) -> str:
        """Compact, stable rendering for an LLM prompt: one fact per line."""
        return "\n".join(f"{f.id} | {f.text}" for f in self.facts)
