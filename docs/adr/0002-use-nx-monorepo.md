---
status: proposed
date: 2026-10-14
---

# Use an Nx monorepo

## Context and Problem Statement

The project will contain a Next.js web app, a NestJS API, a Python import job
and later an Angular dashboard and shared libraries. How should this code be
organised so that it can share types and tooling and still be built and tested
separately?

## Considered Options

- Nx monorepo
- Turborepo monorepo
- pnpm workspaces without a build system
- One repository per app

## Decision Outcome

Chosen option: "Nx monorepo", because it supports Next.js, NestJS and Angular
with official plugins and only builds and tests what a change affects.

### Consequences

- Good, because shared code (for example API types) lives in libraries instead of being copied.
- Good, because one pull request can change web app and API together.
- Good, because `nx affected` keeps CI fast as the repo grows.
- Bad, because Nx adds its own concepts and configuration to learn.
- Bad, because the Python import job is not a first-class Nx project and needs custom targets.

## Pros and Cons of the Options

### Turborepo

- Good, because it is simple and fast.
- Bad, because it has no generators or plugins for Angular and NestJS.

### pnpm workspaces only

- Good, because there is nothing extra to learn.
- Bad, because caching and "only test what changed" would have to be built by hand.

### One repository per app

- Good, because each app is fully independent.
- Bad, because shared types and cross-cutting changes need several pull requests.
