# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: insights.spec.js >> Insights Dashboard >> should display market opportunities
- Location: tests/insights.spec.js:27:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('a:has-text("$")').first()
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('a:has-text("$")').first()

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - main [ref=e2]:
    - generic:
      - img
    - generic [ref=e4]:
      - generic [ref=e5]:
        - link [ref=e6] [cursor=pointer]:
          - /url: /
          - img [ref=e7]
        - generic [ref=e9]:
          - heading "MARKETINSIGHTS" [level=1] [ref=e10]
          - paragraph [ref=e11]: Dash Application Analytics V2
      - generic [ref=e15]: Live Integration
    - generic [ref=e16]:
      - generic [ref=e17]:
        - generic [ref=e18]:
          - img [ref=e20]
          - generic [ref=e24]:
            - paragraph [ref=e25]: Muestra
            - heading "..." [level=2] [ref=e26]
        - generic [ref=e27]:
          - img [ref=e29]
          - generic [ref=e31]:
            - paragraph [ref=e32]: Promedio
            - heading "$undefined" [level=2] [ref=e33]
        - generic [ref=e34]:
          - img [ref=e36]
          - generic [ref=e39]:
            - paragraph [ref=e40]: Uso Medio
            - heading "84.2K KM" [level=2] [ref=e41]
        - generic [ref=e42]:
          - img [ref=e44]
          - generic [ref=e47]:
            - paragraph [ref=e48]: Tendencia
            - heading "+12.4%" [level=2] [ref=e49]
      - generic [ref=e50]:
        - generic [ref=e51]:
          - generic [ref=e52]:
            - generic [ref=e53]:
              - img [ref=e55]
              - heading "Análisis de Depreciación" [level=3] [ref=e58]
            - generic [ref=e59]:
              - button "Toyota" [ref=e60]
              - button "Hyundai" [ref=e61]
              - button "Nissan" [ref=e62]
              - button "Kia" [ref=e63]
              - button "Suzuki" [ref=e64]
            - generic [ref=e67]:
              - list [ref=e69]:
                - listitem [ref=e70]:
                  - img "Hyundai legend icon" [ref=e71]
                  - text: Hyundai
                - listitem [ref=e73]:
                  - img "Nissan legend icon" [ref=e74]
                  - text: Nissan
                - listitem [ref=e76]:
                  - img "Toyota legend icon" [ref=e77]
                  - text: Toyota
              - application [ref=e79]
          - generic [ref=e84]:
            - generic [ref=e85]:
              - heading "Mejor Relación $/KM" [level=3] [ref=e86]
              - application [ref=e90]
            - heading "Oportunidades" [level=3] [ref=e92]
        - generic [ref=e93]:
          - generic [ref=e95]:
            - generic [ref=e96]:
              - paragraph [ref=e97]: Caro
              - heading [level=4]
              - paragraph [ref=e98]: $
            - generic [ref=e99]:
              - paragraph [ref=e100]: Barato
              - heading [level=4]
              - paragraph [ref=e101]: $
          - application [ref=e106]
  - generic [ref=e111] [cursor=pointer]:
    - button "Open Next.js Dev Tools" [ref=e112]:
      - img [ref=e113]
    - generic [ref=e116]:
      - button "Open issues overlay" [ref=e117]:
        - generic [ref=e118]:
          - generic [ref=e119]: "7"
          - generic [ref=e120]: "8"
        - generic [ref=e121]:
          - text: Issue
          - generic [ref=e122]: s
      - button "Collapse issues badge" [ref=e123]:
        - img [ref=e124]
  - alert [ref=e126]
```

# Test source

```ts
  1  | const { test, expect } = require('@playwright/test');
  2  |
  3  | test.describe('Insights Dashboard', () => {
  4  |   test.beforeEach(async ({ page }) => {
  5  |     await page.goto('/insights');
  6  |     await page.waitForLoadState('networkidle');
  7  |   });
  8  |
  9  |   test('should display aggregate statistics cards', async ({ page }) => {
  10 |     // Check for core metric labels
  11 |     await expect(page.locator('text=Muestra')).toBeVisible();
  12 |     await expect(page.locator('text=Promedio')).toBeVisible();
  13 |     await expect(page.locator('text=Uso Medio')).toBeVisible();
  14 |     await expect(page.locator('text=Tendencia')).toBeVisible();
  15 |   });
  16 |
  17 |   test('should load charts and data visualizations', async ({ page }) => {
  18 |     // Depreciation chart container
  19 |     const depreciationChart = page.locator('.recharts-responsive-container').first();
  20 |     await expect(depreciationChart).toBeVisible();
  21 |
  22 |     // Check for brand toggles in depreciation chart
  23 |     await expect(page.locator('button:has-text("Toyota")')).toBeVisible();
  24 |     await expect(page.locator('button:has-text("Hyundai")')).toBeVisible();
  25 |   });
  26 |
  27 |   test('should display market opportunities', async ({ page }) => {
  28 |     const opportunitiesTitle = page.locator('h3:has-text("Oportunidades")');
  29 |     await expect(opportunitiesTitle).toBeVisible();
  30 |
  31 |     // Check if at least one opportunity card exists (they are links)
  32 |     const opportunityLink = page.locator('a:has-text("$")').first();
> 33 |     await expect(opportunityLink).toBeVisible();
     |                                   ^ Error: expect(locator).toBeVisible() failed
  34 |   });
  35 | });
  36 |
```