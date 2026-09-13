import { test, expect } from "@playwright/test";
import { completeOnboarding } from "./helpers/onboarding";

test.describe("clinic assistant", () => {
  test("settings toggle and launcher render", async ({ page }) => {
    const email = `owner-${Date.now()}@example.com`;
    await page.goto("/register");
    await page.getByLabel("Your name").fill("Dr E2E");
    await page.getByLabel("Clinic name").fill("E2E Clinic");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill("password123");
    await page.getByRole("button", { name: "Create account" }).click();
    await completeOnboarding(page);

    await page.getByRole("link", { name: "Assistant" }).click();
    await expect(
      page.getByRole("heading", { name: "Assistant" }),
    ).toBeVisible();
    await expect(page.getByLabel("Enable clinic assistant")).toBeVisible();

    await page
      .getByRole("navigation")
      .getByRole("link", { name: "Patients" })
      .click();
    await expect(page).toHaveURL(/\/dashboard\/patients/);
    await page.getByRole("button", { name: "Open clinic assistant" }).click();
    await expect(
      page.getByRole("dialog", { name: "Clinic assistant" }),
    ).toBeVisible();
  });
});
