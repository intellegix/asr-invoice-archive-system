import { test, expect } from '@playwright/test';

test.describe('Phase 2D: Documents Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/documents');
    await page.waitForLoadState('networkidle');
  });

  test('page title is visible', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: 'Documents', exact: true }).first()
    ).toBeVisible();
  });

  test('page description is visible', async ({ page }) => {
    await expect(
      page.getByText('Browse and manage all processed documents')
    ).toBeVisible();
  });

  test('search input is visible', async ({ page }) => {
    await expect(
      page.getByPlaceholder('Search documents, vendors, or GL accounts...')
    ).toBeVisible();
  });

  test('Filters button is visible', async ({ page }) => {
    await expect(
      page.getByRole('button', { name: /Filters/i })
    ).toBeVisible();
  });

  test('Export button is visible', async ({ page }) => {
    await expect(
      page.getByRole('button', { name: /Export/i })
    ).toBeVisible();
  });

  test('All Documents quick filter is visible', async ({ page }) => {
    await expect(page.getByText(/All Documents/)).toBeVisible();
  });

  test('Manual Review quick filter is visible', async ({ page }) => {
    await expect(page.getByText(/Manual Review/)).toBeVisible();
  });

  test('Unpaid quick filter is visible', async ({ page }) => {
    await expect(page.getByText(/Unpaid/)).toBeVisible();
  });

  test('High Value quick filter is visible', async ({ page }) => {
    await expect(page.getByText(/High Value/)).toBeVisible();
  });

  test('documents table or empty state is rendered', async ({ page }) => {
    // Either the table headers are visible or the empty state is shown
    const tableVisible = await page.locator('th:has-text("Document")').isVisible();
    const emptyVisible = await page.getByText('No documents found').isVisible();
    expect(tableVisible || emptyVisible).toBe(true);
  });

  test('table headers include expected columns', async ({ page }) => {
    // Skip if no documents (empty state)
    const emptyVisible = await page.getByText('No documents found').isVisible();
    if (!emptyVisible) {
      await expect(page.locator('th:has-text("Document")')).toBeVisible();
      await expect(page.locator('th:has-text("Vendor")')).toBeVisible();
      await expect(page.locator('th:has-text("Amount")')).toBeVisible();
      await expect(page.locator('th:has-text("Payment Status")')).toBeVisible();
      await expect(page.locator('th:has-text("GL Account")')).toBeVisible();
      await expect(page.locator('th:has-text("Destination")')).toBeVisible();
      await expect(page.locator('th:has-text("Confidence")')).toBeVisible();
      await expect(page.locator('th:has-text("Processed")')).toBeVisible();
    }
  });

  test('summary stats section exists', async ({ page }) => {
    // The summary stats section with Total Documents / High Confidence / Total Amount / GL Accounts
    await expect(page.getByText('High Confidence Classifications')).toBeVisible();
    await expect(page.getByText('Total Amount Processed')).toBeVisible();
    await expect(page.getByText('GL Accounts in Use')).toBeVisible();
  });

  test('search input accepts text', async ({ page }) => {
    const searchInput = page.getByPlaceholder(
      'Search documents, vendors, or GL accounts...'
    );
    await searchInput.fill('invoice');
    await expect(searchInput).toHaveValue('invoice');
  });

  test('screenshot captures full documents page', async ({ page }) => {
    await page.screenshot({
      path: 'e2e/screenshots/documents-desktop.png',
      fullPage: true,
    });
  });
});
