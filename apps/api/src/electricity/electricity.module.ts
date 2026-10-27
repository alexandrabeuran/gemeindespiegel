import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { GridOperator } from './grid-operator.entity';
import { MunicipalityPrice } from './municipality-price.entity';
import { Tariff } from './tariff.entity';

@Module({
  imports: [
    TypeOrmModule.forFeature([GridOperator, Tariff, MunicipalityPrice]),
  ],
})
export class ElectricityModule {}
