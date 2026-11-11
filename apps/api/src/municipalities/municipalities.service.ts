import { Injectable, NotFoundException } from '@nestjs/common';
import { DataSource } from 'typeorm';
import { ListMunicipalitiesQuery } from './list-municipalities.query';
import {
  MunicipalityList,
  MunicipalityListItem,
} from './municipality-list.response';

// One row as PostgreSQL returns it: snake_case names, numeric as string.
interface MunicipalityRow {
  bfs_number: number;
  name: string;
  canton_abbreviation: string;
  canton_name: string;
  average_total: string | null;
  multiple_operators: boolean | null;
}

// Shared by the count and the page, so total always counts exactly the rows the pages show.
// $1 = escaped search text or null, $2 = canton abbreviation or null.
// unaccent on both sides makes "zurich" match "Zürich"; ILIKE ignores case.
const MATCHES = `
  WHERE ($1::text IS NULL
         OR unaccent(m.name) ILIKE '%' || unaccent($1::text) || '%' ESCAPE '\\')
    AND ($2::text IS NULL OR c.abbreviation = $2::text)
`;

// Column names cannot be SQL parameters, so the ORDER BY comes from this fixed list and never from user text.
// The BFS number breaks ties, so pages never overlap or skip rows.
// The image sorts by byte order by default (Ä after Z); ICU's Swiss German collation sorts Ä like A.
const NAME = 'm.name COLLATE "de-CH-x-icu"';
const ORDER_BY: Record<
  `${ListMunicipalitiesQuery['sort']}-${ListMunicipalitiesQuery['order']}`,
  string
> = {
  'name-asc': `${NAME} ASC, m.bfs_number`,
  'name-desc': `${NAME} DESC, m.bfs_number`,
  // NULLS LAST in both directions: without it, PostgreSQL puts NULL first when descending.
  'price-asc': 'p.average_total ASC NULLS LAST, m.bfs_number',
  'price-desc': 'p.average_total DESC NULLS LAST, m.bfs_number',
};

// The search text is matched literally, so LIKE's own special characters need a backslash in front.
function escapeLike(text: string): string {
  return text.replace(/[\\%_]/g, (character) => `\\${character}`);
}

@Injectable()
export class MunicipalitiesService {
  constructor(private readonly dataSource: DataSource) {}

  async list(query: ListMunicipalitiesQuery): Promise<MunicipalityList> {
    const year = query.year ?? (await this.newestYear());
    if (query.year !== undefined && !(await this.hasYear(query.year))) {
      throw new NotFoundException(`No price data for year ${query.year}`);
    }
    // $1 and $2 of MATCHES; undefined would be an error in pg, null means "no filter".
    const filters = [
      query.search === undefined ? null : escapeLike(query.search),
      query.canton ?? null,
    ];

    // A separate count, because the page can be empty while there are still matches (offset past the end).
    const [counted] = await this.dataSource.query<{ total: string }[]>(
      `
      SELECT count(*) AS total
      FROM municipality m
      JOIN canton c ON c.bfs_number = m.canton_bfs_number
      ${MATCHES}
      `,
      filters,
    );

    // Plain SQL instead of the query builder, so the review reads the query that actually runs (as with migrations, ADR 0009).
    const rows = await this.dataSource.query<MunicipalityRow[]>(
      `
      SELECT m.bfs_number,
             m.name,
             c.abbreviation AS canton_abbreviation,
             c.name AS canton_name,
             p.average_total,
             p.multiple_operators
      FROM municipality m
      JOIN canton c ON c.bfs_number = m.canton_bfs_number
      -- LEFT JOIN keeps municipalities without a price; the year belongs in ON, in WHERE it would drop them again.
      LEFT JOIN municipality_price p
        ON p.municipality_bfs_number = m.bfs_number
       AND p.tariff_year = $3
      ${MATCHES}
      ORDER BY ${ORDER_BY[`${query.sort}-${query.order}`]}
      LIMIT $4 OFFSET $5
      `,
      [...filters, year, query.limit, query.offset],
    );

    return {
      year,
      // count() is bigint, which the pg driver returns as a string.
      total: Number(counted?.total ?? 0),
      limit: query.limit,
      offset: query.offset,
      items: rows.map(toItem),
    };
  }

  private async newestYear(): Promise<number | null> {
    // max() always returns one row, with null when the table is empty.
    const [newest] = await this.dataSource.query<{ year: number | null }[]>(
      'SELECT max(tariff_year) AS year FROM municipality_price',
    );
    return newest?.year ?? null;
  }

  private async hasYear(year: number): Promise<boolean> {
    const rows = await this.dataSource.query<unknown[]>(
      'SELECT 1 FROM municipality_price WHERE tariff_year = $1 LIMIT 1',
      [year],
    );
    return rows.length > 0;
  }
}

function toItem(row: MunicipalityRow): MunicipalityListItem {
  return {
    bfsNumber: row.bfs_number,
    name: row.name,
    canton: { abbreviation: row.canton_abbreviation, name: row.canton_name },
    price:
      row.average_total === null
        ? null
        : {
            averageTotal: Number(row.average_total),
            multipleOperators: row.multiple_operators === true,
          },
  };
}
