import { listenPort } from './listen-port';

describe('listenPort', () => {
  it('uses 3333 when PORT is missing', () => {
    expect(listenPort({})).toBe(3333);
  });

  // An empty line like "PORT=" in a .env file must not mean "any free port".
  it('uses 3333 when PORT is empty', () => {
    expect(listenPort({ PORT: '' })).toBe(3333);
  });

  it('uses PORT when it is set', () => {
    expect(listenPort({ PORT: '4000' })).toBe(4000);
  });

  it.each(['abc', '0', '-1', '70000'])('rejects PORT=%s', (value) => {
    expect(() => listenPort({ PORT: value })).toThrow('PORT');
  });
});
