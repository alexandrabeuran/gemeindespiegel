import { NotFoundException } from '@nestjs/common';
import { DataSource } from 'typeorm';
import { databaseOptions } from '../src/database/database-options';
import { ListMunicipalitiesQuery } from '../src/municipalities/list-municipalities.query';
import { MunicipalitiesService } from '../src/municipalities/municipalities.service';
import { seed } from './seed';

// Builds the query the way the ValidationPipe does: class defaults first, then the given values.
function query(values: Partial<ListMunicipalitiesQuery> = {}) {
  return Object.assign(new ListMunicipalitiesQuery(), values);
}

describe('MunicipalitiesService (PostgreSQL)', () => {
  let dataSource: DataSource;
  let service: MunicipalitiesService;

  beforeAll(async () => {
    dataSource = await new DataSource(
      databaseOptions(process.env),
    ).initialize();
    await seed(dataSource);
    service = new MunicipalitiesService(dataSource);
  });

  afterAll(async () => {
    await dataSource?.destroy();
  });

  it('lists all municipalities by name for the newest year', async () => {
    const result = await service.list(query());

    expect(result.year).toBe(2027);
    expect(result.total).toBe(5);
    expect(result.limit).toBe(50);
    expect(result.offset).toBe(0);
    expect(result.items.map((item) => item.name)).toEqual([
      'Bern',
      'Neuchâtel',
      'Siselen',
      'Winterthur',
      'Zürich',
    ]);
  });

  it('returns the price as a number and null without a price', async () => {
    const { items } = await service.list(query());

    expect(items.find((item) => item.bfsNumber === 261)).toEqual({
      bfsNumber: 261,
      name: 'Zürich',
      canton: { abbreviation: 'ZH', name: 'Zürich' },
      price: { averageTotal: 27.1234, multipleOperators: false },
    });
    expect(items.find((item) => item.bfsNumber === 499)?.price).toBeNull();
  });

  describe('search', () => {
    it.each([
      ['zurich', 'Zürich'],
      ['ZÜRICH', 'Zürich'],
      ['rich', 'Zürich'],
      ['neuchatel', 'Neuchâtel'],
    ])('finds %s', async (search, name) => {
      const result = await service.list(query({ search }));

      expect(result.items.map((item) => item.name)).toEqual([name]);
      expect(result.total).toBe(1);
    });

    // Without escaping, % and _ would be LIKE wildcards and match every row.
    it.each(['%', '_'])('treats %s as a plain character', async (search) => {
      const result = await service.list(query({ search }));

      expect(result.items).toEqual([]);
      expect(result.total).toBe(0);
    });
  });

  describe('canton', () => {
    it('returns only municipalities of that canton', async () => {
      const result = await service.list(query({ canton: 'ZH' }));

      expect(result.items.map((item) => item.bfsNumber)).toEqual([230, 261]);
    });

    it('returns an empty list for a canton that does not exist', async () => {
      const result = await service.list(query({ canton: 'XX' }));

      expect(result.items).toEqual([]);
      expect(result.total).toBe(0);
    });

    it('combines with the search', async () => {
      const result = await service.list(query({ canton: 'BE', search: 'e' }));

      expect(result.items.map((item) => item.name)).toEqual([
        'Bern',
        'Siselen',
      ]);
    });
  });

  it('counts all matches, not only the current page', async () => {
    const result = await service.list(query({ canton: 'ZH', limit: 1 }));

    expect(result.items).toHaveLength(1);
    expect(result.total).toBe(2);
  });

  const bfsNumbers = async (values: Partial<ListMunicipalitiesQuery>) =>
    (await service.list(query(values))).items.map((item) => item.bfsNumber);

  describe('sorting', () => {
    // Winterthur (230) and Bern (351) cost the same, so the BFS number decides; Siselen (499) has no price.
    it('sorts by price ascending with ties by BFS number and no price last', async () => {
      expect(await bfsNumbers({ sort: 'price', order: 'asc' })).toEqual([
        230, 351, 261, 6458, 499,
      ]);
    });

    it('keeps municipalities without a price last when descending', async () => {
      expect(await bfsNumbers({ sort: 'price', order: 'desc' })).toEqual([
        6458, 261, 230, 351, 499,
      ]);
    });

    it('sorts by name descending', async () => {
      expect(await bfsNumbers({ order: 'desc' })).toEqual([
        261, 230, 499, 6458, 351,
      ]);
    });

    // A plain byte order would put Ä after Z.
    it('sorts a leading umlaut like its base letter', async () => {
      await dataSource.query(
        "INSERT INTO municipality (bfs_number, name, canton_bfs_number) VALUES (731, 'Ägerten', 2)",
      );
      try {
        const result = await service.list(query({ canton: 'BE' }));

        expect(result.items.map((item) => item.name)).toEqual([
          'Ägerten',
          'Bern',
          'Siselen',
        ]);
      } finally {
        await dataSource.query(
          'DELETE FROM municipality WHERE bfs_number = 731',
        );
      }
    });
  });

  describe('pages', () => {
    it('shows every municipality exactly once across all pages', async () => {
      const seen: number[] = [];
      for (let offset = 0; offset < 5; offset += 2) {
        seen.push(...(await bfsNumbers({ sort: 'price', limit: 2, offset })));
      }

      expect(seen).toEqual(await bfsNumbers({ sort: 'price' }));
    });

    it('returns an empty page past the end but still the total', async () => {
      const result = await service.list(query({ offset: 10 }));

      expect(result.items).toEqual([]);
      expect(result.total).toBe(5);
    });
  });

  describe('year', () => {
    it('uses the given year', async () => {
      const result = await service.list(query({ year: 2026 }));

      expect(result.year).toBe(2026);
      expect(
        result.items
          .filter((item) => item.price !== null)
          .map((item) => [item.bfsNumber, item.price?.averageTotal]),
      ).toEqual([[261, 26]]);
    });

    it('rejects a year without data with 404', async () => {
      await expect(service.list(query({ year: 1999 }))).rejects.toBeInstanceOf(
        NotFoundException,
      );
    });

    describe('without any price data', () => {
      beforeAll(async () => {
        await dataSource.query('TRUNCATE municipality_price');
      });

      afterAll(async () => {
        await seed(dataSource);
      });

      it('returns year null and no prices, but all municipalities', async () => {
        const result = await service.list(query());

        expect(result.year).toBeNull();
        expect(result.total).toBe(5);
        expect(result.items.every((item) => item.price === null)).toBe(true);
      });
    });
  });
});
