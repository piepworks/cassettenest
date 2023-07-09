// @ts-check
const { test, expect } = require('@playwright/test');

test('has title, go to create account', async ({ page }) => {
  await page.goto('./');

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/Log in \/ Cassette Nest/);
  await page.getByRole('link', { name: 'start your 14-day free trial' }).click();
  await expect(page).toHaveURL(/.*register/);
});
