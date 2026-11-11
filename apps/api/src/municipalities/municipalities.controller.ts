import { Controller, Get, Query } from '@nestjs/common';
import { ListMunicipalitiesQuery } from './list-municipalities.query';
import { MunicipalitiesService } from './municipalities.service';
import type { MunicipalityList } from './municipality-list.response';

@Controller('municipalities')
export class MunicipalitiesController {
  constructor(private readonly municipalities: MunicipalitiesService) {}

  // The global ValidationPipe turns the raw query string into a checked ListMunicipalitiesQuery before this runs.
  @Get()
  list(@Query() query: ListMunicipalitiesQuery): Promise<MunicipalityList> {
    return this.municipalities.list(query);
  }
}
