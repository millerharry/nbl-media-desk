# 0007. Per-stage run records as the observability backbone

- **Status:** Accepted
- **Date:** 2026-11-08

## Context
The job ad's "monitoring agent performance" means reliability, latency and error rates. We also need cost and fact-check metrics for evals and the dashboard.

## Decision
Each pipeline stage writes a run record (SQLite by default) with run ID, game ID, stage, model, token usage including cache reads, cost, latency, verdict counts and errors. Logs are structured JSON keyed by run ID. OpenTelemetry export is optional. The dashboard reads only run records.

## Consequences
One source of truth for dashboard, evals and alerts. SQLite is enough for one user; Postgres is a later swap.

## Alternatives considered
- **Hosted LLM observability SaaS:** quicker dashboards, but adds a vendor and hides the engineering this project should show.
