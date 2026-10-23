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
workspace setup and an empty web app.

## Running locally

Requirements: Node.js 24 and pnpm.

```sh
pnpm install
pnpm nx dev web
```

The app then runs on <http://localhost:3000>.

Run all checks (lint, typecheck, tests, build):

```sh
pnpm nx run-many -t lint typecheck test build
```

## License

[MIT](LICENSE)
