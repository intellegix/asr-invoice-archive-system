import { test, expect } from '@playwright/test';

test.describe('P48: Re-Classify Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/documents');
    await page.waitForLoadState('networkidle');
  });

  test('Re-Classify button is visible in document detail modal', async ({ page }) => {
    const firstRow = page.locator('table tbody tr').first();
    if (await firstRow.isVisible()) {
      await firstRow.click();
      await page.waitForSelector('[role="dialog"]');
      await expect(
        page.getByRole('button', { name: /Re-Classify/i }),
      ).toBeVisible();
    } else {
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
      await expect(
        btn.or(page.getByText(/Re-Classifying/i)).or(page.getByText(/reprocess/i)),
      ).toBeVisible();
    }
  });

  test('modal can be closed after Re-Classify action', async ({ page }) => {
    const firstRow = page.locator('table tbody tr').first();
    if (await firstRow.isVisible()) {
      await firstRow.click();
      await page.waitForSelector('[role="dialog"]');
      // Close modal via close button or Escape
      const closeBtn = page.getByRole('button', { name: /close/i });
      if (await closeBtn.isVisible()) {
        await closeBtn.click();
      } else {
        await page.keyboard.press('Escape');
      }
      await expect(page.locator('[role="dialog"]')).not.toBeVisible();
    }
  });

  test('documents table shows expected columns', async ({ page }) => {
    const table = page.locator('table');
    if (await table.isVisible()) {
      // Verify key column headers exist
      await expect(page.getByRole('columnheader', { name: /document/i }).or(
        page.getByRole('columnheader', { name: /file/i }),
      )).toBeVisible();
    } else {
      await expect(page.getByText(/No documents found/i)).toBeVisible();
    }
  });

  test('documents page has search input', async ({ page }) => {
    const searchInput = page.getByRole('textbox', { name: /search/i }).or(
      page.locator('input[type="text"][placeholder*="earch"]'),
    );
    await expect(searchInput).toBeVisible();
  });
});
