import { BACKEND_URL } from "./config";
import type { AccessPolicy, AuthResponse, Department, ProfileValues, Tokens, User } from "./types";

const REFRESH_KEY = "rolecanvas.refresh";

// The short-lived access token lives only in memory. The refresh token is kept in
// localStorage so a reload does not sign the user out. (Trade-off: readable by any script on
// the page; acceptable for this demo, revisit before production, for example with httpOnly cookies.)
let accessToken: string | null = null;

function readRefresh(): string | null {
  try {
    return localStorage.getItem(REFRESH_KEY);
  } catch {
    return null;
  }
}

export function setTokens(tokens: Tokens | null): void {
  accessToken = tokens?.access ?? null;
  try {
    if (tokens) localStorage.setItem(REFRESH_KEY, tokens.refresh);
    else localStorage.removeItem(REFRESH_KEY);
  } catch {
    /* storage unavailable: the session just will not survive a reload */
  }
}

export function hasStoredSession(): boolean {
  return readRefresh() !== null;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function messageFrom(body: unknown, fallback: string): string {
  if (body && typeof body === "object") {
    const record = body as Record<string, unknown>;
    if (typeof record.detail === "string") return record.detail;
    for (const value of Object.values(record)) {
      if (Array.isArray(value) && typeof value[0] === "string") return value[0];
      if (typeof value === "string") return value;
    }
  }
  return fallback;
}

let refreshing: Promise<boolean> | null = null;

/** Exchange the stored refresh token for a new pair. Concurrent callers share one request. */
export function refreshSession(): Promise<boolean> {
  refreshing ??= (async () => {
    const refresh = readRefresh();
    if (!refresh) return false;
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh }),
      });
      if (!response.ok) {
        setTokens(null);
        return false;
      }
      setTokens((await response.json()) as Tokens);
      return true;
    } catch {
      return false;
    } finally {
      refreshing = null;
    }
  })();
  return refreshing;
}

async function request<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body) headers.set("Content-Type", "application/json");
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  const response = await fetch(`${BACKEND_URL}${path}`, { ...init, headers });

  // 401 usually means the access token expired or is stale after a role change: refresh once.
  if (response.status === 401 && retry && (await refreshSession())) {
    return request<T>(path, init, false);
  }
  if (response.status === 204) return undefined as T;
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, messageFrom(body, `Request failed (${response.status})`));
  return body as T;
}

export const api = {
  loginWithGoogle: (idToken: string) =>
    request<AuthResponse>("/api/auth/google/", { method: "POST", body: JSON.stringify({ id_token: idToken }) }),
  logout: () => {
    const refresh = readRefresh();
    return refresh
      ? request<void>("/api/auth/logout/", { method: "POST", body: JSON.stringify({ refresh }) }, false)
      : Promise.resolve();
  },
  me: () => request<User>("/api/me/"),
  departments: () => request<Department[]>("/api/departments/"),
  access: () => request<AccessPolicy>("/api/me/access/"),
  updateProfile: (values: Partial<ProfileValues>) =>
    request<AuthResponse>("/api/me/", { method: "PATCH", body: JSON.stringify(values) }),
};
