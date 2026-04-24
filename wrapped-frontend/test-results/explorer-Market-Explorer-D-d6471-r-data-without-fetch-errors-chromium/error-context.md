# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: explorer.spec.js >> Market Explorer Data Verification >> should display car data without fetch errors
- Location: tests/explorer.spec.js:4:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('text=Toyota')
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 10000ms
  - waiting for locator('text=Toyota')

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e2]:
    - generic:
      - img
    - banner [ref=e3]:
      - generic [ref=e4]:
        - img [ref=e6]
        - button [ref=e10]:
          - img [ref=e11]
      - heading "EL FUTURO DEL ANÁLISIS AUTOMOTRIZ" [level=1] [ref=e17]:
        - text: EL FUTURO DEL
        - text: ANÁLISIS AUTOMOTRIZ
      - paragraph [ref=e18]: Explora el mercado automotriz de Costa Rica con datos en tiempo real.
    - main [ref=e19]:
      - link "Tour Background Interactive Tour Descubre tu historia con el mercado. Un viaje inmersivo, estilo Spotify Wrapped. COMENZAR" [ref=e20] [cursor=pointer]:
        - /url: /tour
        - generic [ref=e21]:
          - generic:
            - generic:
              - img "Tour Background"
          - generic [ref=e22]:
            - generic [ref=e23]:
              - img [ref=e25]
              - heading "Interactive Tour" [level=2] [ref=e28]
            - paragraph [ref=e29]: Descubre tu historia con el mercado. Un viaje inmersivo, estilo Spotify Wrapped.
            - button "COMENZAR" [ref=e30]:
              - text: COMENZAR
              - img [ref=e31]
      - link "Search Background Market Explorer Top Ventas Híbridos Busca y compara vehículos con filtros avanzados potenciados por IA. AI suggest EXPLORAR" [ref=e33] [cursor=pointer]:
        - /url: /search
        - generic [ref=e34]:
          - generic:
            - generic:
              - img "Search Background"
          - generic [ref=e35]:
            - generic [ref=e36]:
              - img [ref=e38]
              - heading "Market Explorer" [level=2] [ref=e41]
            - generic [ref=e42]:
              - generic [ref=e43]: Top Ventas
              - generic [ref=e44]: Híbridos
            - paragraph [ref=e45]: Busca y compara vehículos con filtros avanzados potenciados por IA.
            - generic [ref=e46]:
              - img [ref=e47]
              - generic [ref=e53]: AI suggest
            - button "EXPLORAR" [ref=e54]:
              - text: EXPLORAR
              - img [ref=e55]
    - navigation [ref=e57]:
      - link "Inicio" [ref=e58] [cursor=pointer]:
        - /url: /
        - img [ref=e60]
        - generic [ref=e63]: Inicio
      - link "Tour" [ref=e64] [cursor=pointer]:
        - /url: /tour
        - img [ref=e66]
        - generic [ref=e69]: Tour
      - link "Explorer" [ref=e70] [cursor=pointer]:
        - /url: /search
        - img [ref=e72]
        - generic [ref=e75]: Explorer
      - link "Insights" [ref=e76] [cursor=pointer]:
        - /url: /insights
        - img [ref=e78]
        - generic [ref=e83]: Insights
    - contentinfo [ref=e84]:
      - generic [ref=e85]:
        - generic [ref=e86]: v.4.3.0 UNIFIED
        - generic [ref=e87]: EST. 2026
  - button "Open Next.js Dev Tools" [ref=e93] [cursor=pointer]:
    - img [ref=e94]
  - alert [ref=e97]
```

# Test source

```ts
  1  | const { test, expect } = require('@playwright/test');
  2  |
  3  | test.describe('Market Explorer Data Verification', () => {
  4  |   test('should display car data without fetch errors', async ({ page }) => {
  5  |     // Navigate to the home page
  6  |     await page.goto('/');
  7  |
  8  |     // Wait for the page to load initial elements
  9  |     await page.waitForLoadState('networkidle');
  10 |
  11 |     // Screenshot for visual verification
  12 |     await page.screenshot({ path: 'test-results/homepage-initial.png', fullPage: true });
  13 |
  14 |     // Check that we don't have the "Failed to fetch" error seen in user's screenshot
  15 |     const errorOverlay = page.locator('text=Failed to fetch');
  16 |     await expect(errorOverlay).not.toBeVisible();
  17 |
  18 |     // Verify some indicative data is present (e.g., brand counts or model names)
  19 |     // Based on the code, we expect brand categories to show up in the stories/explorer
  20 |     // If the API failed, these will likely be empty or placeholders
  21 |     const brandItem = page.locator('text=Toyota');
> 22 |     await expect(brandItem).toBeVisible({ timeout: 10000 });
     |                             ^ Error: expect(locator).toBeVisible() failed
  23 |   });
  24 |
  25 |   test('explorer page should load statistics', async ({ page }) => {
  26 |     await page.goto('/explorer');
  27 |     await page.waitForLoadState('networkidle');
  28 |     await page.screenshot({ path: 'test-results/explorer-initial.png', fullPage: true });
  29 |
  30 |     // In the explorer, we expect facets and stats cards
  31 |     await expect(page.locator('text=Precio Promedio')).toBeVisible();
  32 |
  33 |     // Check that specific data is loaded (not just the title)
  34 |     // The previous screenshot showed a specific avg price if it worked
  35 |     const statsValue = page.locator('h3:has-text("$")');
  36 |     await expect(statsValue).toBeVisible();
  37 |   });
  38 | });
  39 |
```