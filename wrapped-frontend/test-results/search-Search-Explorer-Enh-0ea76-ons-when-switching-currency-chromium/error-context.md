# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: search.spec.js >> Search Explorer Enhancements >> should update price range options when switching currency
- Location: tests\search.spec.js:57:3

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3001/search
Call log:
  - navigating to "http://localhost:3001/search", waiting until "load"

```

# Test source

```ts
  1  | const { test, expect } = require('@playwright/test');
  2  | 
  3  | test.describe('Search Explorer Enhancements', () => {
  4  |   test.beforeEach(async ({ page }) => {
> 5  |     await page.goto('/search');
     |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3001/search
  6  |     // Wait for the page to load
  7  |     await page.waitForLoadState('networkidle');
  8  |   });
  9  | 
  10 |   test('should display improved search bar with new placeholder', async ({ page }) => {
  11 |     const searchBar = page.locator('input[placeholder="Marca, modelo, año, provincia o precio..."]');
  12 |     await expect(searchBar).toBeVisible();
  13 |     
  14 |     // Test clear button
  15 |     await searchBar.fill('Toyota');
  16 |     const clearButton = page.locator('button:has(svg.lucide-x)');
  17 |     await expect(clearButton).toBeVisible();
  18 |     await clearButton.click();
  19 |     await expect(searchBar).toHaveValue('');
  20 |   });
  21 | 
  22 |   test('should display year range string selector', async ({ page }) => {
  23 |     const yearSelect = page.locator('select:has-text("Todos los años")');
  24 |     await expect(yearSelect).toBeVisible();
  25 |   });
  26 | 
  27 |   test('should toggle between List and Tree view for brands', async ({ page }) => {
  28 |     // Default is list view
  29 |     const gridButton = page.locator('aside button').first();
  30 |     const listButton = page.locator('aside button').nth(1);
  31 |     
  32 |     await expect(gridButton).toHaveClass(/bg-cyan-600/); // Active
  33 |     
  34 |     // Switch to Tree view
  35 |     await listButton.click();
  36 |     await expect(listButton).toHaveClass(/bg-cyan-600/);
  37 |     
  38 |     // Check tree view elements (e.g., search within tree)
  39 |     const treeSearch = page.locator('input[placeholder="Filtrar marcas o modelos..."]');
  40 |     await expect(treeSearch).toBeVisible();
  41 |   });
  42 | 
  43 |   test('should display currency toggle and default to CRC', async ({ page }) => {
  44 |     // Check that both CRC and USD buttons exist
  45 |     const crcBtn = page.locator('button:has-text("CRC")').first();
  46 |     const usdBtn = page.locator('button:has-text("USD")').first();
  47 |     await expect(crcBtn).toBeVisible();
  48 |     await expect(usdBtn).toBeVisible();
  49 |     
  50 |     // By default, CRC should be active (emerald background)
  51 |     await expect(crcBtn).toHaveClass(/bg-emerald-600/);
  52 |     
  53 |     // Label should indicate CRC
  54 |     await expect(page.locator('label:has-text("Rango de Precio (CRC)")').first()).toBeVisible();
  55 |   });
  56 | 
  57 |   test('should update price range options when switching currency', async ({ page }) => {
  58 |     // By default CRC is selected, so the Min dropdown should have '₡2M'
  59 |     const minSelect = page.locator('aside select').filter({ hasText: 'Min' });
  60 |     const maxSelect = page.locator('aside select').filter({ hasText: 'Max' });
  61 |     
  62 |     // Check that '₡2M' option exists
  63 |     await expect(minSelect.locator('option[value="2000000"]')).toHaveCount(1);
  64 |     
  65 |     // Switch to USD
  66 |     const usdBtn = page.locator('button:has-text("USD")');
  67 |     await usdBtn.click();
  68 |     
  69 |     // Label should indicate USD
  70 |     await expect(page.locator('label:has-text("Rango de Precio (USD)")').first()).toBeVisible();
  71 |     
  72 |     // Check that '$5k' option exists
  73 |     await expect(minSelect.locator('option[value="5000"]')).toHaveCount(1);
  74 |   });
  75 | 
  76 |   test('should display at least one data source', async ({ page }) => {
  77 |     // The label for data sources should be visible
  78 |     const sourceLabel = page.locator('label:has-text("Fuente de Datos")').first();
  79 |     await expect(sourceLabel).toBeVisible();
  80 |     
  81 |     // Check that there is at least one button in the container
  82 |     const sourceContainer = page.locator('aside').filter({ hasText: 'Fuente de Datos' });
  83 |     const sourceButtons = sourceContainer.locator('button');
  84 |     
  85 |     // Wait for at least one source button to be rendered (data from API)
  86 |     await page.waitForLoadState('networkidle');
  87 |     // If no data sources are fetched (API is slow or mocked empty), skip the count check instead of failing.
  88 |     try {
  89 |       await expect(sourceButtons.first()).toBeAttached({ timeout: 5000 });
  90 |     } catch (e) {
  91 |       console.log('API did not return data sources in time, skipping count check.');
  92 |       return;
  93 |     }
  94 |     
  95 |     const count = await sourceButtons.count();
  96 |     expect(count).toBeGreaterThan(0);
  97 |   });
  98 | });
  99 | 
```