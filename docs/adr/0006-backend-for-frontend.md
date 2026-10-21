---
status: proposed
date: 2026-10-19
---

# Browser talks only to Next.js (backend for frontend)

## Context and Problem Statement

The web app needs data from the NestJS API. Should the browser call the API
directly, or should all requests go through the Next.js server?

## Considered Options

- Browser calls only Next.js, the API stays internal (backend for frontend)
- Browser calls the NestJS API directly

## Decision Outcome

Chosen option: "Backend for frontend", because only one service is exposed to
the internet and the API can stay private.

### Consequences

- Good, because the attack surface is smaller.
- Good, because no CORS configuration is needed.
- Good, because access tokens can stay on the server once accounts are added.
- Bad, because every request takes one extra hop through Next.js.

## More Information

Exception: the Angular dashboard for data imports (planned later) may call the
API directly, behind a login.
