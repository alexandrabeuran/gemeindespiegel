// Separate from jest.config.cts, so `nx test api` stays fast and runs without Docker.
module.exports = {
  displayName: 'api-e2e',
  preset: '../../jest.preset.cjs',
  testEnvironment: 'node',
  transform: {
    '^.+\\.[tj]s$': ['ts-jest', { tsconfig: '<rootDir>/tsconfig.spec.json' }],
  },
  moduleFileExtensions: ['ts', 'js', 'html'],
  testMatch: ['<rootDir>/test/**/*.e2e-spec.ts'],
  // One container for all e2e files: starting PostgreSQL and migrating takes several seconds.
  globalSetup: '<rootDir>/test/global-setup.ts',
  globalTeardown: '<rootDir>/test/global-teardown.ts',
  // Pulling the image on a fresh machine can take a while.
  testTimeout: 30_000,
};
