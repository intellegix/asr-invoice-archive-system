import { test, expect } from '@playwright/test';

test.describe('Phase 2B: Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('page title is visible', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('welcome subtitle is visible', async ({ page }) => {
    await expect(
      page.getByText("Welcome back! Here's what's happening")
    ).toBeVisible();
  });

  test('Total Documents metric card is rendered', async ({ page }) => {
    await expect(page.getByText('Total Documents')).toBeVisible();
  });

  test('Payment Accuracy metric card is rendered', async ({ page }) => {
    await expect(page.getByText('Payment Accuracy')).toBeVisible();
  });

  test('Total Amount Processed metric card is rendered', async ({ page }) => {
    await expect(page.getByText('Total Amount Processed')).toBeVisible();
  });

  test('GL Accounts Used metric card is rendered', async ({ page }) => {
    await expect(page.getByText('GL Accounts Used')).toBeVisible();
  });

  test('Recent Documents section is rendered', async ({ page }) => {
    await expect(page.getByText('Recent Documents').first()).toBeVisible();
  });

  test('Payment Status Distribution section is rendered', async ({ page }) => {
    await expect(page.getByText('Payment Status Distribution')).toBeVisible();
  });

  test('Quick Actions section is rendered', async ({ page }) => {
    await expect(page.getByText('Quick Actions')).toBeVisible();
  });

  test('Upload Documents quick action button exists', async ({ page }) => {
    await expect(page.getByText('Upload Documents')).toBeVisible();
    await expect(page.getByText('Add new documents for processing')).toBeVisible();
  });

  test('View Reports quick action button exists', async ({ page }) => {
    await expect(page.getByText('View Reports')).toBeVisible();
  });

  test('Review Queue quick action button exists', async ({ page }) => {
    await expect(page.getByText('Review Queue')).toBeVisible();
  });

  test('screenshot captures full dashboard', async ({ page }) => {
    await page.screenshot({
      path: 'e2e/screenshots/dashboard-desktop.png',
      fullPage: true,
    });
  });
});
