import {
  Column,
  Entity,
  JoinColumn,
  ManyToOne,
  PrimaryGeneratedColumn,
  Unique,
} from 'typeorm';
import { Municipality } from '../municipalities/municipality.entity';
import { GridOperator } from './grid-operator.entity';

// numeric keeps prices exact, so the parts add up to the total. The pg driver returns numeric as string.
const price = { type: 'numeric', precision: 7, scale: 4 } as const;

@Entity({ name: 'tariff' })
@Unique('uq_tariff_municipality_operator_year', [
  'municipality',
  'gridOperator',
  'tariffYear',
])
export class Tariff {
  @PrimaryGeneratedColumn('identity', { name: 'id' })
  id!: number;

  @ManyToOne(() => Municipality, { nullable: false })
  @JoinColumn({ name: 'municipality_bfs_number' })
  municipality!: Municipality;

  @ManyToOne(() => GridOperator, { nullable: false })
  @JoinColumn({ name: 'grid_operator_elcom_id' })
  gridOperator!: GridOperator;

  @Column({ name: 'tariff_year', type: 'smallint' })
  tariffYear!: number;

  @Column({ name: 'total', ...price })
  total!: string;

  @Column({ name: 'energy', ...price })
  energy!: string;

  @Column({ name: 'grid_usage', ...price })
  gridUsage!: string;

  @Column({ name: 'levies', ...price })
  levies!: string;

  @Column({ name: 'grid_surcharge', ...price })
  gridSurcharge!: string;

  @Column({ name: 'metering', ...price })
  metering!: string;
}
