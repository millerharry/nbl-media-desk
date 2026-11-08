# 0008. Open-source licence

- **Status:** Accepted
- **Date:** 2026-11-08

## Context
The project is a public portfolio piece that may become a product. The licence decides what others (including companies) can do with it, and what the author keeps.

## Decision
**Apache-2.0.** It's as permissive as MIT for users, adds an explicit patent grant and patent-retaliation clause, requires stating changes, and is the common choice for AI and infrastructure projects. It doesn't stop the author building a commercial product or hosted service on top, and it doesn't cover trademarks: the product name stays the author's to control.

## Consequences
Anyone, including competitors, may use and sell derived versions. If keeping a commercial moat matters later, the usual path is open core: keep the core Apache-2.0 and build hosted or premium features (multi-club management, integrations) in a separate private codebase.

## Alternatives considered
- **MIT:** simplest and most familiar; no patent grant.
- **AGPL-3.0:** forces hosted competitors to open their changes, but deters company adoption and contributions.
- **Source-available (BSL, Elastic):** protects a product, but it isn't open source and is weaker as a portfolio signal.
