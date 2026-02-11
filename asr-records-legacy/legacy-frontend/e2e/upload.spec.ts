import { test, expect } from '@playwright/test';

test.describe('Phase 2C: Upload Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/upload');
    await page.waitForLoadState('networkidle');
  });

  test('page title is visible', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: 'Upload Documents' })
    ).toBeVisible();
  });

  test('page description is visible', async ({ page }) => {
    await expect(
      page.getByText('Upload documents for automated processing')
    ).toBeVisible();
  });

  test('dropzone area is visible', async ({ page }) => {
    await expect(
      page.getByText('Drop files here to upload')
    ).toBeVisible();
  });

  test('click to browse text is visible', async ({ page }) => {
    await expect(
      page.getByText('Or click to browse and select files')
    ).toBeVisible();
  });

  test('supported file types are shown', async ({ page }) => {
    await expect(page.getByText('PDF, PNG, JPG supported')).toBeVisible();
  });

  test('size limit is shown', async ({ page }) => {
    await expect(page.getByText('Up to 10MB per file')).toBeVisible();
  });

  test('batch upload info is shown', async ({ page }) => {
    await expect(page.getByText('Batch upload available')).toBeVisible();
  });

  test('GL Account Classifications feature card', async ({ page }) => {
    await expect(
      page.getByText('40+ GL Account Classifications')
    ).toBeVisible();
  });

  test('5-Method Payment Detection feature card', async ({ page }) => {
    await expect(
      page.getByText('5-Method Payment Detection')
    ).toBeVisible();
  });

  test('Smart Billing Routes feature card', async ({ page }) => {
    await expect(page.getByText('Smart Billing Routes')).toBeVisible();
  });

  test('System Status panel is visible', async ({ page }) => {
    await expect(page.getByText('System Status')).toBeVisible();
    await expect(page.getByText('Processing System')).toBeVisible();
    await expect(page.getByText('Online', { exact: true })).toBeVisible();
  });

  test('no upload progress section when empty', async ({ page }) => {
    await expect(page.getByText('Upload Progress')).not.toBeVisible();
  });

  test('screenshot captures full upload page', async ({ page }) => {
    await page.screenshot({
      path: 'e2e/screenshots/upload-desktop.png',
      fullPage: true,
    });
  });
});
