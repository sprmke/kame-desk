import { expect, type Page } from "@playwright/test";

export async function registerOwner(
  page: Page,
  opts?: { name?: string; clinic?: string; email?: string },
) {
  const email = opts?.email ?? `owner-${Date.now()}@example.com`;
  await page.goto("/register");
  await page.getByLabel("Your name").fill(opts?.name ?? "Dr E2E");
  await page.getByLabel("Clinic name").fill(opts?.clinic ?? "E2E Clinic");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill("password123");
  await page.getByRole("button", { name: "Create clinic" }).click();
  await expect(page).toHaveURL(/\/onboarding/);
  return email;
}

export async function completeOnboarding(page: Page) {
  await expect(
    page.getByRole("heading", { name: "Clinic profile" }),
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

export async function openSettings(page: Page) {
  await page.getByRole("button", { name: "Account menu" }).click();
  await page.getByRole("menuitem", { name: "Settings" }).click();
}
