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

export { ApiError, NetworkError, TimeoutError, PayloadError, DEFAULT_ERROR_MESSAGE };
