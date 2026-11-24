import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { api, clearSession, getStoredUser, getToken, setSession } from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getStoredUser());
  const [loading, setLoading] = useState(Boolean(getToken()));

  useEffect(() => {
    if (!getToken()) return;
    api
      .me()
      .then((data) => {
        setUser(data);
        setSession(getToken(), data);
      })
      .catch(() => {
        clearSession();
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      async signup(payload) {
        const data = await api.signup(payload);
        setSession(data.access_token, data.user);
        setUser(data.user);
        return data;
      },
      async login(payload) {
        const data = await api.login(payload);
        setSession(data.access_token, data.user);
        setUser(data.user);
        return data;
      },
      logout() {
        clearSession();
        setUser(null);
      },
    }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
