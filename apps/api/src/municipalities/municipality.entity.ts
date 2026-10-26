import { Column, Entity, JoinColumn, ManyToOne, PrimaryColumn } from 'typeorm';
import { Canton } from './canton.entity';

@Entity({ name: 'municipality' })
export class Municipality {
  @PrimaryColumn({ name: 'bfs_number', type: 'smallint' })
  bfsNumber!: number;

  @Column({ name: 'name', type: 'text' })
  name!: string;

  @ManyToOne(() => Canton, { nullable: false })
  @JoinColumn({ name: 'canton_bfs_number' })
  canton!: Canton;
}
