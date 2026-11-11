// 3333 because the web app already uses 3000 (C3 SPEC).
const DEFAULT_PORT = 3333;

// Fail at startup with a clear message instead of listening somewhere unexpected.
export function listenPort(env: Record<string, string | undefined>): number {
  const raw = env['PORT'];
  // `||` instead of `??`: an empty PORT from a .env file counts as not set.
  if (!raw) {
    return DEFAULT_PORT;
  }
  const port = Number(raw);
  if (!Number.isInteger(port) || port < 1 || port > 65_535) {
    throw new Error(`PORT must be a port number, got "${raw}"`);
  }
  return port;
}
