import { test, expect } from "@playwright/test";

test.describe("onboarding", () => {
  test("register redirects to onboarding wizard", async ({ page }) => {
    const email = `owner-${Date.now()}@example.com`;
    await page.goto("/register");
    await page.getByLabel("Your name").fill("Dr Test");
    await page.getByLabel("Clinic name").fill("E2E Clinic");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill("password123");
    await page.getByRole("button", { name: "Create account" }).click();
    await expect(page).toHaveURL(/\/onboarding/);
    await expect(
      page.getByRole("heading", { name: "Set up your clinic" }),
    ).toBeVisible();
  });
});
