// scripts/dev/capture-baseline.mjs
import { chromium } from "@playwright/test";
import fs from "fs";
import path from "path";

const BASE_URL = process.env.BASE_URL || "http://localhost:3100";
const OUTPUT_DIR = path.resolve(import.meta.dirname, "../../../.audit-screenshots/baseline");

const VIEWPORTS = [
  { name: "desktop", width: 1440, height: 900 },
  { name: "tablet", width: 820, height: 1180 },
  { name: "mobile", width: 375, height: 812 },
];

const THEMES = ["light", "dark"];

const ROUTES = [
  { path: "/dashboard/waiting-room", name: "waiting-room" },
  { path: "/dashboard", name: "today" },
  { path: "/dashboard/appointments", name: "schedule" },
  { path: "/dashboard/patients", name: "patients" },
  { path: "/login", name: "login", unauthenticated: true },
];

async function main() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  console.log(`Saving baseline screenshots to: ${OUTPUT_DIR}`);

  const browser = await chromium.launch({ headless: true });

  for (const vp of VIEWPORTS) {
    for (const theme of THEMES) {
      console.log(`\n--- Viewport: ${vp.name} (${vp.width}x${vp.height}) | Theme: ${theme} ---`);
      const context = await browser.newContext({
        viewport: { width: vp.width, height: vp.height },
        colorScheme: theme,
      });

      const page = await context.newPage();

      // Set theme in localStorage before navigation
      await page.addInitScript(({ themeKey, themeVal }) => {
        try {
          localStorage.setItem(themeKey, themeVal);
          if (themeVal === "dark") {
            document.documentElement.classList.add("dark");
          } else {
            document.documentElement.classList.remove("dark");
          }
        } catch (e) {}
      }, { themeKey: "dd-theme", themeVal: theme });

      // First log in if needed
      console.log("Logging in via /login...");
      await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
      
      const emailInput = page.getByLabel("Email");
      const passwordInput = page.getByLabel("Password");
      if (await emailInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        await emailInput.fill("demo@example.com");
        await passwordInput.fill("password123");
        await page.getByRole("button", { name: "Sign in" }).click();
        await page.waitForURL(/\/dashboard/, { timeout: 10000 }).catch(() => {});
        await page.waitForLoadState("networkidle").catch(() => {});
      }

      for (const route of ROUTES) {
        const filename = `${route.name}-${vp.name}-${theme}.png`;
        const filepath = path.join(OUTPUT_DIR, filename);

        try {
          console.log(`Capturing ${route.path} -> ${filename}...`);
          await page.goto(`${BASE_URL}${route.path}`, { waitUntil: "networkidle", timeout: 15000 });
          // Ensure theme applied correctly
          await page.evaluate((t) => {
            document.documentElement.classList.toggle("dark", t === "dark");
            localStorage.setItem("dd-theme", t);
          }, theme);
          await page.waitForTimeout(600); // let animations settle

          await page.screenshot({ path: filepath, fullPage: false });
          console.log(`  ✓ Saved ${filename}`);
        } catch (err) {
          console.error(`  ✗ Failed ${filename}:`, err.message);
        }
      }

      await context.close();
    }
  }

  await browser.close();
  console.log("\nBaseline capture complete.");
}

main().catch(err => {
  console.error("Fatal error:", err);
  process.exit(1);
});
