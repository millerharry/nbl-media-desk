# 0005. Human approval before anything is published

- **Status:** Accepted
- **Date:** 2026-11-08

## Context
Content goes out under a club's name about real people. Even a verified draft can be badly judged in tone or context.

## Decision
The system produces drafts only. Delivery is a Slack message with Approve, Edit and Reject actions (through n8n). There is no code path that posts to social platforms. Every decision is logged in the run records.

## Consequences
Safe by default, and the approval rate becomes a quality metric. Publishing stays a manual step.

## Alternatives considered
- **Auto-publish when the fact check passes:** faster, but unacceptable risk for v1.
