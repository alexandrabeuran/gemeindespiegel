import { BadRequestException } from '@nestjs/common';
import { createValidationPipe } from '../app/validation-pipe';
import { ListMunicipalitiesQuery } from './list-municipalities.query';

// Query values arrive as strings, exactly like Express hands them over; a repeated parameter becomes an array.
type RawQuery = Record<string, string | string[]>;

async function parse(raw: RawQuery) {
  return createValidationPipe().transform(raw, {
    type: 'query',
    metatype: ListMunicipalitiesQuery,
  });
}

async function rejectedFields(raw: RawQuery) {
  try {
    await parse(raw);
  } catch (error) {
    expect(error).toBeInstanceOf(BadRequestException);
    return (error as BadRequestException).getResponse();
  }
  throw new Error(`expected ${JSON.stringify(raw)} to be rejected`);
}

describe('ListMunicipalitiesQuery', () => {
  it('fills in the defaults when no parameter is given', async () => {
    const query = await parse({});

    expect(query).toEqual(
      expect.objectContaining({
        sort: 'name',
        order: 'asc',
        limit: 50,
        offset: 0,
      }),
    );
    expect(query.search).toBeUndefined();
    expect(query.year).toBeUndefined();
  });

  it('turns numbers from the URL into numbers and trims the search', async () => {
    const query = await parse({
      search: '  zurich ',
      limit: '200',
      year: '2027',
    });

    expect(query.search).toBe('zurich');
    expect(query.limit).toBe(200);
    expect(query.year).toBe(2027);
  });

  it.each([
    ['limit', '0'],
    ['limit', '201'],
    ['offset', '-1'],
    ['sort', 'foo'],
    ['order', 'up'],
    ['year', '99999'],
    ['canton', 'zh1'],
    ['search', '   '],
    ['search', 'x'.repeat(101)],
    ['year', '1899'],
    ['year', '2101'],
    // PostgreSQL cannot store these, so letting them through would end in a 500.
    ['offset', '99999999999999999999'],
    ['search', 'a\0b'],
    // Number() would quietly accept all of these.
    ['offset', ''],
    ['limit', ' 5'],
    ['limit', '1e2'],
    ['year', '0x7EB'],
    ['year', '2027.0'],
  ])('rejects %s=%j and names the field', async (field, value) => {
    const response = await rejectedFields({ [field]: value });

    expect(JSON.stringify(response)).toContain(field);
  });

  it('rejects a repeated parameter', async () => {
    const response = await rejectedFields({ limit: ['1', '2'] });

    expect(JSON.stringify(response)).toContain('limit');
  });

  it('accepts the boundaries', async () => {
    await expect(parse({ limit: '1', year: '1900' })).resolves.toEqual(
      expect.objectContaining({ limit: 1, year: 1900 }),
    );
    await expect(parse({ limit: '200', year: '2100' })).resolves.toEqual(
      expect.objectContaining({ limit: 200, year: 2100 }),
    );
  });

  it('rejects unknown parameters', async () => {
    const response = await rejectedFields({ colour: 'red' });

    expect(JSON.stringify(response)).toContain('colour');
  });
});
