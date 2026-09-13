import { test, expect, type Page } from "@playwright/test";
import path from "node:path";
import fs from "node:fs";

const EMAIL = process.env.DESIGN_SCREENSHOT_EMAIL ?? "demo@example.com";
const PASSWORD = process.env.DESIGN_SCREENSHOT_PASSWORD ?? "password123";
const OUT_DIR = path.resolve(process.cwd(), "../../.audit-screenshots/harness");

const VIEWPORTS = [
  { name: "mobile", width: 375, height: 812 },
  { name: "tablet", width: 820, height: 1180 },
  { name: "desktop", width: 1440, height: 900 },
] as const;

const THEMES = ["light", "dark"] as const;

const PUBLIC_ROUTES = ["/login"];

const AUTH_ROUTES = [
  "/dashboard",
  "/dashboard/waiting-room",
  "/dashboard/appointments",
  "/dashboard/appointments/calendar",
  "/dashboard/patients",
  "/dashboard/billing",
  "/dashboard/insights/reports",
  "/dashboard/insights/audit-log",
  "/dashboard/settings/account",
  "/dashboard/settings/clinic/details",
  "/dashboard/notifications",
];

function slug(route: string) {
  return route.replace(/^\//, "").replaceAll("/", "_") || "root";
}

async function setTheme(page: Page, theme: "light" | "dark") {
  await page.evaluate(
    ([key, value]) => {
      localStorage.setItem(key, value);
      document.documentElement.classList.toggle("dark", value === "dark");
    },
    ["dd-theme", theme],
  );
}

async function captureRoute(
  page: Page,
  route: string,
  vp: (typeof VIEWPORTS)[number],
  theme: (typeof THEMES)[number],
) {
  await page.setViewportSize({ width: vp.width, height: vp.height });
  await page.goto(route);
  await page.waitForTimeout(400);
  const file = path.join(OUT_DIR, `${slug(route)}-${vp.name}-${theme}.png`);
  await page.screenshot({ path: file, fullPage: true });
}

async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(EMAIL);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 20_000 });
}

test.describe("design screenshot harness", () => {
  test("capture routes at three widths and two themes", async ({ page }) => {
    test.skip(
      process.env.CAPTURE_DESIGN_SCREENSHOTS !== "1",
      "Set CAPTURE_DESIGN_SCREENSHOTS=1. Needs a seeded local app (pnpm run dev).",
    );

    fs.mkdirSync(OUT_DIR, { recursive: true });

    for (const theme of THEMES) {
      await page.goto("/login");
      await setTheme(page, theme);
      for (const vp of VIEWPORTS) {
        for (const route of PUBLIC_ROUTES) {
          await captureRoute(page, route, vp, theme);
        }
      }
    }

    await login(page);

    for (const theme of THEMES) {
      await setTheme(page, theme);
      for (const vp of VIEWPORTS) {
        for (const route of AUTH_ROUTES) {
          await captureRoute(page, route, vp, theme);
        }
      }
    }
  });
});
