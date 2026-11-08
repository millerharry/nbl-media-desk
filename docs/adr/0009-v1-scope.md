# 0009. v1 scope

- **Status:** Accepted
- **Date:** 2026-11-08

## Context
The full vision (watcher, n8n, Slack, dashboard) is large. The core value, and the hardest part, is grounded content: facts, agent and fact-checker.

## Decision
Milestone v0.1 is the **core loop on one recent real game plus the synthetic golden set**: canonical model and adapters, fact engine, MCP server, newsroom agent, fact-checker, and the eval harness, run from the CLI. Then v0.2 adds the watcher, n8n workflow and Slack approval. v0.3 adds the dashboard. v1.0 adds a demo GIF, docs polish and a tagged release.

## Consequences
A demoable, defensible core early. Integrations come after the hard part is proven.

## Alternatives considered
- **End to end first with thin stages:** looks complete sooner, but the quality of each stage is unproven.
