const DEFAULT_ERROR_MESSAGE = 'Something went wrong. Please try again.';

class ApiError extends Error {
  constructor(status, detail, ...rest) {
    const message = typeof detail === 'string' ? detail : DEFAULT_ERROR_MESSAGE;
    super(message, ...rest);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

class NetworkError extends Error {
  constructor(cause) {
    super('Network request failed. Check your connection.', { cause });
    this.name = 'NetworkError';
  }
}

class TimeoutError extends Error {
  constructor() {
    super('The request timed out. Please try again.');
    this.name = 'TimeoutError';
  }
}

class PayloadError extends Error {
  constructor() {
    super('The server returned an unexpected response.');
    this.name = 'PayloadError';
  }
}

const IGNORED_LOC_SEGMENTS = new Set(['body', 'query', 'path']);

/**
 * Render a FastAPI/Pydantic 422 `detail` array as a single readable string,
 * e.g. "license_number: Field required; vin: Field required".
 * Returns null when the detail is not a validation-error array.
 */
function formatValidationDetail(detail) {
  if (!Array.isArray(detail)) return null;
  const parts = detail
    .map((entry) => {
      if (!entry || typeof entry !== 'object') {
        return typeof entry === 'string' ? entry : '';
      }
      const loc = Array.isArray(entry.loc) ? entry.loc : [];
      const field = loc
        .filter((segment) => !IGNORED_LOC_SEGMENTS.has(segment))
        .join('.');
      const message = typeof entry.msg === 'string' ? entry.msg : 'Invalid value';
      return field ? `${field}: ${message}` : message;
    })
    .filter(Boolean);
  return parts.length ? parts.join('; ') : null;
}

/**
 * Single entry point for turning any thrown value into a string that is safe
 * to render as a React child. Raw `ApiError.detail` may be an object or an
 * array (FastAPI 422 bodies), which React refuses to render.
 */
function formatApiError(error, fallback = DEFAULT_ERROR_MESSAGE) {
  const detail = error?.detail;
  const fromValidation = formatValidationDetail(detail);
  if (fromValidation) return fromValidation;
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (detail && typeof detail === 'object') {
    const message = typeof detail.message === 'string' ? detail.message : '';
    if (message) return message;
  }
  if (typeof error?.message === 'string' && error.message.trim()) {
    return error.message;
  }
  return fallback;
}

export {
  ApiError,
  NetworkError,
  TimeoutError,
  PayloadError,
  formatApiError,
  formatValidationDetail,
  DEFAULT_ERROR_MESSAGE,
};
