# 0002. Language and agent runtime

- **Status:** Accepted
- **Date:** 2026-11-08

## Context
We need an MCP server, an LLM pipeline with tool use and structured outputs, data wrangling, and an eval harness. Options for the LLM layer: the Anthropic SDK (Messages API with the tool runner and structured outputs), the Claude Agent SDK (the Claude Code harness as a library, with built-in file, shell and web tools), or Managed Agents (Anthropic-hosted loop and sandbox).

## Decision
- **Language: Python 3.12+**, managed with `uv`; Pydantic v2; `ruff` for lint and format; `mypy --strict`; `pytest`.
- **LLM runtime: Anthropic Python SDK** (Messages API), using the tool runner for the storyline step and structured outputs (`output_config.format` / `messages.parse`) for writing and claim extraction.
- **MCP:** the official `mcp` Python SDK for the server. The pipeline uses the same tool functions in process, and external clients (Claude Desktop, Claude Code) connect over stdio.
- Models: `claude-opus-5-5` for writing; `claude-haiku-5-5` or `claude-sonnet-5-5` for extraction, chosen by eval.

## Consequences
- The post-game job is a bounded workflow, not open-ended exploration. The Messages API gives us deterministic control flow, typed outputs, and the smallest attack surface (no shell or filesystem tools).
- Python has the strongest data tooling (`nba_api`, pandas if needed) and first-class MCP and Anthropic SDKs.
- The Claude Agent SDK and Managed Agents stay open as later options (for example a conversational "ask the media desk" mode, or hosted scheduled runs). The MCP server makes that switch cheap.

## Alternatives considered
- **Claude Agent SDK:** great for coding and filesystem agents. Its built-in tools must be locked down for this use, and it adds a harness we don't need for a fixed pipeline.
- **Managed Agents:** hosted and scheduled, but adds platform coupling before the core is proven. Revisit for deployment.
- **TypeScript:** equally good SDKs, weaker data and eval ecosystem for this domain.
