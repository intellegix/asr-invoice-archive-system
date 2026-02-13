import { test, expect } from '@playwright/test';

test.describe('Error Handling', () => {
  test('invalid route redirects to dashboard', async ({ page }) => {
    await page.goto('/nonexistent-page-12345');
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    expect(page.url()).toContain('/dashboard');
  });

  test('upload page shows file type restriction info', async ({ page }) => {
    await page.goto('/upload');
    await page.waitForLoadState('networkidle');
    // The upload page should display supported file types
    await expect(
      page.getByText(/pdf|jpg|jpeg|png|supported/i).first()
    ).toBeVisible();
  });

  test('upload page shows file size limit info', async ({ page }) => {
    await page.goto('/upload');
    await page.waitForLoadState('networkidle');
    // The upload page should mention size limits
    await expect(page.getByText(/10\s?MB|25\s?MB|max.*size|size.*limit/i).first()).toBeVisible();
  });

  test('API error response is structured JSON', async ({ request }) => {
    // Hit a nonexistent API endpoint to verify structured error response
    const response = await request.get('http://localhost:8000/api/v1/nonexistent');
    expect(response.status()).toBe(404);
    const body = await response.json();
    expect(body.success).toBe(false);
    expect(body.errors).toBeDefined();
  });
});
