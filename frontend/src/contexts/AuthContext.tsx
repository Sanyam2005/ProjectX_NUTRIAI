import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

import {
  fetchMe,
  loginGuest,
  loginMicrosoft,
  loginPassword,
  logout as apiLogout,
  signupPassword,
} from "@/api/auth";
import { tokenStorage } from "@/api/client";
import type { User } from "@/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  signInGuest: () => Promise<void>;
  signInMicrosoft: (email: string, name: string) => Promise<void>;
  signInPassword: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name: string) => Promise<void>;
  signOut: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!tokenStorage.get()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await fetchMe();
      setUser(me);
    } catch {
      tokenStorage.clear();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const signInGuest = useCallback(async () => {
    const res = await loginGuest();
    setUser(res.user);
  }, []);

  const signInMicrosoft = useCallback(async (email: string, name: string) => {
    const res = await loginMicrosoft(email, name);
    setUser(res.user);
  }, []);

  const signInPassword = useCallback(async (email: string, password: string) => {
    const res = await loginPassword(email, password);
    setUser(res.user);
  }, []);

  const signUp = useCallback(async (email: string, password: string, name: string) => {
    const res = await signupPassword(email, password, name);
    setUser(res.user);
  }, []);

  const signOut = useCallback(async () => {
    await apiLogout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, loading, signInGuest, signInMicrosoft, signInPassword, signUp, signOut, refresh }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth outside AuthProvider");
  return ctx;
}
