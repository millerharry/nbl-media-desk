# CLAUDE.md

Guidance for Claude Code and other agents working in this repo.

- Read `docs/design.md` and `docs/adr/` before changing architecture. A change to an accepted decision needs a new ADR.
- Run `make check` before declaring work done. It must pass: ruff, ruff format, `mypy --strict`, pytest, and the data guard.
- Never commit real game data, logos, or secrets (ADR-0006). Fixtures use fictional teams and players.
- LLMs never compute numbers: add fact generators to the fact engine with unit tests (ADR-0003).
- Default models: `claude-opus-5-5` (writer, judge), `claude-haiku-5-5` (claim extraction). Models are set in `src/nbl_media_desk/config.py`, never hard-coded elsewhere.
- Tests that call the network or the Claude API must be marked `@pytest.mark.live`.
