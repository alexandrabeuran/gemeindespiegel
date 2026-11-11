import type { StartedPostgreSqlContainer } from '@testcontainers/postgresql';

declare global {
  var postgresContainer: StartedPostgreSqlContainer | undefined;
}
