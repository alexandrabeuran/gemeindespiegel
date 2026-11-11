import { Transform, Type } from 'class-transformer';
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

export class ListMunicipalitiesQuery {
  // Trimming happens before validation, so a search of only spaces counts as empty and is rejected.
  @IsOptional()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsString()
  @Length(1, 100)
  search?: string;

  @IsOptional()
  @Matches(/^[A-Z]{2}$/, { message: 'canton must be two capital letters' })
  canton?: string;

  // The range check keeps values away from the smallint column; years without data are the service's job (404).
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1900)
  @Max(2100)
  year?: number;

  @IsIn(SORT_FIELDS)
  sort: (typeof SORT_FIELDS)[number] = 'name';

  @IsIn(SORT_ORDERS)
  order: (typeof SORT_ORDERS)[number] = 'asc';

  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(200)
  limit = 50;

  @Type(() => Number)
  @IsInt()
  @Min(0)
  offset = 0;
}
