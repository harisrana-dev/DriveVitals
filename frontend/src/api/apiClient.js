import { API_BASE, REQUEST_TIMEOUT_MS } from './config';
import { ApiError, NetworkError, TimeoutError, PayloadError } from './errors';
import { tokenStorage } from '../auth/tokenStorage';

const LOG_TAG = '[api]';

const AUTH_FREE_PATHS = new Set(['/auth/login', '/auth/signup']);

function isAbsoluteUrl(path) {
  return /^https?:\/\//i.test(path);
}

function buildUrl(path) {
  if (isAbsoluteUrl(path)) return path;
  const [scheme, rest] = API_BASE.split('://');
  const joined = `${rest.replace(/\/+$/, '')}/${path.replace(/^\/+/, '')}`;
  return `${scheme}://${joined}`;
}

function applyTimeout(signal, timeoutMs) {
  if (signal && signal.aborted) return signal;
  if (timeoutMs <= 0) return signal;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const onAbort = () => {
    clearTimeout(timer);
    controller.abort();
  };
  if (signal) {
    if (signal.aborted) {
      clearTimeout(timer);
      return signal;
    }
    signal.addEventListener('abort', onAbort, { once: true });
  }
  return {
    signal: controller.signal,
    dispose() {
      clearTimeout(timer);
      if (signal) signal.removeEventListener('abort', onAbort);
    },
  };
}

function unwrapEnvelope(payload) {
  if (payload !== null && typeof payload === 'object' && 'data' in payload) {
    return { data: payload.data, count: payload.count ?? null };
  }
  return { data: payload, count: null };
}

async function parseResponse(response) {
  const text = await response.text();
  let payload = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      if (response.ok) throw new PayloadError();
    }
  }

  if (!response.ok) {
    const detail = payload?.detail ?? payload?.message ?? `Request failed (${response.status})`;
    throw new ApiError(response.status, detail);
  }

  return unwrapEnvelope(payload);
}

async function request(path, options = {}) {
  const { method = 'GET', body, params, timeoutMs = REQUEST_TIMEOUT_MS, signal } = options;

  let url = buildUrl(path);
  if (params && Object.keys(params).length > 0) {
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) search.set(key, value);
    }
    const qs = search.toString();
    if (qs) url = `${url}${url.includes('?') ? '&' : '?'}${qs}`;
  }

  const controller = applyTimeout(signal, timeoutMs);

  const isAuthFreePath = AUTH_FREE_PATHS.has(path);
  const token = tokenStorage.get();
  let headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  if (token && !isAuthFreePath && !headers.Authorization) {
    headers = { ...headers, Authorization: `Bearer ${token}` };
  }

  try {
    const response = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
    if (
      response.status === 401 &&
      !isAuthFreePath &&
      !options.headers?.Authorization
    ) {
      window.dispatchEvent(new CustomEvent('auth:expired'));
    }
    return await parseResponse(response);
  } catch (error) {
    if (error instanceof ApiError) {
      console.error(`${LOG_TAG} ${method} ${url} ->`, error.status, error.detail);
      throw error;
    }
    if (error && error.name === 'AbortError') {
      throw new TimeoutError();
    }
    const networkError = new NetworkError(error);
    console.error(`${LOG_TAG} ${method} ${url} ->`, networkError.message, error);
    throw networkError;
  } finally {
    if (controller.dispose) controller.dispose();
  }
}

const apiClient = {
  get(path, options) {
    return request(path, { ...options, method: 'GET' });
  },
  post(path, body, options) {
    return request(path, { ...options, method: 'POST', body });
  },
  put(path, body, options) {
    return request(path, { ...options, method: 'PUT', body });
  },
  patch(path, body, options) {
    return request(path, { ...options, method: 'PATCH', body });
  },
  delete(path, options) {
    return request(path, { ...options, method: 'DELETE' });
  },
};

export { apiClient, unwrapEnvelope, PayloadError };
