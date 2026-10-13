import { createContext, ReactNode, useContext, useEffect, useState } from "react";
import { api, tokens } from "../lib/api";
import type { User } from "../types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState>({
  user: null,
  loading: true,
  login: async () => {},
  logout: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tokens.access) {
      setLoading(false);
      return;
    }
    api
      .get<User>("/auth/me")
      .then((r) => setUser(r.data))
      .catch(() => tokens.clear())
      .finally(() => setLoading(false));
  }, []);

  async function login(username: string, password: string) {
    const resp = await api.post("/auth/login", { username, password });
    tokens.set(resp.data.access_token, resp.data.refresh_token);
    const me = await api.get<User>("/auth/me");
    setUser(me.data);
  }

  async function logout() {
    try {
      await api.post("/auth/logout");
    } finally {
      tokens.clear();
      setUser(null);
    }
  }

  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
