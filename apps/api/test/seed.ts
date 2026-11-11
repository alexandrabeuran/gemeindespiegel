import type { DataSource } from 'typeorm';

// Small on purpose: each row exists for one rule of the SPEC, so a failing test points at that rule.
export async function seed(dataSource: DataSource): Promise<void> {
  await dataSource.query(
    'TRUNCATE tariff, municipality_price, municipality, grid_operator, canton',
  );

  await dataSource.query(`
    INSERT INTO canton (bfs_number, abbreviation, name) VALUES
      (1, 'ZH', 'Zürich'),
      (2, 'BE', 'Bern'),
      (24, 'NE', 'Neuchâtel')
  `);

  await dataSource.query(`
    INSERT INTO municipality (bfs_number, name, canton_bfs_number) VALUES
      (261, 'Zürich', 1),      -- search without umlaut, partial match "rich"
      (230, 'Winterthur', 1),  -- same price as Bern, lower BFS number
      (351, 'Bern', 2),        -- same price as Winterthur, several grid operators
      (499, 'Siselen', 2),     -- no price, must still be listed and sorted last
      (6458, 'Neuchâtel', 24)  -- search without circumflex
  `);

  await dataSource.query(`
    INSERT INTO municipality_price
      (municipality_bfs_number, tariff_year, average_total, multiple_operators) VALUES
      (261, 2027, 27.1234, false),
      (230, 2027, 25.0000, false),
      (351, 2027, 25.0000, true),
      (6458, 2027, 30.5000, false),
      -- An older year, so "newest year" is a real choice and ?year=2026 has data.
      (261, 2026, 26.0000, false)
  `);
}
