---
status: proposed
date: 2026-10-21
---

# Record architecture decisions in MADR format

## Context and Problem Statement

Gemeindespiegel combines several apps and languages (Next.js, NestJS, Python).
Many choices are made before any code exists. Without a written record, the
reasons behind them get lost and later changes risk repeating old discussions.

## Considered Options

- MADR (Markdown Any Decision Records)
- Nygard format (Context, Decision, Consequences)
- No formal records, decisions only in the README

## Decision Outcome

Chosen option: "MADR", because its "Considered Options" section makes the
trade-offs visible, not only the result.

### Consequences

- Good, because every decision can be traced back to its reasons.
- Good, because the records live next to the code and are reviewed in pull requests.
- Bad, because each record takes a bit more writing than the Nygard format.

## More Information

- Records are numbered and never deleted. A changed decision gets a new record
  that supersedes the old one.
- New records start as `proposed` and become `accepted` once confirmed.
- Format: <https://adr.github.io/madr/>
