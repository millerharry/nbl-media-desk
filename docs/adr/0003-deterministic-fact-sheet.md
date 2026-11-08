# 0003. Deterministic fact sheet; LLMs never compute numbers

- **Status:** Accepted
- **Date:** 2026-11-08

## Context
LLMs are good at choosing and phrasing stories and unreliable at arithmetic over large tables (sums, percentages, runs, "first since" comparisons). Wrong numbers are the failure that matters most to a club.

## Decision
A pure-Python **fact engine** computes every number the writer may use and emits a `FactSheet` of facts with stable IDs (`F-001`, ...), each with subject, metric, value, scope and a canonical sentence. The writer may only state numbers that appear in the fact sheet and must cite fact IDs.

## Consequences
- Numbers are unit-testable and correct by construction.
- Story richness is limited to what the fact engine computes, so new storyline types need new fact generators (intentional, and well-tested).
- The fact sheet is also a useful product on its own (exposed through MCP).

## Alternatives considered
- **Let the model compute from raw JSON, then check:** shifts work to the checker and raises the failure rate.
- **Code-execution tool for the model:** flexible, but harder to test and audit than a fixed engine.
