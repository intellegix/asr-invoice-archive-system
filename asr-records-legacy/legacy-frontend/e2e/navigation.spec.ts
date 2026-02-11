import { test, expect } from '@playwright/test';

test.describe('Phase 2E: Navigation Flows', () => {
  test('sidebar is visible on dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('ASR Records', { exact: true })).toBeVisible();
    await expect(page.getByText('Legacy Edition')).toBeVisible();
  });

  test('sidebar shows quick stats', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    // Quick stats in the sidebar show document count and accuracy
    await expect(page.locator('nav').getByText('1,234')).toBeVisible();
    await expect(page.locator('nav').getByText('94%')).toBeVisible();
  });

  test('sidebar has primary nav links', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('link', { name: /Dashboard/ })).toBeVisible();
    await expect(page.getByRole('link', { name: /Upload/ })).toBeVisible();
    // "Documents" appears both as nav link and quick stat - use link role
    const docLinks = page.getByRole('link', { name: /Documents/ });
    expect(await docLinks.count()).toBeGreaterThanOrEqual(1);
  });

  test('sidebar has secondary nav links', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('Tools')).toBeVisible();
    await expect(page.getByRole('link', { name: /Reports/ })).toBeVisible();
    await expect(page.getByRole('link', { name: /Settings/ })).toBeVisible();
  });

  test('sidebar shows system online status', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('System Online')).toBeVisible();
  });

  test('Dashboard nav link highlights when active', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    const dashLink = page.getByRole('link', { name: /Dashboard/ }).first();
    await expect(dashLink).toHaveClass(/bg-primary-50/);
  });

  test('clicking Upload nav link navigates to /upload', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.getByRole('link', { name: /Upload/ }).first().click();
    await page.waitForURL('**/upload');
    expect(page.url()).toContain('/upload');
    await expect(
      page.getByRole('heading', { name: 'Upload Documents' })
    ).toBeVisible();
  });

  test('clicking Documents nav link navigates to /documents', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    // Use the nav link specifically (not the quick stats "Documents" text)
    await page.getByRole('link', { name: /Documents/ }).first().click();
    await page.waitForURL('**/documents');
    expect(page.url()).toContain('/documents');
  });

  test('unknown route redirects to dashboard', async ({ page }) => {
    await page.goto('/nonexistent-page');
    await page.waitForURL('**/dashboard');
    expect(page.url()).toContain('/dashboard');
  });

  test('header renders consistently across pages', async ({ page }) => {
    // Check header on dashboard
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('ASR Records Legacy')).toBeVisible();

    // Check header on upload
    await page.goto('/upload');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('ASR Records Legacy')).toBeVisible();

    // Check header on documents
    await page.goto('/documents');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('ASR Records Legacy')).toBeVisible();
  });
});
