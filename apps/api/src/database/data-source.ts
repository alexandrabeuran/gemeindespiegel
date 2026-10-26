import { join } from 'node:path';
import { DataSource } from 'typeorm';
import { databaseOptions } from './database-options';

// Entry point for the TypeORM CLI (migration:run, migration:generate).
// The NestJS app does not use this file: webpack bundles the app, so file globs would not resolve there.
export default new DataSource({
  ...databaseOptions(process.env),
  entities: [join(__dirname, '..', '**', '*.entity.ts')],
  migrations: [join(__dirname, 'migrations', '*.ts')],
});
