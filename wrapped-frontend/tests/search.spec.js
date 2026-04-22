const { test, expect } = require('@playwright/test');

test.describe('Search Explorer Enhancements', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/search');
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
  });

  test('should display improved search bar with new placeholder', async ({ page }) => {
    const searchBar = page.locator('input[placeholder="Marca, modelo, año, provincia o precio..."]');
    await expect(searchBar).toBeVisible();
    
    // Test clear button
    await searchBar.fill('Toyota');
    const clearButton = page.locator('button:has(svg.lucide-x)');
    await expect(clearButton).toBeVisible();
    await clearButton.click();
    await expect(searchBar).toHaveValue('');
  });

  test('should display year range string selector', async ({ page }) => {
    const yearSelect = page.locator('select:has-text("Todos los años")');
    await expect(yearSelect).toBeVisible();
  });

  test('should toggle between List and Tree view for brands', async ({ page }) => {
    // Default is list view
    const gridButton = page.locator('button:has(svg.lucide-grid)');
    const listButton = page.locator('button:has(svg.lucide-list)');
    
    await expect(gridButton).toHaveClass(/bg-cyan-600/); // Active
    
    // Switch to Tree view
    await listButton.click();
    await expect(listButton).toHaveClass(/bg-cyan-600/);
    
    // Check tree view elements (e.g., search within tree)
    const treeSearch = page.locator('input[placeholder="Filtrar marcas o modelos..."]');
    await expect(treeSearch).toBeVisible();
  });

  test('should display price range quick filters', async ({ page }) => {
    await expect(page.locator('text=Menos de $10k')).toBeVisible();
    await expect(page.locator('text=$10k - $25k')).toBeVisible();
    await expect(page.locator('text=Más de $50k')).toBeVisible();
  });

  test('should update results when a price range is selected', async ({ page }) => {
    const priceButton = page.locator('text=Menos de $10k');
    await priceButton.click();
    
    // Verify that the price range is highlighted (emerald color in our code)
    await expect(priceButton).toHaveClass(/bg-emerald-600/);
    
    // Verify that the numeric inputs are updated (optional, but good)
    const minInput = page.locator('input[placeholder="Min"]');
    const maxInput = page.locator('input[placeholder="Max"]');
    await expect(minInput).toHaveValue('0');
    await expect(maxInput).toHaveValue('10000');
  });

  test('should display source (fuente) filters', async ({ page }) => {
    // The label for data sources should be visible
    const sourceLabel = page.locator('label:has-text("Fuente de Datos")');
    await expect(sourceLabel).toBeVisible();
  });
});
