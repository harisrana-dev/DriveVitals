const HEARTBEAT_INTERVAL_MS = 30000;
const STALE_AFTER_MS = 45000;
const RECONNECT_BASE_MS = 1000;
const RECONNECT_MAX_MS = 30000;

function withJitter(delay) {
  return delay + Math.floor(Math.random() * 500);
}

function createChannel(url) {
  let ws = null;
  let state = 'connecting';
  let reconnectAttempts = 0;
  let reconnectTimer = null;
  let heartbeatTimer = null;
  let lastActivity = 0;
  let manuallyClosed = false;
  const handlers = new Set();
  const stateListeners = new Set();

  function setState(next) {
    if (next === state) return;
    state = next;
    stateListeners.forEach((listener) => listener(next));
  }

  function clearTimers() {
    if (reconnectTimer !== null) clearTimeout(reconnectTimer);
    reconnectTimer = null;
    if (heartbeatTimer !== null) clearInterval(heartbeatTimer);
    heartbeatTimer = null;
  }

  function scheduleReconnect() {
    const delay = withJitter(
      Math.min(RECONNECT_BASE_MS * 2 ** reconnectAttempts, RECONNECT_MAX_MS),
    );
    reconnectAttempts += 1;
    clearTimeout(reconnectTimer);
    setState('reconnecting');
    reconnectTimer = setTimeout(() => openSocket(), delay);
  }

  function forceReconnect() {
    if (ws) {
      ws.onclose = null;
      try {
        ws.close();
      } catch {
        // ignore
      }
      ws = null;
    }
    clearInterval(heartbeatTimer);
    heartbeatTimer = null;
    scheduleReconnect();
  }

  function openSocket() {
    manuallyClosed = false;
    if (ws) {
      ws.onclose = null;
      try {
        ws.close();
      } catch {
        // ignore
      }
      ws = null;
    }
    setState(reconnectAttempts === 0 ? 'connecting' : 'reconnecting');

    try {
      ws = new WebSocket(url);
    } catch {
      scheduleReconnect();
      return;
    }

    ws.onopen = () => {
      reconnectAttempts = 0;
      lastActivity = Date.now();
      setState('connected');
      clearInterval(heartbeatTimer);
      heartbeatTimer = setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
        if (Date.now() - lastActivity > STALE_AFTER_MS) {
          forceReconnect();
        }
      }, HEARTBEAT_INTERVAL_MS);
    };

    ws.onmessage = (event) => {
      lastActivity = Date.now();
      let message;
      try {
        message = JSON.parse(event.data);
      } catch {
        return;
      }
      handlers.forEach((handler) => handler.onMessage(message));
    };

    ws.onclose = () => {
      clearInterval(heartbeatTimer);
      heartbeatTimer = null;
      if (manuallyClosed) {
        setState('offline');
        return;
      }
      scheduleReconnect();
    };

    ws.onerror = () => {
      // onerror is always followed by onclose, which schedules the reconnect.
    };
  }

  function subscribe({ onMessage, onState }) {
    const handler = { onMessage };
    handlers.add(handler);
    if (onState) {
      stateListeners.add(onState);
      onState(state);
    }
    if (ws === null && reconnectTimer === null) {
      openSocket();
    }
    return () => {
      handlers.delete(handler);
      if (onState) stateListeners.delete(onState);
      if (handlers.size === 0) {
        close();
      }
    };
  }

  function close() {
    manuallyClosed = true;
    clearTimers();
    setState('offline');
    if (ws) {
      ws.onclose = null;
      try {
        ws.close();
      } catch {
        // ignore
      }
      ws = null;
    }
    handlers.clear();
    stateListeners.clear();
  }

  function getState() {
    return state;
  }

  return { subscribe, close, getState };
}

const channels = new Map();

function subscribeToUrl(url, handlers) {
  let channel = channels.get(url);
  if (!channel) {
    channel = createChannel(url);
    channels.set(url, channel);
  }
  return channel.subscribe(handlers);
}

function getChannelState(url) {
  const channel = channels.get(url);
  return channel ? channel.getState() : 'offline';
}

export { subscribeToUrl, getChannelState };
