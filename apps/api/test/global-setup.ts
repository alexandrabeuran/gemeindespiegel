import { execFileSync } from 'node:child_process';
import { join } from 'node:path';
import { PostgreSqlContainer } from '@testcontainers/postgresql';

// Same image as compose.yaml, so the tests see the database the app runs on.
const POSTGRES_IMAGE = 'postgres:18.6-alpine';
const REPO_ROOT = join(__dirname, '..', '..', '..');

export default async function globalSetup(): Promise<void> {
  const container = await new PostgreSqlContainer(POSTGRES_IMAGE).start();

  // Test files run in workers started after this, so they inherit these variables.
  process.env['POSTGRES_HOST'] = container.getHost();
  process.env['POSTGRES_PORT'] = String(container.getPort());
  process.env['POSTGRES_USER'] = container.getUsername();
  process.env['POSTGRES_PASSWORD'] = container.getPassword();
  process.env['POSTGRES_DB'] = container.getDatabase();

  // The real migrations through the same Nx target as the importer test, so there is one way to build the schema.
  execFileSync(
    'pnpm',
    ['exec', 'nx', 'run', 'api:migrate', '--skip-nx-cache'],
    {
      cwd: REPO_ROOT,
      env: process.env,
      stdio: 'inherit',
    },
  );

  // globalTeardown runs in the same process, so a global is the documented way to hand over the container.
  globalThis.postgresContainer = container;
}
