
import asyncio
from playwright.async_api import async_playwright
import sys
import os

# Emulate scraper.py path logic
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

async def test_launch():
    print("Testing browser launch with stealth...")
    async with async_playwright() as p:
        from core.browser import launch_comet
        from core.cli import CLILogger
        
        logger = CLILogger()
        # We use a dummy port to avoid conflict if one is running
        browser, context, page, proc = await launch_comet(p, port=9223, logger=logger)
        
        if page:
            print("SUCCESS: Browser launched and stealth applied!")
            await page.close()
            await browser.close()
            if proc: proc.terminate()
        else:
            print("FAILED: Page is None")

if __name__ == "__main__":
    asyncio.run(test_launch())
