import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { databaseOptions } from '../database/database-options';
import { ElectricityModule } from '../electricity/electricity.module';
import { MunicipalitiesModule } from '../municipalities/municipalities.module';
import { AppController } from './app.controller';
import { AppService } from './app.service';

@Module({
  imports: [
    // forRootAsync reads the environment when Nest starts, not when this file is imported.
    TypeOrmModule.forRootAsync({
      useFactory: () => ({
        ...databaseOptions(process.env),
        // Entities register themselves via TypeOrmModule.forFeature, because webpack bundles the app.
        autoLoadEntities: true,
      }),
    }),
    MunicipalitiesModule,
    ElectricityModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
