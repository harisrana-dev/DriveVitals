import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

vi.mock('../auth/tokenStorage', () => ({
  tokenStorage: {
    get: vi.fn(() => null),
    set: vi.fn(),
    clear: vi.fn(),
  },
}));

import { apiClient, unwrapEnvelope } from './apiClient';
import { endpoints } from './endpoints';
import { ApiError, TimeoutError, NetworkError } from './errors';
import { tokenStorage } from '../auth/tokenStorage';

function jsonResponse({ status = 200, ok, body }) {
  return {
    ok: ok ?? (status >= 200 && status < 300),
    status,
    text: vi.fn(async () => (body === undefined ? '' : JSON.stringify(body))),
  };
}

const dispatchEvent = vi.fn();

beforeEach(() => {
  tokenStorage.get.mockReturnValue(null);
  dispatchEvent.mockClear();
  vi.stubGlobal('window', { dispatchEvent });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('unwrapEnvelope', () => {
  it('extracts data and count from an envelope', () => {
    expect(unwrapEnvelope({ data: { id: 1 }, count: 3 })).toEqual({
      data: { id: 1 },
      count: 3,
    });
  });

  it('defaults count to null when absent', () => {
    expect(unwrapEnvelope({ data: [] })).toEqual({ data: [], count: null });
  });

  it('passes through non-envelope payloads', () => {
    expect(unwrapEnvelope({ foo: 1 })).toEqual({ data: { foo: 1 }, count: null });
    expect(unwrapEnvelope(null)).toEqual({ data: null, count: null });
  });
});

describe('apiClient auth behavior', () => {
  it('does not attach Authorization for auth-free endpoints', async () => {
    tokenStorage.get.mockReturnValue('tok-1');
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(jsonResponse({ body: { data: { user: {} } } }));

    await apiClient.post(endpoints.auth.login, { email: 'a', password: 'b' });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/auth\/login$/);
    expect(tokenStorage.get).toHaveBeenCalled();
    expect(init.headers.Authorization).toBeUndefined();
  });

  it('attaches the stored token as a Bearer header for protected endpoints', async () => {
    tokenStorage.get.mockReturnValue('tok-1');
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(jsonResponse({ body: { data: [] } }));

    await apiClient.get(endpoints.fleet.list);

    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers.Authorization).toBe('Bearer tok-1');
  });

  it('sends no Authorization header when no token is stored', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(jsonResponse({ body: { data: [] } }));

    await apiClient.get(endpoints.fleet.list);

    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers.Authorization).toBeUndefined();
  });

  it('dispatches auth:expired on a 401 from a protected endpoint', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse({ status: 401, body: { detail: 'INVALID_OR_EXPIRED_TOKEN' } })
    );

    await expect(apiClient.get(endpoints.auth.me)).rejects.toBeInstanceOf(ApiError);
    expect(dispatchEvent).toHaveBeenCalledTimes(1);
    const [event] = dispatchEvent.mock.calls[0];
    expect(event.type).toBe('auth:expired');
  });

  it('does not dispatch auth:expired when the caller supplied Authorization', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse({ status: 401, body: { detail: 'INVALID_OR_EXPIRED_TOKEN' } })
    );

    await expect(
      apiClient.get(endpoints.auth.me, { headers: { Authorization: 'Bearer tok-1' } })
    ).rejects.toBeInstanceOf(ApiError);
    expect(dispatchEvent).not.toHaveBeenCalled();
  });

  it('does not dispatch auth:expired for a 401 from auth-free endpoints', async () => {
    tokenStorage.get.mockReturnValue('stale');
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse({ status: 401, body: { detail: 'INVALID_CREDENTIALS' } })
    );

    await expect(
      apiClient.post(endpoints.auth.login, { email: 'a', password: 'b' })
    ).rejects.toBeInstanceOf(ApiError);
    expect(dispatchEvent).not.toHaveBeenCalled();
  });
});

describe('apiClient errors', () => {
  it('wraps a 409 detail into an ApiError', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse({ status: 409, body: { detail: 'EMAIL_EXISTS' } })
    );

    await expect(apiClient.post(endpoints.auth.signup, {})).rejects.toMatchObject({
      status: 409,
      detail: 'EMAIL_EXISTS',
    });
  });

  it('throws TimeoutError when the request is aborted', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(
      Object.assign(new Error('aborted'), { name: 'AbortError' })
    );

    await expect(apiClient.get('/anything')).rejects.toBeInstanceOf(TimeoutError);
  });

  it('throws NetworkError on a failed fetch without a response', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(apiClient.get('/anything')).rejects.toBeInstanceOf(NetworkError);
  });
});