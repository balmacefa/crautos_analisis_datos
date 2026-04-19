const { test, expect } = require('@playwright/test');

test.describe('Market Explorer Data Verification', () => {
  test('should display car data without fetch errors', async ({ page }) => {
    // Navigate to the home page
    await page.goto('/');

    // Wait for the page to load initial elements
    await page.waitForLoadState('networkidle');

    // Screenshot for visual verification
    await page.screenshot({ path: 'test-results/homepage-initial.png', fullPage: true });

    // Check that we don't have the "Failed to fetch" error seen in user's screenshot
    const errorOverlay = page.locator('text=Failed to fetch');
    await expect(errorOverlay).not.toBeVisible();

    // Verify some indicative data is present (e.g., brand counts or model names)
    // Based on the code, we expect brand categories to show up in the stories/explorer
    // If the API failed, these will likely be empty or placeholders
    const brandItem = page.locator('text=Toyota'); 
    await expect(brandItem).toBeVisible({ timeout: 10000 });
  });

  test('explorer page should load statistics', async ({ page }) => {
    await page.goto('/explorer');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'test-results/explorer-initial.png', fullPage: true });

    // In the explorer, we expect facets and stats cards
    await expect(page.locator('text=Precio Promedio')).toBeVisible();
    
    // Check that specific data is loaded (not just the title)
    // The previous screenshot showed a specific avg price if it worked
    const statsValue = page.locator('h3:has-text("$")');
    await expect(statsValue).toBeVisible();
  });
});
