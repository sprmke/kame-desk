import { test, expect } from "@playwright/test";
import {
  completeOnboarding,
  openSettings,
  registerOwner,
} from "./helpers/onboarding";

test.describe("clinic assistant", () => {
  test("settings toggle and launcher render", async ({ page }) => {
    await registerOwner(page);
    await completeOnboarding(page);

    await openSettings(page);
    await page.getByRole("link", { name: "Assistant" }).click();
    await expect(
      page.getByRole("heading", { name: "Assistant" }),
    ).toBeVisible();
    await expect(page.getByText("Enable clinic assistant")).toBeVisible();

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
