# 0004. Independent extraction plus deterministic verification

- **Status:** Accepted
- **Date:** 2026-11-08

## Context
Citations from the writer can be wrong ("F-014" cited next to the wrong value). An LLM asked "is this text consistent with these facts?" tends to agree and is hard to measure.

## Decision
1. A separate model call extracts typed claims (`subject, metric, value, scope, comparator, span`) from the **final text only**, without seeing the fact sheet.
2. Code verifies each claim against the fact sheet and canonical model, with explicit normalisation and tolerances.
3. A coverage check makes sure every number in the text belongs to a verified claim.
4. Verdicts: `verified`, `contradicted`, `unsupported`, `opinion`. Contradicted or unsupported claims block the piece. Up to two repair rounds, then flag to a human.
5. Recall and precision are measured with a mutation-testing eval (injected errors).

## Consequences
- Measurable, explainable fact-checking with a clear audit trail per claim.
- Extra latency and cost for one cheap model call per piece.
- Natural-language edge cases ("doubled their tally") need normaliser work, tracked through the mutation suite.

## Alternatives considered
- **LLM-as-judge only:** cheap to build, unmeasurable failure modes, agreement bias.
- **Trust the writer's citations:** misses value mismatches.
