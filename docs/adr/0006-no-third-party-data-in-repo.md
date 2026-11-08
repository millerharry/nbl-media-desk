# 0006. No third-party game data in the repository

- **Status:** Accepted
- **Date:** 2026-11-08

## Context
No licence was found that allows redistributing NBL or Genius Sports data, and NBA.com data is under the NBA.com Terms of Use. The repo is public.

## Decision
- Never commit raw feed data, derived box scores of real games, or league and club logos.
- Real-game data is fetched on demand into a git-ignored cache (`.cache/`), at most once per finished game, with a descriptive User-Agent and conservative rate limits.
- Tests, CI and public evals use synthetic fixtures only. A CI check rejects large JSON files outside `tests/fixtures/` and `evals/golden/`.

## Consequences
The public eval set is synthetic, so its realism depends on our fixture generator. Real-game evals run locally. Reduced legal risk for an open-source project.

## Alternatives considered
- **Commit a few real games for convenience:** small but real IP risk, and it sets a bad precedent for contributors.
