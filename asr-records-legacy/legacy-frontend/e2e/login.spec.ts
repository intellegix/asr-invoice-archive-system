import { test, expect } from '@playwright/test';

test.describe('Login Page', () => {
  test('login page renders with form', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: /sign in|login|log in/i })).toBeVisible();
  });

  test('login form has API key input', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    const apiKeyInput = page.getByPlaceholder(/api key|enter.*key/i);
    await expect(apiKeyInput).toBeVisible();
  });

  test('login form has submit button', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    const submitButton = page.getByRole('button', { name: /sign in|log in|connect/i });
    await expect(submitButton).toBeVisible();
  });

  test('successful login redirects to dashboard', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Fill in API key and submit
    const apiKeyInput = page.getByPlaceholder(/api key|enter.*key/i);
    await apiKeyInput.fill('test-api-key-for-dev');

    const submitButton = page.getByRole('button', { name: /sign in|log in|connect/i });
    await submitButton.click();

    // Should redirect to dashboard after successful login
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    expect(page.url()).toContain('/dashboard');
  });

  test('no console errors on login page', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.goto('/login');
    await page.waitForTimeout(2000);
    const unexpected = errors.filter(
      (e) =>
        !e.includes('Failed to fetch') &&
        !e.includes('Network Error') &&
        !e.includes('404') &&
        !e.includes('Failed to load resource')
    );
    expect(unexpected).toHaveLength(0);
  });
});
