const HEARTBEAT_INTERVAL_MS = 30000;
const STALE_AFTER_MS = 45000;
const RECONNECT_BASE_MS = 1000;
const RECONNECT_MAX_MS = 30000;

const WS_AUTH_REJECT_CODE = 4401;

function withJitter(delay) {
  return delay + Math.floor(Math.random() * 500);
}

function createChannel(getUrl) {
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

  function startHeartbeat() {
    clearInterval(heartbeatTimer);
    heartbeatTimer = null;
    heartbeatTimer = setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        try {
          ws.send(JSON.stringify({ type: 'ping' }));
        } catch {
          // ignore
        }
      }
      if (Date.now() - lastActivity > STALE_AFTER_MS) {
        handleStaleConnection();
      }
    }, HEARTBEAT_INTERVAL_MS);
  }

  function handleStaleConnection() {
    clearInterval(heartbeatTimer);
    heartbeatTimer = null;
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
    scheduleReconnect();
  }

  function scheduleReconnect() {
    const delay = withJitter(
      Math.min(RECONNECT_BASE_MS * 2 ** reconnectAttempts, RECONNECT_MAX_MS),
    );
    reconnectAttempts += 1;
    clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(() => openSocket(), delay);
  }

  function forceReconnect() {
    clearInterval(heartbeatTimer);
    heartbeatTimer = null;
    if (ws) {
      ws.onclose = null;
      try {
        ws.close();
      } catch {
        // ignore
      }
      ws = null;
    }
    reconnectAttempts = 0;
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
    openSocket();
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
    setState('connecting');

    // Read the current token at connection time, not at channel creation time.
    // This ensures reconnectAll() picks up fresh tokens after login.
    const url = getUrl();

    try {
      ws = new WebSocket(url);
    } catch {
      scheduleReconnect();
      return;
    }

    ws.onopen = () => {
      reconnectAttempts = 0;
      lastActivity = Date.now();
      setState('live');
      startHeartbeat();
    };

    ws.onmessage = (event) => {
      lastActivity = Date.now();
      setState('live');
      let message;
      try {
        message = JSON.parse(event.data);
      } catch {
        return;
      }
      handlers.forEach((handler) => handler.onMessage(message));
    };

    ws.onclose = (event) => {
      clearInterval(heartbeatTimer);
      heartbeatTimer = null;
      // The server rejected our session token (missing/invalid/expired).
      // Retrying cannot succeed while the session is unusable, so stay
      // offline until the app reconnects with a fresh session.
      if (event && event.code === WS_AUTH_REJECT_CODE) {
        manuallyClosed = true;
        setState('offline');
        return;
      }
      if (manuallyClosed) {
        setState('offline');
        return;
      }
      // A live socket dropping shows a brief CONNECTING window while the first
      // reconnect is scheduled; once attempts start failing, stay OFFLINE.
      setState(state === 'live' ? 'connecting' : 'offline');
      scheduleReconnect();
    };

    ws.onerror = () => {
      setState('offline');
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

  return { subscribe, close, getState, forceReconnect };
}

const channels = new Map();

function subscribeToUrl(key, getUrl, handlers) {
  let channel = channels.get(key);
  if (!channel) {
    channel = createChannel(getUrl);
    channels.set(key, channel);
  }
  return channel.subscribe(handlers);
}

function getChannelState(key) {
  const channel = channels.get(key);
  return channel ? channel.getState() : 'offline';
}

function reconnectAll() {
  // Force each existing channel to reconnect with the current token.
  // getUrl() is called inside openSocket(), so it reads the live token
  // from tokenStorage at reconnect time — not the stale URL from creation.
  // We do NOT close/destroy channels because LiveDataProvider's subscription
  // effect has stable deps and won't re-run to re-subscribe.
  channels.forEach((channel) => channel.forceReconnect());
}

export { subscribeToUrl, getChannelState, reconnectAll, WS_AUTH_REJECT_CODE };
