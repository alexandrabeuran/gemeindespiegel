import { ValidationPipe } from '@nestjs/common';

// One factory for main.ts and the tests, so the tests check the settings the running API really uses.
export function createValidationPipe(): ValidationPipe {
  return new ValidationPipe({
    // Creates a real class instance, so defaults and @Type conversions apply.
    transform: true,
    // Unknown parameters are an error instead of being dropped silently (SPEC: 400 for unknown parameters).
    whitelist: true,
    forbidNonWhitelisted: true,
  });
}
