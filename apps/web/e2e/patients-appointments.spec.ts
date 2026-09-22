import { test, expect, type Page } from "@playwright/test";
import { completeOnboarding, registerOwner } from "./helpers/onboarding";

function nextOpenDay(): Date {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  while (date.getDay() === 0) {
    date.setDate(date.getDate() + 1);
  }
  return date;
}

async function pickDate(page: Page, date: Date) {
  await page.getByLabel("Date").click();
  const calendar = page.locator(".dd-datepicker");
  await expect(calendar).toBeVisible();
  const today = new Date();
  if (
    date.getMonth() !== today.getMonth() ||
    date.getFullYear() !== today.getFullYear()
  ) {
    await page.getByRole("button", { name: "Go to the Next Month" }).click();
  }
  const day = String(date.getDate());
  await calendar
    .locator(".rdp-day:not(.rdp-outside) .rdp-day_button")
    .filter({ hasText: new RegExp(`^${day}$`) })
    .click();
  await expect(page.getByLabel("Date")).not.toContainText("Pick a date");
}

test.describe("patients and appointments", () => {
  test("create patient and book appointment", async ({ page }) => {
    await registerOwner(page);
    await completeOnboarding(page);

    await page
      .getByRole("navigation")
      .getByRole("link", { name: "Patients" })
      .click();
    await expect(page).toHaveURL(/\/dashboard\/patients/);
    await page.getByRole("link", { name: "New patient" }).first().click();
    await page.getByLabel("Full name").fill("E2E Patient");
    await page.getByLabel("Contact").fill("09171234567");
    await page.getByLabel(/consents to clinic data processing/i).check();
    await page.getByRole("button", { name: "Save" }).click();
    await expect(
      page.getByRole("heading", { name: "E2E Patient" }),
    ).toBeVisible();

    await page.getByRole("link", { name: "Book" }).click();
    await pickDate(page, nextOpenDay());
    await page.getByRole("button", { name: "Book" }).click();
    await expect(page).toHaveURL(/\/dashboard\/appointments\/?$/);
    await expect(page.getByText("E2E Patient").first()).toBeVisible();
  });
});
