// @ts-check
import { test, expect } from '@playwright/test';

test('patterns page / light mode', async ({ page }) => {
  await page.goto('./patterns');
  await expect(page).toHaveTitle(/Pattern Library \/ Cassette Nest/);
  await expect(page).toHaveScreenshot('patterns-light.png', { fullPage: true });
});

test.use({ colorScheme: 'dark' });

test('patterns page / dark mode', async ({ page }) => {
  await page.goto('./patterns');
  await expect(page).toHaveScreenshot('patterns-dark.png', { fullPage: true });
});
