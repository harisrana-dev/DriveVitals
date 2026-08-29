import { WS_BASE } from '../api/config';
import { tokenStorage } from '../auth/tokenStorage';
import { subscribeToUrl, getChannelState, reconnectAll } from './connectionManager';

const channelNames = ['dashboard', 'trips', 'alerts'];

function makeGetUrl(channelName) {
  return () => {
    const token = tokenStorage.get();
    const base = `${WS_BASE}/ws/${channelName}`;
    if (!token) return base;
    return `${base}?token=${encodeURIComponent(token)}`;
  };
}

function subscribeToChannel(channelName, handlers) {
  if (!channelNames.includes(channelName)) {
    console.error(`[ws] Unknown channel "${channelName}".`, channelNames);
    return () => {};
  }
  const getUrl = makeGetUrl(channelName);
  return subscribeToUrl(channelName, getUrl, handlers);
}

function getState(channelName) {
  return getChannelState(channelName);
}

export { subscribeToChannel, getState, reconnectAll, channelNames };