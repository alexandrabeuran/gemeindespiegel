import type { DataSourceOptions } from 'typeorm';

type PostgresDataSourceOptions = Extract<
  DataSourceOptions,
  { type: 'postgres' }
>;

type Env = Record<string, string | undefined>;

// Fail at startup with the variable name instead of a vague connection error later.
function required(env: Env, name: string): string {
  const value = env[name];
  if (!value) {
    throw new Error(`Missing environment variable ${name}, see .env.example`);
  }
  return value;
}

function port(env: Env): number {
  const raw = env['POSTGRES_PORT'] ?? '5432';
  const value = Number(raw);
  if (!Number.isInteger(value) || value <= 0) {
    throw new Error(`POSTGRES_PORT must be a port number, got "${raw}"`);
  }
  return value;
}

// Shared by the NestJS app and the TypeORM migration CLI, so both connect the same way.
export function databaseOptions(env: Env): PostgresDataSourceOptions {
  return {
    type: 'postgres',
    host: env['POSTGRES_HOST'] ?? 'localhost',
    port: port(env),
    username: required(env, 'POSTGRES_USER'),
    password: required(env, 'POSTGRES_PASSWORD'),
    database: required(env, 'POSTGRES_DB'),
    // The schema changes only through reviewed migrations (ADR 0009).
    synchronize: false,
  };
}
