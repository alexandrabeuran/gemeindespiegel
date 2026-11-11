import { BadRequestException } from '@nestjs/common';
import { createValidationPipe } from '../app/validation-pipe';
import { ListMunicipalitiesQuery } from './list-municipalities.query';

// Query values arrive as strings, exactly like Express hands them over.
async function parse(raw: Record<string, string>) {
  return createValidationPipe().transform(raw, {
    type: 'query',
    metatype: ListMunicipalitiesQuery,
  });
}

async function rejectedFields(raw: Record<string, string>) {
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
  ])('rejects %s=%s and names the field', async (field, value) => {
    const response = await rejectedFields({ [field]: value });

    expect(JSON.stringify(response)).toContain(field);
  });

  it('rejects unknown parameters', async () => {
    const response = await rejectedFields({ colour: 'red' });

    expect(JSON.stringify(response)).toContain('colour');
  });
});
