# C3 API

Status: draft, 2026-11-02

## Goal

Make the imported data available over HTTP: a NestJS endpoint that lists
municipalities with search, canton filter, sorting by electricity price and
pagination, described by OpenAPI, tested with Jest and Supertest, shipped as
a container image to GHCR and started together with the database by
Docker Compose. The web app (C4) builds directly on this contract.

## Scope

- `GET /api/municipalities` (details below).
- `GET /api/health`: checks the database connection with `@nestjs/terminus`.
  200 when the database answers, 503 when it does not.
- Errors in one format, RFC 9457 (`application/problem+json`), for
  validation errors (400), unknown year (404), unexpected errors (500) and
  an unavailable database at `/api/health` (503).
  A 500 never contains a stack trace or SQL.
- OpenAPI code-first with `@nestjs/swagger`: DTO classes are the contract.
  Swagger UI at `/api/docs`. An Nx target `api:openapi` writes
  `apps/api/openapi.json`; the file is committed and CI fails if it is out of
  date (C4 generates TypeScript types from it). New ADR 0010
  "Code-first OpenAPI as the API contract".
- Migration (from C2): indexes on the foreign keys
  `municipality.canton_bfs_number` and `tariff.grid_operator_elcom_id`, and
  the PostgreSQL extension `unaccent`. `municipality_price` and
  `tariff.municipality_bfs_number` need no extra index, because the primary
  key of `municipality_price` and the unique constraint of `tariff` both
  start with the municipality.
- The API listens on port 3333 by default (`PORT` overrides it), because
  `web` uses 3000.
- Container image for the API: multi-stage `Dockerfile` on `node:26-slim`.
  The build stage installs with pnpm and builds with Nx. The runtime stage
  contains only the bundle, production dependencies and compiled migrations,
  and runs as a non-root user.
- Migrations run as their own step, never inside the API process
  (no `migrationsRun`). The API image can run them with a separate command,
  so Compose (and later a Kubernetes job) can start them before the API.
- Docker Compose: `docker compose up` starts `db`, then `migrate` (one-off,
  same image), then `api` once `migrate` has finished successfully. The API
  has a healthcheck based on `/api/health`.
- CI: pull requests build both images (API and importer) without pushing.
  On `main`, both are pushed to `ghcr.io` with the tags `sha-<commit>` and
  `latest`.
- Tests:
  - Unit tests (part of `nx test api`) with a mocked repository: query
    validation, defaults, error format, mapping of database rows to the
    response.
  - End-to-end tests with Supertest against a PostgreSQL in Testcontainers
    with the real migrations and a small seed (target `api:test-e2e`, also
    in CI): search, filter, sorting, pagination, health.
- Architecture diagram (LikeC4) shows the API, its database access and the
  images in GHCR.

## Endpoint `GET /api/municipalities`

### Query parameters

| Parameter | Values                                   | Default             |
| --------- | ---------------------------------------- | ------------------- |
| `search`  | text, 1 to 100 characters after trimming | none                |
| `canton`  | two capital letters, e.g. `ZH`           | none (all cantons)  |
| `year`    | tariff year, 1900 to 2100, e.g. `2027`   | newest year in data |
| `sort`    | `name`, `price`                          | `name`              |
| `order`   | `asc`, `desc`                            | `asc`               |
| `limit`   | 1 to 200                                 | 50                  |
| `offset`  | 0 or more                                | 0                   |

### Rules

- Search ignores case and accents and matches anywhere in the name:
  `zurich` finds Zürich, `neuchatel` finds Neuchâtel, `rich` finds Zürich.
  `%` and `_` in the search text are matched literally, not as wildcards.
- `canton` with a valid format but no such canton returns an empty list,
  not an error.
- Every sort has the BFS number as a second key, so pages never overlap or
  skip rows.
- Sorting by price puts municipalities without a price last, for both
  `asc` and `desc`. Municipalities without a price are never hidden.
- `year` within 1900 to 2100 but without data returns 404. Outside that range
  it returns 400, so the value never reaches the `smallint` column. Without
  `year`, the newest year in `municipality_price` is used. If there is no
  price data at all, the response has `year: null` and every `price` is
  `null`.
- Unknown query parameters and invalid values return 400 with the field
  names in the problem details.

### Response (200)

```json
{
  "year": 2027,
  "total": 2110,
  "limit": 50,
  "offset": 0,
  "items": [
    {
      "bfsNumber": 261,
      "name": "Zürich",
      "canton": { "abbreviation": "ZH", "name": "Zürich" },
      "price": { "averageTotal": 27.1234, "multipleOperators": false }
    }
  ]
}
```

- `total` counts all matches, not only the current page.
- `price` is `null` for a municipality without ElCom data in that year.
- `averageTotal` is in Rp./kWh as a JSON number. The database stores
  `numeric(7,4)`; the pg driver returns it as a string, the API converts it.

## Out of scope

- Detail endpoint per municipality with grid operators and price parts
  (later, when the web app needs it).
- Authentication and rate limiting (C8 and later).
- CORS: not needed, because the browser only talks to Next.js (ADR 0006).
- Versioned releases and image tags per version (C10).
- Security scans of the images (Trivy, C10).
- Running the API in Kubernetes (C11).
- Caching of responses.

## Steps

One pull request per step.

- C3.1 Migration: foreign key indexes and `unaccent`, reviewed as SQL.
- C3.2 Municipalities endpoint: query DTO with validation, service with the
  SQL for search, filter, sort and pagination, unit tests, Testcontainers
  e2e tests (`api:test-e2e`, in CI).
- C3.3 Contract and operations: OpenAPI with Swagger UI, `api:openapi` and
  CI check, ADR 0010, problem details for all errors, `/api/health`.
- C3.4 Container: short Docker refresher first (layers, multi-stage builds,
  build cache), then the API `Dockerfile`, Compose services `migrate` and
  `api`, README update.
- C3.5 GHCR: CI builds both images in PRs and pushes them on `main`,
  LikeC4 update, end-to-end check, spec status "done".

## Acceptance criteria

1. `GET /api/municipalities` without parameters returns the first 50
   municipalities sorted by name, `total` 2110 and `year` 2027 (with the
   C2 data).
2. `search=zurich` finds Zürich (BFS 261); `search=neuchatel` finds
   Neuchâtel; `search=%` returns no rows instead of all rows.
3. `canton=ZH` returns only municipalities of canton Zürich; `canton=XX`
   returns an empty list with status 200; `canton=zh1` returns 400.
4. `sort=price&order=desc` and `sort=price&order=asc` both list Siselen
   (BFS 499, no price) after all municipalities with a price.
5. Two municipalities with the same price are always in BFS number order;
   reading all pages with `limit=200` gives each municipality exactly once.
6. `limit=0`, `limit=201`, `offset=-1`, `sort=foo`, `year=99999` and an unknown
   parameter each return 400 as `application/problem+json` naming the field.
7. `year=1999` returns 404 as problem details.
8. `GET /api/health` returns 200 with a running database and 503 as problem
   details when the database is stopped.
9. `apps/api/openapi.json` matches the code; CI fails if it is outdated
   (checked once with a deliberately outdated file).
10. The migration adds the two indexes and `unaccent`; reverting it removes
    them again.
11. `docker compose up` on an empty database starts `db`, runs `migrate` and
    starts `api`; the API container runs as a non-root user and becomes
    healthy.
12. In a pull request, CI builds both images and pushes nothing. After the
    merge to `main`, both images are in GHCR with the tags `sha-<commit>`
    and `latest`.
13. `nx run-many -t lint typecheck test build` passes; `api:test-e2e` passes
    locally and in CI.
14. No credentials in the images or the repository; gitleaks stays green.

## End-to-end check

1. Fresh clone, `pnpm install`, copy `.env.example` to `.env`.
2. `docker compose up -d`, wait until `api` is healthy, then
   `docker compose run --rm importer`.
3. `curl 'localhost:3333/api/municipalities?search=zurich'`. Expected:
   Zürich, canton ZH, a price between 10 and 46 Rp./kWh.
4. `curl 'localhost:3333/api/municipalities?sort=price&order=desc&limit=200&offset=2000'`.
   Expected: Siselen is the last item.
5. `curl -i 'localhost:3333/api/municipalities?limit=500'`. Expected: 400,
   `Content-Type: application/problem+json`.
6. Open `localhost:3333/api/docs`: the endpoint and its parameters are
   documented.
7. `docker compose stop db`, then `curl -i localhost:3333/api/health`.
   Expected: 503.
8. `docker pull ghcr.io/<owner>/gemeindespiegel-api:latest` works after the
   merge of C3.5.
