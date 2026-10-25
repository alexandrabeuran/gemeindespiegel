---
status: proposed
date: 2026-10-23
---

# Database access with TypeORM

## Context and Problem Statement

The NestJS API owns the PostgreSQL schema (see
[ADR 0007](0007-python-import-job.md)). It needs a way to describe tables in
TypeScript, to create and change them with versioned migrations, and later to
read data for the endpoints. The Python import job writes into the same tables
with plain SQL. Which library should the API use?

## Considered Options

- TypeORM
- Drizzle ORM
- Prisma
- Plain SQL with `node-postgres` and a separate migration tool

## Decision Outcome

Chosen option: "TypeORM", because it has an official NestJS module
(`@nestjs/typeorm`), is widely used in existing NestJS and enterprise
projects, and its decorator style is close to Angular, which is used later in
this project.

### Consequences

- Good, because NestJS documents it directly, so setup and testing follow the
  official guides.
- Good, because entities with decorators (`@Entity`, `@Column`) read like
  Angular code.
- Good, because migrations are generated from the entities and can be run
  from Nx and CI.
- Bad, because type safety is weaker than in Drizzle or Prisma: some query
  mistakes only show up at runtime, so integration tests against a real
  database are required.
- Bad, because generated migrations can contain unwanted changes, so every
  migration is reviewed as SQL before it is committed.

## More Information

- `synchronize` is always off. The schema changes only through migrations.
- Table and column names are set explicitly in `snake_case`, because the
  Python job writes to them with plain SQL.
- Migrations run with `nx run api:migrate`, also in the Testcontainers
  integration test, so the Python job is always tested against the real
  schema.
- Drizzle was the closest alternative: it is closer to SQL and has stronger
  types, but no official NestJS module.
