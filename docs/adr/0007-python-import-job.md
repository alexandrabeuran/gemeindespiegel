---
status: proposed
date: 2026-10-19
---

# Import open data with a separate Python job

## Context and Problem Statement

Municipality data (BFS register) and electricity tariffs (ElCom) are published
as open data and change at most a few times a year. The data must be mapped to
the current BFS municipality list. Where should this import run?

## Considered Options

- Separate Python command-line job
- Import inside the NestJS API
- Python FastAPI service

## Decision Outcome

Chosen option: "Separate Python command-line job", because the import runs
rarely and needs no web interface, and Python fits data cleaning best.

### Consequences

- Good, because the API only reads and the job only writes, so responsibilities stay clear.
- Good, because the job can be tested on its own with pytest.
- Bad, because the job depends on the database schema owned by the API.
- Bad, because in the MVP the operator has to start the job by hand.

## More Information

- Database migrations belong to the NestJS API. The job never changes the schema.
- In the MVP the job is started manually, for example with `docker compose run importer`.
  A schedule comes with Kubernetes.
- FastAPI is only added when a web interface for Python code is needed
  (see [ADR 0003](0003-backend-services.md)).
