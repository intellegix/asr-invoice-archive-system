import { test, expect } from '@playwright/test';

test.describe('Phase 2A: Startup Verification', () => {
  test('health endpoint returns 200', async ({ request }) => {
    const response = await request.get('http://localhost:8000/health');
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.system_type).toBe('production_server');
    expect(body.components.gl_accounts.status).toBe('healthy');
    expect(body.components.gl_accounts.count).toBe(79);
  });

  test('frontend loads at localhost:3000', async ({ page }) => {
    const response = await page.goto('/');
    expect(response?.status()).toBe(200);
  });

  test('Vite proxy works for /api routes', async ({ request }) => {
    const response = await request.get('http://localhost:3000/api/status');
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.success).toBe(true);
    expect(body.data.status).toBe('operational');
  });

  test('root redirects to /dashboard', async ({ page }) => {
    await page.goto('/');
    await page.waitForURL('**/dashboard');
    expect(page.url()).toContain('/dashboard');
  });

  test('no JavaScript console errors on load', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    await page.goto('/dashboard');
    await page.waitForTimeout(2000);
    // Filter out expected errors (API 404s for missing data, network errors)
    const unexpectedErrors = errors.filter(
      (e) =>
        !e.includes('Failed to fetch') &&
        !e.includes('Network Error') &&
        !e.includes('404') &&
        !e.includes('Failed to load resource')
    );
    expect(unexpectedErrors).toHaveLength(0);
  });
});
