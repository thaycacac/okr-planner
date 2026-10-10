import { defineConfig, devices } from "@playwright/test";

// Starts its own backend (real API, fresh SQLite, FakeProvider instead of an LLM) and a
// Next.js dev server proxying /api to it, on ports that do not clash with a normal dev setup.
const frontendPort = Number(process.env.E2E_FRONTEND_PORT ?? 3217);
const backendPort = Number(process.env.E2E_BACKEND_PORT ?? 8217);
const python = process.env.E2E_PYTHON ?? ".venv/bin/python";
const baseURL = `http://localhost:${frontendPort}`;

export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  timeout: 120_000,
  expect: { timeout: 20_000 },
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL,
    locale: "en-US",
    timezoneId: "Asia/Ho_Chi_Minh",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } }],
  webServer: [
    {
      command: `${python} -m tests.e2e_server --port ${backendPort} --frontend-origin ${baseURL}`,
      cwd: "../backend",
      url: `http://127.0.0.1:${backendPort}/health`,
      timeout: 60_000,
      reuseExistingServer: false,
    },
    {
      command: `npx next dev --port ${frontendPort}`,
      env: { BACKEND_INTERNAL_URL: `http://127.0.0.1:${backendPort}` },
      url: `${baseURL}/login`,
      timeout: 180_000,
      reuseExistingServer: false,
    },
  ],
});
