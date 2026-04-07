
import asyncio
from playwright.async_api import async_playwright
import sys
import os
import importlib.util

# Emulate scraper.py path logic
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def get_stealth_class():
    """Foolproof way to get the Stealth class."""
    # Try the most direct way first
    try:
        from playwright_stealth.stealth import Stealth
        return Stealth
    except ImportError:
        pass
        
    # Try the package-level export
    try:
        from playwright_stealth import Stealth
        return Stealth
    except ImportError:
        pass
        
    # Manual load from site-packages
    try:
        import playwright_stealth
        spec = importlib.util.find_spec("playwright_stealth.stealth")
        if spec:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return getattr(module, 'Stealth')
    except Exception as e:
        print(f"Deep import failure: {e}")
        
    return None

async def test_launch():
    print("Testing browser launch with dynamic stealth...")
    Stealth = get_stealth_class()
    if not Stealth:
        print("CRITICAL FAILURE: Could not find Stealth class anywhere!")
        return

    async with async_playwright() as p:
        from core.browser import launch_comet
        from core.cli import CLILogger
        
        logger = CLILogger()
        # We use a dummy port to avoid conflict if one is running
        browser, context, page, proc = await launch_comet(p, port=9223, logger=logger)
        
        if page:
            print("SUCCESS: Browser launched!")
            # Manually apply it here to be sure
            await Stealth().apply_stealth_async(page)
            print("SUCCESS: Stealth applied manually!")
            await page.close()
            await browser.close()
            if proc: proc.terminate()
        else:
            print("FAILED: Page is None")

if __name__ == "__main__":
    asyncio.run(test_launch())
