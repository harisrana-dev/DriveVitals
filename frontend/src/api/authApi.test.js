import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('./apiClient', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

import { authApi } from './authApi';
import { endpoints } from './endpoints';
import { apiClient } from './apiClient';

beforeEach(() => {
  vi.clearAllMocks();
});

describe('auth endpoints', () => {
  it('exposes the canonical auth paths', () => {
    expect(endpoints.auth.signup).toBe('/auth/signup');
    expect(endpoints.auth.login).toBe('/auth/login');
    expect(endpoints.auth.logout).toBe('/auth/logout');
    expect(endpoints.auth.me).toBe('/auth/me');
  });
});

describe('authApi', () => {
  it('signup posts normalized fields to the signup endpoint', async () => {
    apiClient.post.mockResolvedValue({ data: { user: { user_id: 'u-1' } }, count: null });

    const result = await authApi.signup({
      fullName: 'Ada Lovelace',
      email: 'ada@example.com',
      password: 'supersecret',
    });

    expect(apiClient.post).toHaveBeenCalledWith(endpoints.auth.signup, {
      full_name: 'Ada Lovelace',
      email: 'ada@example.com',
      password: 'supersecret',
    });
    expect(result.data.user.user_id).toBe('u-1');
  });

  it('login posts credentials to the login endpoint', async () => {
    apiClient.post.mockResolvedValue({ data: { token: 'tok-1', user: {} }, count: null });

    await authApi.login({ email: 'ada@example.com', password: 'supersecret' });

    expect(apiClient.post).toHaveBeenCalledWith(endpoints.auth.login, {
      email: 'ada@example.com',
      password: 'supersecret',
    });
  });

  it('logout posts with a caller-supplied Authorization header', async () => {
    apiClient.post.mockResolvedValue({ data: null, count: null });

    await authApi.logout('tok-1');

    expect(apiClient.post).toHaveBeenCalledWith(
      endpoints.auth.logout,
      undefined,
      { headers: { Authorization: 'Bearer tok-1' } }
    );
  });

  it('logout sends no Authorization header when the token is missing', async () => {
    apiClient.post.mockResolvedValue({ data: null, count: null });

    await authApi.logout(null);

    expect(apiClient.post).toHaveBeenCalledWith(
      endpoints.auth.logout,
      undefined,
      { headers: undefined }
    );
  });

  it('me requests the profile with the supplied token', async () => {
    apiClient.get.mockResolvedValue({
      data: { user_id: 'u-1', email: 'ada@example.com', role: 'operator' },
      count: null,
    });

    const result = await authApi.me('tok-1');

    expect(apiClient.get).toHaveBeenCalledWith(
      endpoints.auth.me,
      { headers: { Authorization: 'Bearer tok-1' } }
    );
    expect(result.data.email).toBe('ada@example.com');
  });
});