# Security policy

## Supported versions

The project is pre-1.0. Only the latest `main` receives security fixes.

## Reporting a vulnerability

Please **do not open a public issue.** Use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) on this repository. You'll get an acknowledgement within 5 working days and a fix plan within 14.

## Scope

In scope: secret leakage, prompt injection through feed data that changes agent behaviour, bypasses of the fact-check or human-approval gates, unsafe defaults in the MCP server, dependency vulnerabilities.

## Design safeguards

- Secrets only via environment variables; gitleaks in pre-commit and CI.
- The MCP server is read-only; the agent has no shell, filesystem or web tools.
- Feed strings are treated as data, never as instructions.
- Nothing is published without human approval ([ADR-0005](docs/adr/0005-human-approval-before-publish.md)).
