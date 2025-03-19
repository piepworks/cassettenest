// @ts-check
import { expect, test } from '@playwright/test';

// Don't use default, logged-in state
test.use({ storageState: { cookies: [], origins: [] } });

test('log in and registration pages', async ({ page }) => {
  await page.goto('./');

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle('Log in / Cassette Nest');
  await page.getByRole('link', { name: 'create an account' }).click();
  await expect(page).toHaveURL(/.*register/);
});
