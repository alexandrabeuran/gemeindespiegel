import { Column, Entity, PrimaryColumn } from 'typeorm';

@Entity({ name: 'grid_operator' })
export class GridOperator {
  // ElCom's own operator number, so repeated imports refer to the same row.
  @PrimaryColumn({ name: 'elcom_id', type: 'integer' })
  elcomId!: number;

  @Column({ name: 'name', type: 'text' })
  name!: string;
}
