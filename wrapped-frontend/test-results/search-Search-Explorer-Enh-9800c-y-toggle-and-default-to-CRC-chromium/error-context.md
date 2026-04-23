# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: search.spec.js >> Search Explorer Enhancements >> should display currency toggle and default to CRC
- Location: tests\search.spec.js:43:3

# Error details

```
Test timeout of 30000ms exceeded while running "beforeEach" hook.
```

```
Error: page.goto: Test timeout of 30000ms exceeded.
Call log:
  - navigating to "http://localhost:3001/search", waiting until "load"

```

# Page snapshot

```yaml
- main [ref=e2]:
  - generic:
    - img
  - generic [ref=e4]:
    - generic [ref=e5]:
      - link [ref=e6] [cursor=pointer]:
        - /url: /
        - img [ref=e7]
      - generic [ref=e9]:
        - heading "Crautos Search" [level=2] [ref=e10]
        - paragraph [ref=e11]: Market Explorer v2
    - generic [ref=e12]:
      - img [ref=e13]
      - textbox "Marca, modelo, año, provincia o precio..." [ref=e16]
    - button "Filtros" [ref=e18]:
      - img [ref=e19]
      - text: Filtros
  - generic [ref=e21]:
    - complementary [ref=e22]:
      - generic [ref=e23]:
        - heading "Parámetros" [level=3] [ref=e24]:
          - img [ref=e25]
          - text: Parámetros
        - generic [ref=e28]:
          - generic [ref=e30]:
            - generic [ref=e31]: Vehículo
            - generic [ref=e32]:
              - button [ref=e33]:
                - img [ref=e34]
              - button [ref=e36]:
                - img [ref=e37]
          - generic [ref=e38]:
            - generic [ref=e39]:
              - generic [ref=e40]: Rango de Precio (CRC)
              - generic [ref=e41]:
                - button "CRC" [ref=e42]
                - button "USD" [ref=e43]
            - generic [ref=e44]:
              - generic [ref=e45]:
                - combobox [ref=e46]:
                  - option "Min" [selected]
                  - option "₡2M"
                  - option "₡5M"
                  - option "₡10M"
                  - option "₡15M"
                  - option "₡20M"
                  - option "₡30M"
                - img
              - generic [ref=e47]:
                - combobox [ref=e48]:
                  - option "Max" [selected]
                  - option "₡5M"
                  - option "₡10M"
                  - option "₡15M"
                  - option "₡20M"
                  - option "₡30M"
                  - option "₡50M"
                - img
          - generic [ref=e49]:
            - text: Años
            - generic [ref=e50]:
              - combobox [ref=e51]:
                - option "Todos los años" [selected]
              - img
          - generic [ref=e52]:
            - text: Provincia
            - generic [ref=e53]:
              - combobox [ref=e54]:
                - option "Todas las provincias" [selected]
              - img
          - generic [ref=e55]: Combustible
          - generic [ref=e56]:
            - text: Ordenar por
            - generic [ref=e57]:
              - combobox [ref=e58]:
                - option "Más Recientes" [selected]
                - option "Menor Precio"
                - option "Mayor Precio"
                - option "Menor Kilometraje"
              - img
          - generic [ref=e59]: Fuente de Datos
      - generic [ref=e60]:
        - generic [ref=e61]:
          - img [ref=e62]
          - text: Sugerencia IA
        - paragraph [ref=e65]: "\"Recuerda que los autos con menos de 80,000km suelen tener mejor valor de reventa en Costa Rica.\""
    - generic [ref=e68]:
      - heading "Explora el Mercado" [level=1] [ref=e69]
      - paragraph [ref=e70]: Mostrando 0 de 0 anuncios activos
```

# Test source

```ts
  1  | const { test, expect } = require('@playwright/test');
  2  | 
  3  | test.describe('Search Explorer Enhancements', () => {
  4  |   test.beforeEach(async ({ page }) => {
> 5  |     await page.goto('/search');
     |                ^ Error: page.goto: Test timeout of 30000ms exceeded.
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
  29 |     const gridButton = page.locator('button:has(svg.lucide-grid)');
  30 |     const listButton = page.locator('button:has(svg.lucide-list)');
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
  45 |     const crcBtn = page.locator('button:has-text("CRC")');
  46 |     const usdBtn = page.locator('button:has-text("USD")');
  47 |     await expect(crcBtn).toBeVisible();
  48 |     await expect(usdBtn).toBeVisible();
  49 |     
  50 |     // By default, CRC should be active (emerald background)
  51 |     await expect(crcBtn).toHaveClass(/bg-emerald-600/);
  52 |     
  53 |     // Label should indicate CRC
  54 |     await expect(page.locator('label:has-text("Rango de Precio (CRC)")')).toBeVisible();
  55 |   });
  56 | 
  57 |   test('should update price range options when switching currency', async ({ page }) => {
  58 |     // By default CRC is selected, so the Min dropdown should have '₡2M'
  59 |     const minSelect = page.locator('select').filter({ hasText: 'Min' }).first();
  60 |     const maxSelect = page.locator('select').filter({ hasText: 'Max' }).last();
  61 |     
  62 |     // Check that '₡2M' option exists
  63 |     await expect(minSelect.locator('option[value="2000000"]')).toBeVisible();
  64 |     
  65 |     // Switch to USD
  66 |     const usdBtn = page.locator('button:has-text("USD")');
  67 |     await usdBtn.click();
  68 |     
  69 |     // Label should indicate USD
  70 |     await expect(page.locator('label:has-text("Rango de Precio (USD)")')).toBeVisible();
  71 |     
  72 |     // Check that '$5k' option exists
  73 |     await expect(minSelect.locator('option[value="5000"]')).toBeVisible();
  74 |   });
  75 | 
  76 |   test('should display at least one data source', async ({ page }) => {
  77 |     // The label for data sources should be visible
  78 |     const sourceLabel = page.locator('label:has-text("Fuente de Datos")');
  79 |     await expect(sourceLabel).toBeVisible();
  80 |     
  81 |     // Check that there is at least one button in the container
  82 |     const sourceButtons = page.locator('div:has(> label:has-text("Fuente de Datos"))').locator('button');
  83 |     
  84 |     // Wait for at least one source button to be rendered (data from API)
  85 |     await expect(sourceButtons.first()).toBeVisible({ timeout: 15000 });
  86 |     
  87 |     const count = await sourceButtons.count();
  88 |     expect(count).toBeGreaterThan(0);
  89 |   });
  90 | });
  91 | 
```