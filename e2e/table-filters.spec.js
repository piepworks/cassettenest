// @ts-check
import { expect, test } from '@playwright/test';

test('stocks filter reset', async ({ page }) => {
  await page.goto('./stocks');
  await expect(page).toHaveTitle('Film Stocks / Cassette Nest');

  await page
    .getByRole('combobox', { name: 'Manufacturer:' })
    .selectOption('kodak');
  await page.getByRole('link', { name: 'Reset filters' }).click();
  await expect(
    page.getByRole('combobox', { name: 'Manufacturer:' }),
  ).toHaveValue('all');
});
