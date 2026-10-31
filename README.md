# Gemeindespiegel

Compare Swiss municipalities.

## Vision

For people planning to move to Switzerland who don't know the country yet,
Gemeindespiegel compares Swiss municipalities by what matters to them – taxes,
health insurance, electricity, commute – and turns their priorities into a
personal ranking. Instead of juggling separate calculators, single-topic
comparison sites or gut feeling, it brings all the key numbers together in one
place.

## About this project

Gemeindespiegel is a portfolio project. It shows how I plan, build, test and
ship a full-stack application: an Nx monorepo with strict TypeScript, automated
quality checks on every pull request, and architecture decisions documented in
[`docs/adr`](docs/adr/README.md).

The project is at an early stage. Right now the repository contains the
workspace setup, an empty web app, the PostgreSQL database schema and a job
that imports Swiss municipalities and their electricity prices.

## Running locally

Requirements: Node.js 26 and pnpm.

```sh
pnpm install
pnpm nx dev web
```

The app then runs on <http://localhost:3000>.

Run all checks (lint, typecheck, tests, build):

```sh
pnpm nx run-many -t lint typecheck test build
```

### Importing data locally

Requirements: Docker with Docker Compose.

```sh
cp .env.example .env              # then change the password
docker compose up -d db           # PostgreSQL, only reachable from this machine
pnpm nx run api:migrate           # create the tables
docker compose run --rm importer  # fetch BFS and ElCom data and write it
```

The import runs in one transaction: either all data is written or nothing
changes. Running it again gives the same result. It ends with a short summary,
for example the number of municipalities and how many of them have a price.

### Importer (Python)

The importer in `apps/importer` uses Python 3.14 and
[uv](https://docs.astral.sh/uv/). Nx runs its checks like those of the other
projects:

```sh
pnpm nx run-many -t lint typecheck test -p importer  # ruff, mypy, pytest
pnpm nx run importer:test-integration                # needs Docker (Testcontainers)
```

Directly in `apps/importer`: `uv run ruff check .`, `uv run mypy`,
`uv run pytest`. To run the import without Docker, load `.env` into the shell
first (`set -a; source ../../.env; set +a`), then `uv run importer`.

## Data sources

- Municipalities, districts and cantons: Federal Statistical Office (FSO),
  [Swiss official commune register](https://www.agvchapp.bfs.admin.ch/).
  Source: FSO.
- Electricity prices: Federal Electricity Commission (ElCom), tariffs per
  municipality via [LINDAS](https://lindas.admin.ch/), licence "Open use".

## License

[MIT](LICENSE)
