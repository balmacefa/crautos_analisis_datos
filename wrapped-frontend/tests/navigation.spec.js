const { test, expect } = require('@playwright/test');

test.describe('Global Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should navigate between main sections using bottom nav', async ({ page }) => {
    // Check initial page
    await expect(page).toHaveURL('/');
    
    // Navigate to Tour
    await page.click('nav >> text=Tour');
    await expect(page).toHaveURL(/\/tour/);
    
    // Navigate to Explorer (Search)
    await page.click('nav >> text=Explorer');
    await expect(page).toHaveURL(/\/search/);
    
    // Navigate to Insights
    await page.click('nav >> text=Insights');
    await expect(page).toHaveURL(/\/insights/);
    
    // Back to Inicio
    await page.click('nav >> text=Inicio');
    await expect(page).toHaveURL('/');
  });

  test('should navigate using home page cards', async ({ page }) => {
    // Navigate to Tour card
    await page.click('text=Interactive Tour');
    await expect(page).toHaveURL(/\/tour/);
    
    await page.goto('/');
    
    // Navigate to Market Explorer card
    await page.click('text=Market Explorer');
    await expect(page).toHaveURL(/\/search/);
  });
});
