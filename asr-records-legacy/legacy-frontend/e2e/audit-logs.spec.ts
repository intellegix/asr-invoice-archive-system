import { test, expect } from '@playwright/test';

test.describe('P48: Audit Log Viewer', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reports');
    await page.waitForLoadState('networkidle');
  });

  test('Recent Audit Trail section is visible on Reports page', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: /Recent Audit Trail/i }),
    ).toBeVisible();
  });
});
