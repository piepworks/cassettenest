import { test, expect } from '@playwright/test';

test('signup page is awesome', async ({ page }) => {
  await page.goto('localhost:8000');
  await expect(page).toHaveTitle("Log in / Cassette Nest");
  const signupLink = page.locator('text=start your 14-day free trial');
  await expect(signupLink).toHaveAttribute('href', '/register/');
  await signupLink.click();
  // Expects the URL to contain `register`.
  await expect(page).toHaveURL(/.*register/);
});
