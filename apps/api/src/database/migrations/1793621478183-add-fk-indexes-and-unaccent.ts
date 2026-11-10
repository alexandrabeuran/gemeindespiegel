import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddFkIndexesAndUnaccent1793621478183
  implements MigrationInterface
{
  name = 'AddFkIndexesAndUnaccent1793621478183';

  public async up(queryRunner: QueryRunner): Promise<void> {
    // Written by hand: TypeORM does not track extensions, so migration:generate cannot create this.
    await queryRunner.query(`
            CREATE EXTENSION "unaccent"
        `);
    await queryRunner.query(`
            CREATE INDEX "idx_municipality_canton" ON "municipality" ("canton_bfs_number")
        `);
    await queryRunner.query(`
            CREATE INDEX "idx_tariff_grid_operator" ON "tariff" ("grid_operator_elcom_id")
        `);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`
            DROP INDEX "public"."idx_tariff_grid_operator"
        `);
    await queryRunner.query(`
            DROP INDEX "public"."idx_municipality_canton"
        `);
    await queryRunner.query(`
            DROP EXTENSION "unaccent"
        `);
  }
}
