---
status: proposed
date: 2026-10-19
---

# Architecture diagrams as code with LikeC4

## Context and Problem Statement

The architecture should be documented with C4 diagrams that stay up to date
and can later be shown as an interactive overview. Which tool should be used?

## Considered Options

- LikeC4
- Structurizr DSL
- Mermaid C4 diagrams
- Drawn diagrams (for example draw.io)

## Decision Outcome

Chosen option: "LikeC4", because one model produces several views and can be
explored interactively in the browser.

### Consequences

- Good, because diagrams are text files, reviewed and versioned like code.
- Good, because `likec4 validate` catches mistakes in CI.
- Good, because the same model can later feed the public architecture overview.
- Bad, because LikeC4 is younger and less widespread than Structurizr.

## More Information

Only what is decided and will be built is drawn. Further data sources and
people are added in the step that introduces them. The model lives in
`docs/architecture/`.
