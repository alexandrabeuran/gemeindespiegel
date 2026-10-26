import { Column, Entity, PrimaryColumn } from 'typeorm';

@Entity({ name: 'canton' })
export class Canton {
  // The BFS assigns the number (1 = Zürich), so the database must not generate it.
  @PrimaryColumn({ name: 'bfs_number', type: 'smallint' })
  bfsNumber!: number;

  @Column({ name: 'abbreviation', type: 'char', length: 2, unique: true })
  abbreviation!: string;

  @Column({ name: 'name', type: 'text' })
  name!: string;
}
