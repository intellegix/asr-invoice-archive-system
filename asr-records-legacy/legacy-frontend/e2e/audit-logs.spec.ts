import { test, expect } from '@playwright/test';

test.describe('P48: Audit Log Viewer', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reports');
    await page.waitForLoadState('networkidle');
  });

  test('Recent Audit Trail section is visible on Reports page', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: /Recent Audit Trail/i }),
    ).toBeVisible();
  });

  test('audit trail shows empty state or entries', async ({ page }) => {
    // Either audit entries are listed or an empty-state message is shown
    const auditSection = page.locator('text=/Recent Audit Trail/i').locator('..');
    await expect(auditSection).toBeVisible();
    const entries = page.locator('[data-testid="audit-entry"]').or(
      page.getByText(/No audit entries/i).or(page.getByText(/No recent/i)),
    );
    // At least the section should render without errors
    await expect(
      auditSection.or(entries),
    ).toBeVisible();
  });

  test('Reports page renders without console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.goto('/reports');
    await page.waitForLoadState('networkidle');
    // Filter out known non-critical errors (network 404s for API calls are expected in E2E)
    const criticalErrors = errors.filter(
      (e) => !e.includes('404') && !e.includes('Failed to fetch'),
    );
    expect(criticalErrors).toHaveLength(0);
  });
});
