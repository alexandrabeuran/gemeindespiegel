import { Logger } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app/app.module';
import { listenPort } from './app/listen-port';
import { createValidationPipe } from './app/validation-pipe';

async function bootstrap() {
  const port = listenPort(process.env);
  const app = await NestFactory.create(AppModule);
  app.setGlobalPrefix('api');
  app.useGlobalPipes(createValidationPipe());
  await app.listen(port);
  // The e2e tests wait for this line before sending requests.
  Logger.log(`API is running on http://localhost:${port}/api`);
}

bootstrap();
