const { test, expect } = require('@playwright/test');

test.describe('Insights Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/insights');
    await page.waitForLoadState('networkidle');
  });

  test('should display aggregate statistics cards', async ({ page }) => {
    // Check for core metric labels
    await expect(page.locator('text=Muestra')).toBeVisible();
    await expect(page.locator('text=Promedio')).toBeVisible();
    await expect(page.locator('text=Uso Medio')).toBeVisible();
    await expect(page.locator('text=Tendencia')).toBeVisible();
  });

  test('should load charts and data visualizations', async ({ page }) => {
    // Depreciation chart container
    const depreciationChart = page.locator('.recharts-responsive-container').first();
    await expect(depreciationChart).toBeVisible();
    
    // Check for brand toggles in depreciation chart
    await expect(page.locator('button:has-text("Toyota")')).toBeVisible();
    await expect(page.locator('button:has-text("Hyundai")')).toBeVisible();
  });

  test('should display market opportunities', async ({ page }) => {
    const opportunitiesTitle = page.locator('h3:has-text("Oportunidades")');
    await expect(opportunitiesTitle).toBeVisible();
    
    // Check if at least one opportunity card exists (they are links)
    const opportunityLink = page.locator('a:has-text("$")').first();
    await expect(opportunityLink).toBeVisible();
  });
});
