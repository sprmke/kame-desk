import { test, expect } from "@playwright/test";
import { completeOnboarding } from "./helpers/onboarding";

test.describe("patients and appointments", () => {
  test("create patient and book appointment", async ({ page }) => {
    const email = `owner-${Date.now()}@example.com`;
    await page.goto("/register");
    await page.getByLabel("Your name").fill("Dr E2E");
    await page.getByLabel("Clinic name").fill("E2E Clinic");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill("password123");
    await page.getByRole("button", { name: "Create account" }).click();
    await expect(page).toHaveURL(/\/onboarding/);

    await completeOnboarding(page);

    await page
      .getByRole("navigation")
      .getByRole("link", { name: "Patients" })
      .click();
    await expect(page).toHaveURL(/\/dashboard\/patients/);
    await page.getByRole("link", { name: "New patient" }).click();
    await page.getByLabel("Full name").fill("E2E Patient");
    await page.getByLabel("Contact").fill("09171234567");
    await page.getByLabel(/consents to clinic data processing/i).check();
    await page.getByRole("button", { name: "Save" }).click();
    await expect(
      page.getByRole("heading", { name: "E2E Patient" }),
    ).toBeVisible();

    await page.getByRole("link", { name: "Book" }).click();
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dateStr = tomorrow.toISOString().slice(0, 10);
    await page.locator('input[type="date"]').fill(dateStr);
    await page.locator("select").first().selectOption({ index: 1 });
    await page.locator("select").nth(1).selectOption({ index: 1 });
    await page.getByRole("button", { name: "Book" }).click();
    await expect(page).toHaveURL(/\/dashboard\/appointments/);
    await expect(page.getByText("E2E Patient")).toBeVisible();
  });
});
