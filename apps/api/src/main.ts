import { Logger } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app/app.module';
import { createValidationPipe } from './app/validation-pipe';

// 3333 because the web app already uses 3000 (C3 SPEC).
const DEFAULT_PORT = 3333;

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.setGlobalPrefix('api');
  app.useGlobalPipes(createValidationPipe());
  const port = Number(process.env['PORT'] ?? DEFAULT_PORT);
  await app.listen(port);
  // The e2e tests wait for this line before sending requests.
  Logger.log(`API is running on http://localhost:${port}/api`);
}

bootstrap();
