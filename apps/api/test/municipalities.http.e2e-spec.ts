import request from 'supertest';
import { DataSource } from 'typeorm';
import { databaseOptions } from '../src/database/database-options';
import { seed } from './seed';
import { type RunningApi, startApi } from './start-api';

// The built app over HTTP: main.ts, module wiring, validation and the service together.
// The rules themselves are tested in the service e2e test.
describe('GET /api/municipalities', () => {
  let api: RunningApi;

  beforeAll(async () => {
    const dataSource = await new DataSource(
      databaseOptions(process.env),
    ).initialize();
    await seed(dataSource);
    await dataSource.destroy();
    api = await startApi();
  });

  afterAll(async () => {
    await api?.stop();
  });

  const get = (path: string) => request(api.url).get(path);

  it('lists the first page sorted by name without parameters', async () => {
    const response = await get('/api/municipalities').expect(200);

    expect(response.body).toEqual(
      expect.objectContaining({ year: 2027, total: 5, limit: 50, offset: 0 }),
    );
    expect(response.body.items[0]).toEqual({
      bfsNumber: 351,
      name: 'Bern',
      canton: { abbreviation: 'BE', name: 'Bern' },
      price: { averageTotal: 25, multipleOperators: true },
    });
  });

  it('turns the query string into filters', async () => {
    const response = await get(
      '/api/municipalities?search=zurich&canton=ZH&limit=10',
    ).expect(200);

    expect(
      response.body.items.map((item: { name: string }) => item.name),
    ).toEqual(['Zürich']);
    expect(response.body.limit).toBe(10);
  });

  it.each([
    ['limit', 'limit=0'],
    ['limit', 'limit=201'],
    ['offset', 'offset=-1'],
    ['sort', 'sort=foo'],
    ['year', 'year=99999'],
    ['canton', 'canton=zh1'],
    ['colour', 'colour=red'],
  ])('answers 400 naming %s for ?%s', async (field, queryString) => {
    const response = await get(`/api/municipalities?${queryString}`).expect(
      400,
    );

    expect(JSON.stringify(response.body)).toContain(field);
  });

  it('answers 404 for a year without data', async () => {
    await get('/api/municipalities?year=1999').expect(404);
  });
});
