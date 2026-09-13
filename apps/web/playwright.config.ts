import { defineConfig, devices } from "@playwright/test";

const apiPort = 8000;
const webPort = Number(process.env.PLAYWRIGHT_WEB_PORT ?? 4173);
const apiBase = `http://127.0.0.1:${apiPort}`;
const webBase = `http://127.0.0.1:${webPort}`;
const inGithubCi = Boolean(process.env.GITHUB_ACTIONS);

export default defineConfig({
  testDir: "./e2e",
  testIgnore: "design-screenshot-harness.spec.ts",
  fullyParallel: false,
  forbidOnly: inGithubCi,
  retries: inGithubCi ? 2 : 0,
  workers: 1,
  timeout: 60_000,
  use: {
    baseURL: webBase,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `bash -lc 'cd ../api && DOCTORDESK_TESTING=1 DATABASE_URL=postgresql+asyncpg://doctordesk:doctordesk_local_only@127.0.0.1:5432/doctordesk REDIS_URL=redis://127.0.0.1:6379/0 SECRET_KEY=playwright-e2e-secret CORS_ORIGINS=${webBase} ENVIRONMENT=local uv run alembic upgrade head && DOCTORDESK_TESTING=1 DATABASE_URL=postgresql+asyncpg://doctordesk:doctordesk_local_only@127.0.0.1:5432/doctordesk REDIS_URL=redis://127.0.0.1:6379/0 SECRET_KEY=playwright-e2e-secret CORS_ORIGINS=${webBase} ENVIRONMENT=local uv run uvicorn app.main:app --host 127.0.0.1 --port ${apiPort}'`,
      url: `${apiBase}/api/v1/health`,
      reuseExistingServer: !inGithubCi,
      timeout: 120_000,
    },
    {
      command: `VITE_API_URL=${apiBase}/api/v1 pnpm run build && VITE_API_URL=${apiBase}/api/v1 pnpm exec vite preview --host 127.0.0.1 --port ${webPort}`,
      url: webBase,
      reuseExistingServer: !inGithubCi,
      timeout: 180_000,
    },
  ],
});
