import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("Navigating to crautos.com/autosusados/...")
        await page.goto("https://crautos.com/autosusados/", wait_until="networkidle")
        
        # Wait a bit for overlays
        await asyncio.sleep(5)
        
        print("Checking for consent overlays...")
        # Common Google/Funding Choices selectors
        selectors = [
            ".fc-cta-consent",
            ".fc-button-label",
            "button:has-text('Consent')",
            "button:has-text('Accept')",
            "button:has-text('Acepto')",
            "button:has-text('AGREE')",
            ".fc-primary-button"
        ]
        
        for selector in selectors:
            try:
                element = page.locator(selector)
                if await element.is_visible():
                    print(f"Found visible selector: {selector}")
                    text = await element.inner_text()
                    print(f"Text: {text}")
            except Exception as e:
                pass

        # Take a screenshot to see the overlay
        await page.screenshot(path="consent_check.png")
        print("Screenshot saved to consent_check.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
