# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: explorer.spec.js >> Market Explorer Data Verification >> should display car data without fetch errors
- Location: tests\explorer.spec.js:4:3

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.waitForLoadState: Test timeout of 30000ms exceeded.
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - main [ref=e2]:
    - generic:
      - generic:
        - img
      - generic:
        - img
      - generic:
        - img
      - generic:
        - img
      - generic:
        - img
    - generic [ref=e5]:
      - img [ref=e7]
      - heading "Hallazgos únicos..." [level=2] [ref=e9]
  - button "Open Next.js Dev Tools" [ref=e15] [cursor=pointer]:
    - img [ref=e16]
  - alert [ref=e19]
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
> 9  |     await page.waitForLoadState('networkidle');
     |                ^ Error: page.waitForLoadState: Test timeout of 30000ms exceeded.
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
  22 |     await expect(brandItem).toBeVisible({ timeout: 10000 });
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