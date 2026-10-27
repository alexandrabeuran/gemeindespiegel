import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Canton } from './canton.entity';
import { Municipality } from './municipality.entity';

@Module({
  // forFeature is what autoLoadEntities picks up; an entity that is not listed here is unknown to the app.
  imports: [TypeOrmModule.forFeature([Canton, Municipality])],
})
export class MunicipalitiesModule {}
