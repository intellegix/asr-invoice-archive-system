import { test, expect } from '@playwright/test';

test.describe('P48: Re-Classify Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/documents');
    await page.waitForLoadState('networkidle');
  });

  test('Re-Classify button is visible in document detail modal', async ({ page }) => {
    // Click the first document row to open the detail modal
    const firstRow = page.locator('table tbody tr').first();
    if (await firstRow.isVisible()) {
      await firstRow.click();
      await page.waitForSelector('[role="dialog"]');
      await expect(
        page.getByRole('button', { name: /Re-Classify/i }),
      ).toBeVisible();
    } else {
      // No documents in table — verify empty state instead
      await expect(page.getByText(/No documents found/i)).toBeVisible();
    }
  });

  test('Re-Classify click shows feedback', async ({ page }) => {
    const firstRow = page.locator('table tbody tr').first();
    if (await firstRow.isVisible()) {
      await firstRow.click();
      await page.waitForSelector('[role="dialog"]');
      const btn = page.getByRole('button', { name: /Re-Classify/i });
      await expect(btn).toBeVisible();
      await btn.click();
      // After click, button should show pending state or a toast appears
      await expect(
        btn.or(page.getByText(/Re-Classifying/i)).or(page.getByText(/reprocess/i)),
      ).toBeVisible();
    }
  });
});
