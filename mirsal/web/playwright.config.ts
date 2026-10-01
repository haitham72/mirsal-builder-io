import { defineConfig } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
// The project venv (the Anaconda base env has a broken numpy). Override with E2E_PYTHON.
const py = process.env.E2E_PYTHON ?? path.join(here, "..", ".venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");

// Needs `npm run build` first: the console serves mirsal/mirsal/console/dist.
export default defineConfig({
  testDir: "e2e",
  timeout: 180_000,
  workers: 1,
  reporter: [["list"]],
  use: { baseURL: "http://127.0.0.1:8772", viewport: { width: 1440, height: 900 }, trace: "retain-on-failure" },
  webServer: {
    command: `"${py}" e2e/demo_server.py`,
    url: "http://127.0.0.1:8772/api/inbox",
    cwd: here,
    reuseExistingServer: false,
    timeout: 60_000,
    gracefulShutdown: { signal: "SIGTERM", timeout: 2000 },
  },
});
