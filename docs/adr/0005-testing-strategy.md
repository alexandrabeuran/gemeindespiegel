---
status: proposed
date: 2026-10-18
---

# Testing strategy

## Context and Problem Statement

The project spans React, Angular, NestJS and Python. Which test tools should be
used on which level, and what does CI require before a merge?

## Decision Drivers

- Use the standard tool of each framework where one exists.
- Integration tests should run against a real database, not a mock.
- Accessibility is checked automatically.

## Considered Options

- Framework defaults per app (Vitest, Jest, pytest) plus shared integration and end-to-end tools
- One test runner for all TypeScript code
- End-to-end tests only

## Decision Outcome

Chosen option: "Framework defaults per app", because each app is tested the way
its community expects.

| Level                                            | Tools                                            |
| ------------------------------------------------ | ------------------------------------------------ |
| Unit and component (Next.js, Angular, libraries) | Vitest and Testing Library, API mocking with MSW |
| Unit (NestJS)                                    | Jest                                             |
| Integration                                      | Testcontainers (real PostgreSQL) and Supertest   |
| Python                                           | pytest                                           |
| End-to-end                                       | Playwright with axe for accessibility            |

### Consequences

- Good, because Vitest is the default since Angular 21 and Jest is the default in NestJS.
- Good, because Testcontainers catch problems that mocked databases hide.
- Bad, because two TypeScript test runners mean two configurations.

### Confirmation

CI rule: all tests must pass before a merge. There is no minimum coverage
threshold, because coverage numbers reward quantity over meaningful tests.
