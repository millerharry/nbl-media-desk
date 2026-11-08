# Contributing to NBL Media Desk

Thanks for helping! This project aims to be a reference implementation of grounded, fact-checked LLM content generation, so the bar is: **correct, tested, documented.**

## Getting started

Requirements: Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone <your fork>
cd nbl-media-desk
make install      # uv sync + pre-commit hooks
make check        # lint, format check, mypy --strict, tests, data guard
```

Copy `.env.example` to `.env` and add an `ANTHROPIC_API_KEY` only if you're running live agent code. Unit tests never call the API.

## Ground rules

1. **No third-party game data in the repo** ([ADR-0006](docs/adr/0006-no-third-party-data-in-repo.md)). Use fictional teams and players in fixtures and golden games. CI enforces this.
2. **LLMs don't compute numbers** ([ADR-0003](docs/adr/0003-deterministic-fact-sheet.md)). New storyline types start as fact generators with unit tests.
3. **Decisions go in ADRs.** If your change contradicts an accepted ADR, add a new ADR that supersedes it in the same PR.
4. **Prompt changes need eval results.** Paste the before/after summary in the PR.
5. **Never commit secrets.** gitleaks runs in pre-commit and CI.

## Workflow

- Branch from `main`: `feat/…`, `fix/…`, `docs/…`.
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
- Keep PRs small and focused; fill in the PR template.
- Add a line to `CHANGELOG.md` under **Unreleased**.

## Code style

- `ruff` for lint and format, `mypy --strict` for types. Both must pass.
- Public functions have type hints and a docstring explaining *why*, not just *what*.
- Tests live in `tests/unit/`. Anything that hits the network or the Claude API is marked `@pytest.mark.live` and skipped in CI.

## Code of Conduct

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
