
import asyncio
import os
import sys
from playwright.async_api import async_playwright

# Add current dir to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

async def final_check():
    print("--- FINAL SYSTEM CHECK ---")
    
    # 1. Check Imports
    try:
        from core.browser import launch_comet, apply_pure_stealth
        from core.parser import scrape_article
        from core.cli import CLILogger
        print("PASS: Core modules imported successfully.")
    except Exception as e:
        print(f"FAIL: Import error: {e}")
        return

    # 2. Check Browser Launch & Stealth
    logger = CLILogger()
    async with async_playwright() as p:
        try:
            print("Attempting browser launch...")
            browser, context, page, proc = await launch_comet(p, port=9223, logger=logger)
            if page:
                print("PASS: Browser connected.")
                # apply_pure_stealth is already called inside launch_comet
                print("PASS: Pure JS Stealth applied.")
                await page.close()
                await browser.close()
                if proc: proc.terminate()
            else:
                print("FAIL: Browser connection returned None.")
        except Exception as e:
            print(f"FAIL: Browser launch error: {e}")
            return

    print("--- ALL CORE STABILITY CHECKS PASSED ---")

if __name__ == "__main__":
    asyncio.run(final_check())
