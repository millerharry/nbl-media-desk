# 0001. Canonical game model and source adapters

- **Status:** Accepted
- **Date:** 2026-11-08

## Context
The best data for the project's purpose (NBL games via FIBA LiveStats) is undocumented and unlicensed for reuse, and could change without notice (see `docs/research/data-sources.md`). The NBA fallback (`nba_api`) is fragile in a different way. Tests and public evals need data we can commit.

## Decision
- Define a typed, source-agnostic **canonical game model** (Pydantic v2, strict mode): `Game`, `Team`, `PlayerLine`, `PlayEvent`, `Official`.
- Define a `GameSource` protocol: `get_game(game_id) -> Game`, `list_games(season, ...)`, `is_final(game_id) -> bool`.
- Ship adapters: `FixtureSource` (committed synthetic games), `LiveStatsSource` (NBL, fetch on demand into a git-ignored cache), and later optionally `NbaApiSource`.
- **v1 primary source: NBL via `LiveStatsSource`** for local development and demos, with `FixtureSource` for tests, CI and public evals.
- Everything downstream (fact engine, MCP server, agent, fact-checker) depends only on the canonical model.

## Consequences
- A feed format change breaks one adapter, caught by strict validation and contract tests, not the whole system.
- Adding a league (WNBL, NBL1, NBA) is one adapter.
- Some mapping code and a schema to maintain.

## Alternatives considered
- **Use the LiveStats JSON shape directly:** fastest to start, but couples everything to an undocumented format.
- **NBA first:** more history and a bigger audience, but loses the NBL focus that makes the project relevant, and stats.nba.com blocks cloud IPs.
