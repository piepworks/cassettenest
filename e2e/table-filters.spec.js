// @ts-check
import { test, expect } from '@playwright/test';

test('stocks filter reset', async ({ page }) => {
  await page.goto('./stocks');

  await expect(page).toHaveTitle('Film Stocks / Cassette Nest');
});
