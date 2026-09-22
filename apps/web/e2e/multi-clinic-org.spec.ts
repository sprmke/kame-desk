import { test, expect } from "@playwright/test";
import { completeOnboarding, registerOwner } from "./helpers/onboarding";

test("organization settings redirect to billing plan", async ({ page }) => {
  const suffix = Date.now();
  await registerOwner(page, {
    name: "Org Owner",
    clinic: `Org Clinic ${suffix}`,
    email: `org-owner-${suffix}@example.com`,
  });
  await completeOnboarding(page);

  await page.goto("/dashboard/settings/organization");
  await expect(page).toHaveURL(/\/dashboard\/settings\/plan/);
  await expect(
    page.getByRole("heading", { name: "Billing plan" }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: "Add clinic" })).toHaveCount(0);
});
