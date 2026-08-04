const API_BASE = (import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1').replace(/\/+$/, '');
const WS_BASE = (import.meta.env.VITE_WS_BASE || 'ws://localhost:8000').replace(/\/+$/, '');

const REQUEST_TIMEOUT_MS = 15000;

export { API_BASE, WS_BASE, REQUEST_TIMEOUT_MS };
