export const BACKEND_URL: string = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";

// A function (not a constant) so tests can replace it.
export function getGoogleClientId(): string {
  return __GOOGLE_CLIENT_ID__;
}
