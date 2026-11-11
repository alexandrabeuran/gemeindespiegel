import { NotFoundException } from '@nestjs/common';
import type { DataSource } from 'typeorm';
import { ListMunicipalitiesQuery } from './list-municipalities.query';
import { MunicipalitiesService } from './municipalities.service';

// Answers each SQL statement the way the pg driver would: numeric and bigint as strings.
// The SQL itself is tested against PostgreSQL in test/municipalities.service.e2e-spec.ts.
function fakeDataSource(answers: { years: number[] }) {
  const query = jest.fn(async (sql: string, parameters: unknown[] = []) => {
    if (sql.includes('max(tariff_year)')) {
      return [{ year: Math.max(...answers.years) }];
    }
    if (sql.includes('SELECT 1 FROM municipality_price')) {
      return answers.years.includes(parameters[0] as number) ? [{}] : [];
    }
    if (sql.includes('count(*)')) {
      return [{ total: '2110' }];
    }
    return [
      {
        bfs_number: 261,
        name: 'Zürich',
        canton_abbreviation: 'ZH',
        canton_name: 'Zürich',
        average_total: '27.1234',
        multiple_operators: false,
      },
      {
        bfs_number: 499,
        name: 'Siselen',
        canton_abbreviation: 'BE',
        canton_name: 'Bern',
        average_total: null,
        multiple_operators: null,
      },
    ];
  });
  return { query, dataSource: { query } as unknown as DataSource };
}

describe('MunicipalitiesService', () => {
  it('turns database rows into the response', async () => {
    const { dataSource } = fakeDataSource({ years: [2026, 2027] });

    const result = await new MunicipalitiesService(dataSource).list(
      new ListMunicipalitiesQuery(),
    );

    expect(result).toEqual({
      year: 2027,
      total: 2110,
      limit: 50,
      offset: 0,
      items: [
        {
          bfsNumber: 261,
          name: 'Zürich',
          canton: { abbreviation: 'ZH', name: 'Zürich' },
          price: { averageTotal: 27.1234, multipleOperators: false },
        },
        {
          bfsNumber: 499,
          name: 'Siselen',
          canton: { abbreviation: 'BE', name: 'Bern' },
          price: null,
        },
      ],
    });
  });

  it('throws 404 for a year without data and does not query the list', async () => {
    const { dataSource, query } = fakeDataSource({ years: [2027] });
    const request = Object.assign(new ListMunicipalitiesQuery(), {
      year: 1999,
    });

    await expect(
      new MunicipalitiesService(dataSource).list(request),
    ).rejects.toBeInstanceOf(NotFoundException);
    expect(query).toHaveBeenCalledTimes(1);
  });
});
