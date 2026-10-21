---
status: proposed
date: 2026-10-14
---

# Separate dev, CI, staging and production environments

## Context and Problem Statement

Changes must never go straight to production. At the same time the project
runs on a small budget: a laptop for development and a home server for
hosting. Which environments are needed, and how does a change move through them?

## Considered Options

- Dev, CI, staging and production, promoted by merge and release tag
- Dev, CI and production only
- Deploy every merge to production

## Decision Outcome

Chosen option: "Dev, CI, staging and production", because every change is
tested in a production-like environment before it reaches real users.

| Environment | Where | How a change gets there |
|---|---|---|
| Dev | Laptop, Docker Compose, set up with one command | local work |
| CI | GitHub Actions | every pull request: lint, unit and integration tests (Testcontainers), build |
| Staging | Home server, own VM with k3s and database, behind a login | automatically after merge to `main`, then end-to-end tests with Playwright |
| Production | Home server, own VM | only from a release tag with manual approval (GitHub Environments) |

### Consequences

- Good, because production runs the same image that was tested on staging.
- Good, because branch protection blocks merges with failing checks.
- Good, because deployment uses GitOps (pull), so no self-hosted runner is attached to the public repository.
- Bad, because staging and production need their own VMs, which cost RAM on the home server.
- Bad, because the full setup is only reachable once the home server exists. Until then the MVP runs in dev only.
