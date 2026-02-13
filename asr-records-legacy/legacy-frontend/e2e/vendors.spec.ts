import { test, expect } from '@playwright/test';

test.describe('Vendors Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/vendors');
    await page.waitForLoadState('networkidle');
  });

  test('vendors page loads with heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Vendors' })).toBeVisible();
  });

  test('page description is visible', async ({ page }) => {
    await expect(
      page.getByText(/Manage vendors and view their document processing statistics/)
    ).toBeVisible();
  });

  test('search input is present', async ({ page }) => {
    await expect(page.getByPlaceholder('Search vendors...')).toBeVisible();
  });

  test('Add Vendor button is present', async ({ page }) => {
    await expect(page.getByRole('button', { name: /add vendor/i })).toBeVisible();
  });

  test('summary stats section is rendered', async ({ page }) => {
    await expect(page.getByText('Total Vendors')).toBeVisible();
    await expect(page.getByText('Total Documents')).toBeVisible();
    await expect(page.getByText('Total Processed')).toBeVisible();
  });

  test('no console errors on vendors page', async ({ page }) => {
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
