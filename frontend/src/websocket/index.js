import { WS_BASE } from '../api/config';
import { tokenStorage } from '../auth/tokenStorage';
import { subscribeToUrl, getChannelState, reconnectAll } from './connectionManager';

const channelBaseUrls = {
  dashboard: `${WS_BASE}/ws/dashboard`,
  trips: `${WS_BASE}/ws/trips`,
  alerts: `${WS_BASE}/ws/alerts`,
};

function withToken(url) {
  const token = tokenStorage.get();
  if (!token) return url;
  const separator = url.includes('?') ? '&' : '?';
  return `${url}${separator}token=${encodeURIComponent(token)}`;
}

function subscribeToChannel(channelName, handlers) {
  const baseUrl = channelBaseUrls[channelName];
  if (!baseUrl) {
    console.error(`[ws] Unknown channel "${channelName}".`, Object.keys(channelBaseUrls));
    return () => {};
  }
  return subscribeToUrl(withToken(baseUrl), handlers);
}

function getState(channelName) {
  const baseUrl = channelBaseUrls[channelName];
  if (!baseUrl) return 'offline';
  return getChannelState(withToken(baseUrl));
}

export { subscribeToChannel, getState, reconnectAll, channelBaseUrls };