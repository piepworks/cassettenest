// @ts-check
import { expect, test } from '@playwright/test';

test('patterns page / light mode', async ({ page }) => {
  await page.goto('./patterns');
  await page.emulateMedia({ colorScheme: 'light' });
  await expect(page).toHaveTitle('Pattern Library / Cassette Nest');
  await expect(page).toHaveScreenshot('patterns-light.png', {
    fullPage: true,
    mask: [
      page.locator('input[type=date]'),
      page.locator('.playwright-hidden'),
    ],
  });
});

test('patterns page / dark mode', async ({ page }) => {
  await page.goto('./patterns');
  await page.emulateMedia({ colorScheme: 'dark' });
  await expect(page).toHaveScreenshot('patterns-dark.png', {
    fullPage: true,
    mask: [
      page.locator('input[type=date]'),
      page.locator('.playwright-hidden'),
    ],
  });
});
