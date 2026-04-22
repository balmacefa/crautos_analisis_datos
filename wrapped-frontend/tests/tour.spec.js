const { test, expect } = require('@playwright/test');

test.describe('Interactive Wrapped Tour', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/tour');
    await page.waitForLoadState('networkidle');
  });

  test('should complete the interactive story flow', async ({ page }) => {
    // 1. Intro Slide
    await expect(page.locator('h1:has-text("CRAUTOS")')).toBeVisible();
    await expect(page.locator('h1:has-text("WRAPPED")')).toBeVisible();
    
    // Start the tour
    await page.click('text=Comenzar la historia');
    
    // 2. Magnitude Slide (Wait for stats to load)
    await expect(page.locator('text=La Magnitud')).toBeVisible();
    // Use an aria-label or just the text of the button to go next
    const nextButton = page.locator('button >> svg.lucide-arrow-right').locator('xpath=..');
    
    // Navigate through a few slides to ensure flow works
    for(let i=0; i<3; i++) {
        await nextButton.click();
        await page.waitForTimeout(500); // Wait for animation
    }
    
    // Should be at slide 5 or so
    await expect(page.locator('text=/ 10')).toBeVisible();
  });

  test('should be able to go back to home from tour', async ({ page }) => {
    const backHome = page.locator('a:has(svg.lucide-arrow-left)');
    await backHome.click();
    await expect(page).toHaveURL('/');
  });
});
