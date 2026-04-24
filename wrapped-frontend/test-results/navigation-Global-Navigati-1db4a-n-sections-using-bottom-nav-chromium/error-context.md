# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: navigation.spec.js >> Global Navigation >> should navigate between main sections using bottom nav
- Location: tests/navigation.spec.js:9:3

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('nav').locator('text=Explorer')

```

# Page snapshot

```yaml
- generic [ref=e1]:
  - generic [active]:
    - generic [ref=e4]:
      - generic [ref=e5]:
        - generic [ref=e6]:
          - navigation [ref=e7]:
            - button "previous" [disabled] [ref=e8]:
              - img "previous" [ref=e9]
            - generic [ref=e11]:
              - generic [ref=e12]: 1/
              - text: "9"
            - button "next" [ref=e13] [cursor=pointer]:
              - img "next" [ref=e14]
          - img
        - generic [ref=e16]:
          - generic [ref=e17]:
            - img [ref=e18]
            - generic "Latest available version is detected (16.2.4)." [ref=e20]: Next.js 16.2.4
            - generic [ref=e21]: Turbopack
          - img
      - generic [ref=e22]:
        - dialog "Console Error" [ref=e23]:
          - generic [ref=e26]:
            - generic [ref=e27]:
              - generic [ref=e28]:
                - generic [ref=e30]: Console Error
                - generic [ref=e31]:
                  - button "Copy Error Info" [ref=e32] [cursor=pointer]:
                    - img [ref=e33]
                  - button "No related documentation found" [disabled] [ref=e35]:
                    - img [ref=e36]
                  - button "Attach Node.js inspector" [ref=e38] [cursor=pointer]:
                    - img [ref=e39]
              - generic [ref=e48]:
                - text: "[[[[Network Error] ]Could not connect to"
                - link "http://localhost:8000/api/insights/summary" [ref=e49] [cursor=pointer]:
                  - /url: http://localhost:8000/api/insights/summary
                - text: "]@ Failed to fetch (518ms)"
            - generic [ref=e50]:
              - generic [ref=e51]:
                - paragraph [ref=e53]:
                  - img [ref=e55]
                  - generic [ref=e57]: src/lib/api.js (62:13) @ robustFetcher
                  - button "Open in editor" [ref=e58] [cursor=pointer]:
                    - img [ref=e60]
                - generic [ref=e63]:
                  - generic [ref=e64]: "60 | } catch (err) {"
                  - generic [ref=e65]: 61 | const duration = Date.now() - start;
                  - generic [ref=e66]: "> 62 | console.error(`%c[Network Error] %cCould not connect to %c${url} %c@ ${err.message} (%..."
                  - generic [ref=e67]: "| ^"
                  - generic [ref=e68]: "63 | 'color: #ef4444; font-weight: bold',"
                  - generic [ref=e69]: "64 | 'color: #f87171',"
                  - generic [ref=e70]: "65 | 'color: #94a3b8',"
              - generic [ref=e71]:
                - generic [ref=e72]:
                  - paragraph [ref=e73]:
                    - text: Call Stack
                    - generic [ref=e74]: "5"
                  - button "Show 4 ignore-listed frame(s)" [ref=e75] [cursor=pointer]:
                    - text: Show 4 ignore-listed frame(s)
                    - img [ref=e76]
                - generic [ref=e78]:
                  - generic [ref=e79]:
                    - text: robustFetcher
                    - button "Open robustFetcher in editor" [ref=e80] [cursor=pointer]:
                      - img [ref=e81]
                  - text: src/lib/api.js (62:13)
          - generic [ref=e83]: "1"
          - generic [ref=e84]: "2"
        - contentinfo [ref=e85]:
          - region "Error feedback" [ref=e86]:
            - paragraph [ref=e87]:
              - link "Was this helpful?" [ref=e88] [cursor=pointer]:
                - /url: https://nextjs.org/telemetry#error-feedback
            - button "Mark as helpful" [ref=e89] [cursor=pointer]:
              - img [ref=e90]
            - button "Mark as not helpful" [ref=e93] [cursor=pointer]:
              - img [ref=e94]
    - generic [ref=e100] [cursor=pointer]:
      - button "Open Next.js Dev Tools" [ref=e101]:
        - img [ref=e102]
      - generic [ref=e105]:
        - button "Open issues overlay" [ref=e106]:
          - generic [ref=e107]:
            - generic [ref=e108]: "8"
            - generic [ref=e109]: "9"
          - generic [ref=e110]:
            - text: Issue
            - generic [ref=e111]: s
        - button "Collapse issues badge" [ref=e112]:
          - img [ref=e113]
  - generic [ref=e116]:
    - img [ref=e117]
    - heading "This page couldn’t load" [level=1] [ref=e119]
    - paragraph [ref=e120]: Reload to try again, or go back.
    - generic [ref=e121]:
      - button "Reload" [ref=e123] [cursor=pointer]
      - button "Back" [ref=e124] [cursor=pointer]
```

# Test source

```ts
  1  | const { test, expect } = require('@playwright/test');
  2  |
  3  | test.describe('Global Navigation', () => {
  4  |   test.beforeEach(async ({ page }) => {
  5  |     await page.goto('/');
  6  |     await page.waitForLoadState('networkidle');
  7  |   });
  8  |
  9  |   test('should navigate between main sections using bottom nav', async ({ page }) => {
  10 |     // Check initial page
  11 |     await expect(page).toHaveURL('/');
  12 |
  13 |     // Navigate to Tour
  14 |     await page.click('nav >> text=Tour');
  15 |     await expect(page).toHaveURL(/\/tour/);
  16 |
  17 |     // Navigate to Explorer (Search)
> 18 |     await page.click('nav >> text=Explorer');
     |                ^ Error: page.click: Test timeout of 30000ms exceeded.
  19 |     await expect(page).toHaveURL(/\/search/);
  20 |
  21 |     // Navigate to Insights
  22 |     await page.click('nav >> text=Insights');
  23 |     await expect(page).toHaveURL(/\/insights/);
  24 |
  25 |     // Back to Inicio
  26 |     await page.click('nav >> text=Inicio');
  27 |     await expect(page).toHaveURL('/');
  28 |   });
  29 |
  30 |   test('should navigate using home page cards', async ({ page }) => {
  31 |     // Navigate to Tour card
  32 |     await page.click('text=Interactive Tour');
  33 |     await expect(page).toHaveURL(/\/tour/);
  34 |
  35 |     await page.goto('/');
  36 |
  37 |     // Navigate to Market Explorer card
  38 |     await page.click('text=Market Explorer');
  39 |     await expect(page).toHaveURL(/\/search/);
  40 |   });
  41 | });
  42 |
```