import { Column, Entity, JoinColumn, ManyToOne, PrimaryColumn } from 'typeorm';
import { Municipality } from '../municipalities/municipality.entity';

// One row per municipality and year. Municipalities without ElCom data have no row.
@Entity({ name: 'municipality_price' })
export class MunicipalityPrice {
  // The foreign key is also part of the primary key, so it needs its own column property next to the relation.
  @PrimaryColumn({ name: 'municipality_bfs_number', type: 'smallint' })
  municipalityBfsNumber!: number;

  @PrimaryColumn({ name: 'tariff_year', type: 'smallint' })
  tariffYear!: number;

  @ManyToOne(() => Municipality, { nullable: false })
  @JoinColumn({ name: 'municipality_bfs_number' })
  municipality!: Municipality;

  @Column({ name: 'average_total', type: 'numeric', precision: 7, scale: 4 })
  averageTotal!: string;

  @Column({ name: 'multiple_operators', type: 'boolean' })
  multipleOperators!: boolean;
}
