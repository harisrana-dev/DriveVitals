import { WS_BASE } from '../api/config';
import { subscribeToUrl, getChannelState, reconnectAll } from './connectionManager';

const channels = {
  dashboard: `${WS_BASE}/ws/dashboard`,
  trips: `${WS_BASE}/ws/trips`,
};

function subscribeToChannel(channelName, handlers) {
  const url = channels[channelName];
  if (!url) {
    console.error(`[ws] Unknown channel "${channelName}".`, Object.keys(channels));
    return () => {};
  }
  return subscribeToUrl(url, handlers);
}

function getState(channelName) {
  const url = channels[channelName];
  if (!url) return 'offline';
  return getChannelState(url);
}

export { subscribeToChannel, getState, channels, reconnectAll };
