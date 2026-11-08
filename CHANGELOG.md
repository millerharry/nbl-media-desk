# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Canonical game model (`nbl_media_desk.models`) with strict validation: shooting must add up to points, players to the team total, periods to the final score, events in game-time order.
- Source adapters: `FixtureSource` for committed synthetic games and `LiveStatsSource` for the NBL's FIBA LiveStats feed, with a git-ignored, atomic local cache. Finished games are fetched once.
- Deterministic fact engine with numbered facts: result, periods and breaks, comebacks, lead changes, ties, largest leads, scoring runs, player lines, game and team leaders, double- and triple-doubles, and team totals.
- `nbl-desk facts <game>` CLI command (`--source fixture|livestats`, `--json`).
- Live contract test (`pytest --run-live`) checking computed flow stats against the NBL feed's official totals.
- Golden expectations now list the exact facts behind each must-mention storyline.
- Design document, data-source research and ADRs 0000–0009.
- Project scaffold: uv, ruff, mypy (strict), pytest, pre-commit, GitHub Actions CI with secret scanning.
- Synthetic golden game `golden-001` with must-mention storylines and fact-checker mutation cases.
- Guard script enforcing "no third-party game data in the repo" (ADR-0006).
