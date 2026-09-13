import { expect, type Page } from "@playwright/test";

export async function completeOnboarding(page: Page) {
  await expect(
    page.getByRole("heading", { name: "Set up your clinic" }),
  ).toBeVisible();

  await page.getByLabel("Address").fill("123 Test St");
  await page.getByLabel("Phone").fill("+639171234567");
  await page.getByLabel("Email", { exact: true }).fill("clinic@example.com");
  await page.getByLabel("License").fill("LIC-001");
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByLabel("Specialty")).toBeVisible();
  await page.getByLabel("Specialty").fill("General Practice");
  await page.getByLabel("PRC license").fill("PRC-123");
  await page.getByLabel("Consultation fee").fill("500");
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByText("Monday")).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();

  const serviceName = page.getByLabel("Service name");
  const skipInvite = page.getByRole("button", { name: "Skip for now" });
  await expect(serviceName.or(skipInvite)).toBeVisible();

  if (await serviceName.isVisible()) {
    await page.getByRole("button", { name: "Continue" }).click();
    await expect(skipInvite).toBeVisible();
  }

  await skipInvite.click();

  await expect(page).toHaveURL(/\/dashboard/);
}
