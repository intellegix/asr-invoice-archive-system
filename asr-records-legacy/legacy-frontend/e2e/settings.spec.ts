import { test, expect } from '@playwright/test';

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');
  });

  test('settings page loads with heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
  });

  test('system information section is displayed', async ({ page }) => {
    await expect(page.getByText('System Information')).toBeVisible();
  });

  test('server version is displayed', async ({ page }) => {
    await expect(page.getByText('2.0.0')).toBeVisible();
  });

  test('theme toggle is present', async ({ page }) => {
    // The theme toggle is in the Header, which is visible on the settings page
    const themeButton = page.getByRole('button', { name: /toggle.*theme|dark.*mode|light.*mode/i });
    await expect(themeButton).toBeVisible();
  });

  test('API status indicator is present', async ({ page }) => {
    // Settings page shows system status
    const statusText = page.getByText(/online|offline|operational|degraded/i).first();
    await expect(statusText).toBeVisible();
  });

  test('no console errors on settings page', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
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
