import { type ChildProcess, spawn } from 'node:child_process';
import { once } from 'node:events';
import { createServer } from 'node:net';
import { join } from 'node:path';

// The webpack bundle from `nx build api` (test-e2e depends on build). Starting it instead of AppModule
// tests what ships, and avoids loading the ESM-only @nestjs/typeorm into Jest's CommonJS runtime.
const MAIN = join(
  __dirname,
  '..',
  '..',
  '..',
  'dist',
  'apps',
  'api',
  'main.js',
);
const STARTUP_TIMEOUT_MS = 15_000;

export interface RunningApi {
  url: string;
  stop(): Promise<void>;
}

export async function startApi(): Promise<RunningApi> {
  const port = await freePort();
  const child = spawn(process.execPath, [MAIN], {
    env: { ...process.env, PORT: String(port) },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  await waitForStartup(child);

  return {
    url: `http://localhost:${port}`,
    async stop() {
      // A process killed by a signal keeps exitCode null and sets signalCode; waiting for "exit" again would hang.
      if (child.exitCode === null && child.signalCode === null) {
        child.kill('SIGTERM');
        await once(child, 'exit');
      }
    },
  };
}

// Asks the OS for an unused port, so a running dev server on 3333 does not collide with the test.
async function freePort(): Promise<number> {
  const server = createServer();
  server.listen(0);
  await once(server, 'listening');
  const address = server.address();
  server.close();
  if (address === null || typeof address === 'string') {
    throw new Error('Could not get a free port');
  }
  return address.port;
}

// main.ts logs this line after app.listen, so requests from then on reach the app.
function waitForStartup(child: ChildProcess): Promise<void> {
  let output = '';
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      child.kill('SIGTERM');
      reject(new Error(`API did not start in time:\n${output}`));
    }, STARTUP_TIMEOUT_MS);

    const collect = (chunk: Buffer) => {
      output += chunk.toString();
      if (output.includes('API is running')) {
        clearTimeout(timer);
        resolve();
      }
    };
    child.stdout?.on('data', collect);
    child.stderr?.on('data', collect);
    // Without this, a crash at startup (e.g. a missing variable) would only show up as the timeout.
    child.once('exit', (code) => {
      clearTimeout(timer);
      reject(new Error(`API exited with code ${code}:\n${output}`));
    });
  });
}
