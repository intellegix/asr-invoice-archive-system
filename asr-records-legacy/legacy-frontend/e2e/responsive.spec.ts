import { test, expect } from '@playwright/test';

test.describe('Phase 2F: Responsive Layout', () => {
  const viewports = [
    { name: 'desktop-1920', width: 1920, height: 1080 },
    { name: 'laptop-1366', width: 1366, height: 768 },
    { name: 'tablet-768', width: 768, height: 1024 },
    { name: 'mobile-375', width: 375, height: 667 },
  ];

  for (const viewport of viewports) {
    test(`dashboard renders at ${viewport.name} (${viewport.width}x${viewport.height})`, async ({
      page,
    }) => {
      await page.setViewportSize({
        width: viewport.width,
        height: viewport.height,
      });
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      await expect(
        page.getByRole('heading', { name: 'Dashboard' })
      ).toBeVisible();
      await page.screenshot({
        path: `e2e/screenshots/dashboard-${viewport.name}.png`,
        fullPage: true,
      });
    });
  }

  test('metric cards reflow on narrow viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    // All 4 metric cards should still be visible (stacked vertically)
    await expect(page.getByText('Total Documents')).toBeVisible();
    await expect(page.getByText('Payment Accuracy')).toBeVisible();
    await expect(page.getByText('Total Amount Processed')).toBeVisible();
    await expect(page.getByText('GL Accounts Used')).toBeVisible();
  });

  test('upload page renders at tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/upload');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('Drop files here to upload')).toBeVisible();
    await page.screenshot({
      path: 'e2e/screenshots/upload-tablet.png',
      fullPage: true,
    });
  });

  test('documents page renders at mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/documents');
    await page.waitForLoadState('networkidle');
    await expect(
      page.getByRole('heading', { name: 'Documents', exact: true }).first()
    ).toBeVisible();
    await page.screenshot({
      path: 'e2e/screenshots/documents-mobile.png',
      fullPage: true,
    });
  });
});
