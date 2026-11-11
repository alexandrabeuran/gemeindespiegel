import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Canton } from './canton.entity';
import { MunicipalitiesController } from './municipalities.controller';
import { MunicipalitiesService } from './municipalities.service';
import { Municipality } from './municipality.entity';

@Module({
  // forFeature is what autoLoadEntities picks up; an entity that is not listed here is unknown to the app.
  imports: [TypeOrmModule.forFeature([Canton, Municipality])],
  controllers: [MunicipalitiesController],
  providers: [MunicipalitiesService],
})
export class MunicipalitiesModule {}
