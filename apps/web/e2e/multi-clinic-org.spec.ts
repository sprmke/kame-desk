import { test, expect } from "@playwright/test";

test("org owner can open organization settings", async ({ page }) => {
  const suffix = Date.now();
  await page.goto("/register");
  await page.getByLabel(/email/i).fill(`org-owner-${suffix}@example.com`);
  await page.getByLabel(/^password$/i).fill("password123");
  await page.getByLabel(/full name/i).fill("Org Owner");
  await page.getByLabel(/clinic name/i).fill(`Org Clinic ${suffix}`);
  await page.getByRole("button", { name: /sign up|register|create/i }).click();

  await page.waitForURL(/\/onboarding/, { timeout: 15000 });

  await page.goto("/dashboard/settings/organization");
  await expect(
    page.getByRole("heading", { name: "Organization" }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: "Add clinic" })).toBeVisible();
});
