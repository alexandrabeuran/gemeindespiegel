# C1 Repo foundation

Status: done, 2026-10-25

## Goal

Set up the monorepo so that every later step starts with working quality
gates: code is linted, formatted, type-checked, tested and built automatically,
and nothing reaches `main` without a green pull request.

## Scope

- Nx workspace with pnpm, Node 24 LTS (pinned in `.nvmrc` and `engines`).
- TypeScript in strict mode (`tsconfig.base.json`).
- ESLint and Prettier for the whole workspace. ESLint warnings fail the check
  (`--max-warnings=0`), locally and in CI.
- One app: `apps/web`, an empty Next.js "hello world" page with one Vitest
  and Testing Library test. It exists so that CI checks real code from day one.
- Git hooks with husky: lint-staged (ESLint and Prettier on staged files)
  before each commit, commitlint (Conventional Commits) on each commit message.
- GitHub Actions workflow on every pull request to `main`:
  - lint, format check, typecheck, test and build for affected projects (`nx affected`)
  - gitleaks secret scan
  - commitlint over the commits of the pull request
  - `likec4 validate` for `docs/architecture/` and markdownlint for `docs/`
- Branch protection (ruleset) on `main`: changes only through pull requests,
  all checks above required, 0 approvals required (solo project), no bypass,
  also not for admins. No force pushes, no deletion.
- Issue templates (bug, feature) and a pull request template.
- GitHub Projects board (Kanban: Todo, In progress, Done) linked to the repo.
- `README.md` skeleton: title, subtitle, vision, "About this project", how to
  run locally, license.
- `LICENSE`: MIT.

## Out of scope

- NestJS API and Python import job (C2, C3).
- Real content in the web app: municipality list, i18n, MSW, Playwright (C4).
- Docker Compose, PostgreSQL (C2).
- Dependabot, CodeQL, Trivy, release-please (C10).
- Upgrade to Node 26 LTS (released 2026-10-28): a separate small change after C1.

## Acceptance criteria

1. `pnpm install` on a fresh clone succeeds with Node 24.
2. `pnpm nx run-many -t lint typecheck test build` passes locally.
3. `pnpm nx format:check` passes.
4. A commit with the message `bad message` is rejected by the commit-msg hook;
   `chore: test` is accepted.
5. A staged file with a lint error is blocked by the pre-commit hook.
6. A pull request runs all CI jobs listed in Scope, and each job is a required check.
7. A direct push to `main` is rejected by GitHub, also for the admin account.
8. gitleaks fails on a pull request that contains a fake token.
9. A broken `.c4` file or a markdownlint error in `docs/` makes CI fail.
10. README, LICENSE, issue and PR templates are visible on GitHub.

## End-to-end check

1. Create branch `test/c1-gates`, add a lint error to `apps/web` and a fake
   token, open a pull request. Expected: CI red (lint and gitleaks), merge
   button blocked.
2. Remove both errors and update the branch. Expected: all checks green,
   merge possible.
3. Merge, then try a direct push of a local commit to `main`. Expected: rejected.
4. Delete the test branch.
