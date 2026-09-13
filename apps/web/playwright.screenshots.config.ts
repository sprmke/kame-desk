import { defineConfig, devices } from "@playwright/test";

const webBase =
  process.env.DESIGN_SCREENSHOT_BASE_URL ?? "http://127.0.0.1:3100";

export default defineConfig({
  testDir: "./e2e",
  testMatch: "design-screenshot-harness.spec.ts",
  fullyParallel: false,
  retries: 0,
  workers: 1,
  timeout: 120_000,
  use: {
    baseURL: webBase,
    trace: "off",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
