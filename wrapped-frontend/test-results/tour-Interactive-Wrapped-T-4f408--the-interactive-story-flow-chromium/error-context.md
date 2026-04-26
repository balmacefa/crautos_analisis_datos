# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tour.spec.js >> Interactive Wrapped Tour >> should complete the interactive story flow
- Location: tests\tour.spec.js:9:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('h1:has-text("CRAUTOS")')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('h1:has-text("CRAUTOS")')

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
                - text: "]@ Failed to fetch (2627ms)"
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
  3  | test.describe('Interactive Wrapped Tour', () => {
  4  |   test.beforeEach(async ({ page }) => {
  5  |     await page.goto('/tour');
  6  |     await page.waitForLoadState('networkidle');
  7  |   });
  8  | 
  9  |   test('should complete the interactive story flow', async ({ page }) => {
  10 |     // 1. Intro Slide
> 11 |     await expect(page.locator('h1:has-text("CRAUTOS")')).toBeVisible();
     |                                                          ^ Error: expect(locator).toBeVisible() failed
  12 |     await expect(page.locator('h1:has-text("WRAPPED")')).toBeVisible();
  13 |     
  14 |     // Start the tour
  15 |     await page.click('text=Comenzar la historia');
  16 |     
  17 |     // 2. Magnitude Slide (Wait for stats to load)
  18 |     await expect(page.locator('text=La Magnitud')).toBeVisible();
  19 |     // Use an aria-label or just the text of the button to go next
  20 |     const nextButton = page.locator('button >> svg.lucide-arrow-right').locator('xpath=..');
  21 |     
  22 |     // Navigate through a few slides to ensure flow works
  23 |     for(let i=0; i<3; i++) {
  24 |         await nextButton.click();
  25 |         await page.waitForTimeout(500); // Wait for animation
  26 |     }
  27 |     
  28 |     // Should be at slide 5 or so
  29 |     await expect(page.locator('text=/ 10')).toBeVisible();
  30 |   });
  31 | 
  32 |   test('should be able to go back to home from tour', async ({ page }) => {
  33 |     const backHome = page.locator('a:has(svg.lucide-arrow-left)');
  34 |     await backHome.click();
  35 |     await expect(page).toHaveURL('/');
  36 |   });
  37 | });
  38 | 
```