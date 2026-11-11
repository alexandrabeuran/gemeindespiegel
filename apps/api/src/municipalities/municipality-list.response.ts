// Classes rather than interfaces, so C3.3 can add @ApiProperty for the OpenAPI contract.
export class CantonSummary {
  abbreviation!: string;
  name!: string;
}

// Not "MunicipalityPrice": that name already belongs to the entity in electricity/.
export class PriceSummary {
  // Rp./kWh as a JSON number; the database keeps the exact numeric(7,4).
  averageTotal!: number;
  multipleOperators!: boolean;
}

export class MunicipalityListItem {
  bfsNumber!: number;
  name!: string;
  canton!: CantonSummary;
  price!: PriceSummary | null;
}

export class MunicipalityList {
  // null when there is no price data at all.
  year!: number | null;
  // All matches, not only this page.
  total!: number;
  limit!: number;
  offset!: number;
  items!: MunicipalityListItem[];
}
