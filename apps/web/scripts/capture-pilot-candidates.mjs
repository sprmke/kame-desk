// apps/web/scripts/capture-pilot-candidates.mjs
import { chromium } from "@playwright/test";
import fs from "fs";
import path from "path";

const BASE_URL = process.env.BASE_URL || "http://localhost:3100";
const OUTPUT_DIR = path.resolve(import.meta.dirname, "../../../.audit-screenshots/pilot");

const CANDIDATES = ["candidate-1", "candidate-2", "candidate-3"];
const THEMES = ["light", "dark"];
const VIEWPORTS = [
  { name: "desktop", width: 1440, height: 900 },
  { name: "mobile", width: 375, height: 812 },
];

async function main() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  console.log(`Saving pilot candidate screenshots to: ${OUTPUT_DIR}`);

  const browser = await chromium.launch({ headless: true });

  for (const candidate of CANDIDATES) {
    for (const theme of THEMES) {
      for (const vp of VIEWPORTS) {
        const filename = `${candidate}-${vp.name}-${theme}.png`;
        const filepath = path.join(OUTPUT_DIR, filename);

        const context = await browser.newContext({
          viewport: { width: vp.width, height: vp.height },
          colorScheme: theme,
        });

        const page = await context.newPage();

        // Inject theme and candidate preference in localStorage
        await page.addInitScript(({ themeKey, themeVal, candKey, candVal }) => {
          try {
            localStorage.setItem(themeKey, themeVal);
            localStorage.setItem(candKey, candVal);
            if (themeVal === "dark") {
              document.documentElement.classList.add("dark");
            } else {
              document.documentElement.classList.remove("dark");
            }
          } catch (e) {}
        }, {
          themeKey: "dd-theme",
          themeVal: theme,
          candKey: "dd-pilot-candidate",
          candVal: candidate,
        });

        // Login
        await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
        const emailInput = page.getByLabel("Email");
        const passwordInput = page.getByLabel("Password");
        if (await emailInput.isVisible({ timeout: 2000 }).catch(() => false)) {
          await emailInput.fill("demo@example.com");
          await passwordInput.fill("password123");
          await page.getByRole("button", { name: "Sign in" }).click();
          await page.waitForURL(/\/dashboard/, { timeout: 10000 }).catch(() => {});
        }

        // Go to waiting room
        await page.goto(`${BASE_URL}/dashboard/waiting-room`, { waitUntil: "networkidle", timeout: 15000 });
        await page.evaluate(({ t, c }) => {
          document.documentElement.classList.toggle("dark", t === "dark");
          localStorage.setItem("dd-theme", t);
          localStorage.setItem("dd-pilot-candidate", c);
        }, { t: theme, c: candidate });
        await page.waitForTimeout(600);

        await page.screenshot({ path: filepath, fullPage: false });
        console.log(`  ✓ Saved ${filename}`);
        await context.close();
      }
    }
  }

  await browser.close();
  console.log("Candidate captures finished.");
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
