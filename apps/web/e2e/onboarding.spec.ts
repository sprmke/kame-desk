import { test, expect } from "@playwright/test";
import { registerOwner } from "./helpers/onboarding";

test.describe("onboarding", () => {
  test("register redirects to onboarding wizard", async ({ page }) => {
    await registerOwner(page, { name: "Dr Test", clinic: "E2E Clinic" });
    await expect(
      page.getByRole("heading", { name: "Clinic profile" }),
    ).toBeVisible();
  });
});
