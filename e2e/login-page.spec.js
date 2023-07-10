// @ts-check
import { test, expect } from '@playwright/test';

// Don't use default, logged-in state
test.use({ storageState: { cookies: [], origins: [] } });

test('log in and registration pages', async ({ page }) => {
  await page.goto('./');

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle('Log in / Cassette Nest');
  await page
    .getByRole('link', { name: 'start your 14-day free trial' })
    .click();
  await expect(page).toHaveURL(/.*register/);
});
