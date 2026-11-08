# Evals

Evals measure what matters for this project: **is every published claim true, and is the content worth publishing?** See `docs/design.md` §8 for the full strategy.

## Layout

```
evals/
  golden/<game>/game.json          synthetic game in the canonical shape (safe to commit, ADR-0006)
  golden/<game>/expectations.json  must-mention storylines, known-correct sentences, injected errors
  results/                         run outputs (git-ignored)
```

## Suites (status)

| Suite | Status |
|---|---|
| Golden data integrity (scores add up) | ✅ runs in CI (`tests/unit/test_golden_set.py`) |
| Fact-checker recall on `mutations` | Phase 3d |
| Fact-checker precision on `correct_sentences` | Phase 3d |
| End-to-end groundedness | Phase 3e |
| Content-quality rubric (LLM judge, calibrated) | Phase 3e |

## Adding a golden game

1. Copy `golden/game-001/`, use fictional teams and players only.
2. Make every total add up (the integrity test enforces this).
3. Add at least one mutation for each `kind` you want covered.
