import path from "node:path";
import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";

// The Google client ID is shared with the backend (GOOGLE_OAUTH_CLIENT_ID). Inside Docker it
// arrives as a process env var; running natively it is read from the repo-root .env. Only this
// one value is exposed to the browser bundle (it is public, not a secret).
export default defineConfig(({ mode }) => {
  const rootEnv = loadEnv(mode, path.resolve(import.meta.dirname, ".."), "");
  const googleClientId = process.env.GOOGLE_OAUTH_CLIENT_ID ?? rootEnv.GOOGLE_OAUTH_CLIENT_ID ?? "";
  return {
    plugins: [react()],
    define: { __GOOGLE_CLIENT_ID__: JSON.stringify(googleClientId) },
    server: { host: "0.0.0.0", port: 3000 },
    test: {
      environment: "jsdom",
      setupFiles: ["./src/test/setup.ts"],
      css: false,
    },
  };
});
