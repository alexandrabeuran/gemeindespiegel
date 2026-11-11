import { Transform, type TransformFnParams } from 'class-transformer';
import {
  IsIn,
  IsInt,
  IsOptional,
  IsString,
  Length,
  Matches,
  Max,
  Min,
} from 'class-validator';

export const SORT_FIELDS = ['name', 'price'] as const;
export const SORT_ORDERS = ['asc', 'desc'] as const;

// Number() alone would turn "", " 5", "1e2" and "0x7EB" into valid numbers. Only plain digits count;
// everything else becomes NaN, which @IsInt rejects with the field name.
function toInteger({ value }: TransformFnParams): number {
  return typeof value === 'string' && /^\d+$/.test(value) ? Number(value) : NaN;
}

export class ListMunicipalitiesQuery {
  // Trimming happens before validation, so a search of only spaces counts as empty and is rejected.
  @IsOptional()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsString()
  @Length(1, 100)
  // PostgreSQL text cannot hold a NUL byte, so it would fail with a 500 instead of a 400.
  @Matches(/^\P{Cc}*$/u, {
    message: 'search must not contain control characters',
  })
  search?: string;

  @IsOptional()
  @Matches(/^[A-Z]{2}$/, { message: 'canton must be two capital letters' })
  canton?: string;

  // The range check keeps values away from the smallint column; years without data are the service's job (404).
  @IsOptional()
  @Transform(toInteger)
  @IsInt()
  @Min(1900)
  @Max(2100)
  year?: number;

  @IsIn(SORT_FIELDS)
  sort: (typeof SORT_FIELDS)[number] = 'name';

  @IsIn(SORT_ORDERS)
  order: (typeof SORT_ORDERS)[number] = 'asc';

  @Transform(toInteger)
  @IsInt()
  @Min(1)
  @Max(200)
  limit = 50;

  // Far above the ~2100 municipalities, and far below what PostgreSQL's bigint OFFSET can take.
  @Transform(toInteger)
  @IsInt()
  @Min(0)
  @Max(100_000)
  offset = 0;
}
