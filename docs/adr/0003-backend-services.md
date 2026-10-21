---
status: proposed
date: 2026-10-14
---

# Use NestJS as main API and Python for data work

## Context and Problem Statement

The web app needs an API for municipality data, later also for accounts and
saved preferences. Importing and cleaning open data, and later AI features,
fit better in Python, which has the stronger data ecosystem. Which backend
technologies should be used?

## Considered Options

- NestJS as main API, Python for data and AI
- NestJS only
- Python (FastAPI) only
- Next.js route handlers only, no separate API

## Decision Outcome

Chosen option: "NestJS as main API, Python for data and AI", because the main
API stays in TypeScript like the frontends, while data work uses the tools made
for it.

### Consequences

- Good, because the API shares language and types with the web app.
- Good, because NestJS brings structure (modules, dependency injection) that scales with features like auth.
- Good, because Python is used where it is strongest.
- Bad, because two languages mean two toolchains, two test setups and two kinds of Docker images.

## More Information

Updated on 2026-10-19: Python starts as a command-line import job without a web
framework (see [ADR 0007](0007-python-import-job.md)). A FastAPI service is only
added once a web interface for Python code is actually needed.
