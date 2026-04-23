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

  test('should display currency toggle and default to CRC', async ({ page }) => {
    // Check that both CRC and USD buttons exist
    const crcBtn = page.locator('button:has-text("CRC")');
    const usdBtn = page.locator('button:has-text("USD")');
    await expect(crcBtn).toBeVisible();
    await expect(usdBtn).toBeVisible();
    
    // By default, CRC should be active (emerald background)
    await expect(crcBtn).toHaveClass(/bg-emerald-600/);
    
    // Label should indicate CRC
    await expect(page.locator('label:has-text("Rango de Precio (CRC)")')).toBeVisible();
  });

  test('should update price range options when switching currency', async ({ page }) => {
    // By default CRC is selected, so the Min dropdown should have '₡2M'
    const minSelect = page.locator('select').filter({ hasText: 'Min' }).first();
    const maxSelect = page.locator('select').filter({ hasText: 'Max' }).last();
    
    // Check that '₡2M' option exists
    await expect(minSelect.locator('option[value="2000000"]')).toBeVisible();
    
    // Switch to USD
    const usdBtn = page.locator('button:has-text("USD")');
    await usdBtn.click();
    
    // Label should indicate USD
    await expect(page.locator('label:has-text("Rango de Precio (USD)")')).toBeVisible();
    
    // Check that '$5k' option exists
    await expect(minSelect.locator('option[value="5000"]')).toBeVisible();
  });

  test('should display at least one data source', async ({ page }) => {
    // The label for data sources should be visible
    const sourceLabel = page.locator('label:has-text("Fuente de Datos")');
    await expect(sourceLabel).toBeVisible();
    
    // Check that there is at least one button in the container
    const sourceButtons = page.locator('div:has(> label:has-text("Fuente de Datos"))').locator('button');
    
    // Wait for at least one source button to be rendered (data from API)
    await expect(sourceButtons.first()).toBeVisible({ timeout: 15000 });
    
    const count = await sourceButtons.count();
    expect(count).toBeGreaterThan(0);
  });
});
