import { databaseOptions } from './database-options';

// A complete set of variables, like a filled-in .env file.
const env = {
  POSTGRES_HOST: 'db.example',
  POSTGRES_PORT: '5433',
  POSTGRES_USER: 'tester',
  POSTGRES_PASSWORD: 'secret',
  POSTGRES_DB: 'testdb',
};

describe('databaseOptions', () => {
  it('takes over all values and reads the port as a number', () => {
    expect(databaseOptions(env)).toMatchObject({
      type: 'postgres',
      host: 'db.example',
      port: 5433,
      username: 'tester',
      password: 'secret',
      database: 'testdb',
    });
  });

  it('falls back to localhost:5432 when host and port are not set', () => {
    const withoutHostAndPort = {
      ...env,
      POSTGRES_HOST: undefined,
      POSTGRES_PORT: undefined,
    };

    expect(databaseOptions(withoutHostAndPort)).toMatchObject({
      host: 'localhost',
      port: 5432,
    });
  });

  it('never lets TypeORM change the schema on its own', () => {
    expect(databaseOptions(env).synchronize).toBe(false);
  });

  it.each(['POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DB'])(
    'names %s in the error when it is missing',
    (name) => {
      const incomplete = { ...env, [name]: undefined };

      expect(() => databaseOptions(incomplete)).toThrow(name);
    },
  );

  it('rejects a port that is not a number', () => {
    expect(() => databaseOptions({ ...env, POSTGRES_PORT: 'abc' })).toThrow(
      'POSTGRES_PORT',
    );
  });
});
