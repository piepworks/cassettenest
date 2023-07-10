// @ts-check
import { test, expect } from '@playwright/test';

// Don't use default, logged-in state
test.use({ storageState: { cookies: [], origins: [] } });

test('has title, go to create account', async ({ page }) => {
  await page.goto('./');

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/Log in \/ Cassette Nest/);
  await page
    .getByRole('link', { name: 'start your 14-day free trial' })
    .click();
  await expect(page).toHaveURL(/.*register/);
  await page.screenshot({ path: 'test-results/login.png', fullPage: true });
});
