import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { authApi } from "../api/authApi";
import { tokenStorage } from "../auth/tokenStorage";
import { reconnectAll } from "../websocket";
import { AuthContext } from "./authCtx";

const EXPIRED_EVENT = "auth:expired";

const AUTH_STATUSES = {
  loading: "loading",
  authenticated: "authenticated",
  unauthenticated: "unauthenticated",
};

export function AuthProvider({ children }) {
  const [status, setStatus] = useState(() =>
    tokenStorage.get() ? AUTH_STATUSES.loading : AUTH_STATUSES.unauthenticated
  );
  const [user, setUser] = useState(null);
  const tokenRef = useRef(null);

  const clearSession = useCallback(() => {
    tokenRef.current = null;
    tokenStorage.clear();
    setUser(null);
    setStatus(AUTH_STATUSES.unauthenticated);
  }, []);

  const applyUser = useCallback((nextUser, token) => {
    tokenRef.current = token ?? null;
    if (token) tokenStorage.set(token);
    setUser(nextUser);
    setStatus(AUTH_STATUSES.authenticated);
  }, []);

  const refreshUser = useCallback(async () => {
    const token = tokenRef.current;
    if (!token) return null;
    try {
      const result = await authApi.me(token);
      const nextUser = result?.data ?? null;
      setUser(nextUser);
      return nextUser;
    } catch {
      return null;
    }
  }, []);

  const login = useCallback(
    async ({ email, password }) => {
      const result = await authApi.login({ email, password });
      const token = result?.data?.token ?? null;
      const nextUser = result?.data?.user ?? null;
      applyUser(nextUser, token);
      setStatus(AUTH_STATUSES.authenticated);
      reconnectAll();
      return nextUser;
    },
    [applyUser]
  );

  const signup = useCallback(
    async ({ fullName, email, password }) => {
      const result = await authApi.signup({ email, password, fullName });
      return result?.data?.user ?? null;
    },
    []
  );

  const logout = useCallback(async () => {
    const token = tokenRef.current;
    tokenRef.current = null;
    tokenStorage.clear();
    setUser(null);
    setStatus(AUTH_STATUSES.unauthenticated);
    if (token) {
      try {
        await authApi.logout(token);
      } catch {
        // The session is gone from the client regardless of the network.
      }
    }
    reconnectAll();
  }, []);

  useEffect(() => {
    const token = tokenStorage.get();
    if (!token) return undefined;
    tokenRef.current = token;

    let cancelled = false;
    (async () => {
      try {
        const result = await authApi.me(token);
        if (cancelled) return;
        if (result?.data) {
          applyUser(result.data, token);
        } else {
          clearSession();
        }
      } catch {
        if (cancelled) return;
        clearSession();
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [applyUser, clearSession]);

  useEffect(() => {
    function handleExpired() {
      tokenRef.current = null;
      tokenStorage.clear();
      setUser(null);
      setStatus(AUTH_STATUSES.unauthenticated);
      reconnectAll();
    }
    window.addEventListener(EXPIRED_EVENT, handleExpired);
    return () => window.removeEventListener(EXPIRED_EVENT, handleExpired);
  }, []);

  const value = useMemo(
    () => ({
      status,
      user,
      isAuthenticated: status === AUTH_STATUSES.authenticated,
      isLoading: status === AUTH_STATUSES.loading,
      login,
      signup,
      logout,
      refreshUser,
      clearSession,
      applyUser,
    }),
    [status, user, login, signup, logout, refreshUser, clearSession, applyUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}