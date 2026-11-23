import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, hasStoredSession, refreshSession, setTokens } from "./api";
import type { Department, ProfileValues, User } from "./types";

type Status = "loading" | "anonymous" | "authenticated";

interface AuthState {
  status: Status;
  user: User | null;
  departments: Department[];
  loginWithGoogle: (idToken: string) => Promise<User>;
  updateProfile: (values: Partial<ProfileValues>) => Promise<User>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<Status>("loading");
  const [user, setUser] = useState<User | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);

  // Restore a previous session from the stored refresh token.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (hasStoredSession() && (await refreshSession())) {
        try {
          const me = await api.me();
          if (!cancelled) {
            setUser(me);
            setStatus("authenticated");
          }
          return;
        } catch {
          setTokens(null);
        }
      }
      if (!cancelled) setStatus("anonymous");
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // The dropdowns need the department list as soon as someone is signed in.
  useEffect(() => {
    if (status !== "authenticated") return;
    api.departments().then(setDepartments).catch(() => setDepartments([]));
  }, [status]);

  const loginWithGoogle = useCallback(async (idToken: string) => {
    const result = await api.loginWithGoogle(idToken);
    setTokens(result);
    setUser(result.user);
    setStatus("authenticated");
    return result.user;
  }, []);

  const updateProfile = useCallback(async (values: Partial<ProfileValues>) => {
    const result = await api.updateProfile(values);
    setTokens(result); // the old access token is stale after a role change
    setUser(result.user);
    return result.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } catch {
      /* already invalid on the server: nothing more to revoke */
    }
    setTokens(null);
    setUser(null);
    setDepartments([]);
    setStatus("anonymous");
  }, []);

  const value = useMemo(
    () => ({ status, user, departments, loginWithGoogle, updateProfile, logout }),
    [status, user, departments, loginWithGoogle, updateProfile, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
