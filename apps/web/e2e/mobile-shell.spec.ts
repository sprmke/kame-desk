import { test, expect } from "@playwright/test";
import { completeOnboarding, registerOwner } from "./helpers/onboarding";

test.describe("native mobile shell", () => {
  test("bottom tabs on phone, sidebar on desktop", async ({ page }) => {
    await registerOwner(page, { name: "Dr Mobile", clinic: "Mobile Clinic" });
    await completeOnboarding(page);

    await page.setViewportSize({ width: 390, height: 844 });
    const tabs = page.getByTestId("bottom-tab-bar");
    await expect(tabs).toBeVisible();
    await expect(tabs.getByRole("link", { name: "Waiting" })).toBeVisible();

    await tabs.getByRole("link", { name: "Waiting" }).click();
    await expect(page).toHaveURL(/\/dashboard\/waiting-room/);
    await page.getByRole("button", { name: "Walk-in" }).click();
    await expect(page.getByTestId("walk-in-modal")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Walk-in" })).toBeVisible();
    await page.keyboard.press("Escape");

    await page.setViewportSize({ width: 1280, height: 800 });
    await expect(tabs).toBeHidden();
    await expect(
      page.getByRole("navigation").getByRole("link", { name: "Patients" }),
    ).toBeVisible();
  });
});
