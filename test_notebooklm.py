import asyncio
import os
import sys
from playwright.async_api import async_playwright

# Add current dir to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.browser import launch_comet
from core.notebooklm import upload_to_notebooklm
from core.cli import CLILogger

async def test_upload():
    logger = CLILogger()
    async with async_playwright() as p:
        try:
            browser, context, page, proc = await launch_comet(p, headless=False, logger=logger)
            if not page:
                print("Failed to launch browser")
                return
            
            # Use a dummy markdown file
            test_file = "perplexity_discover_content.md"
            if not os.path.exists(test_file):
                with open(test_file, "w") as f:
                    f.write("# Test Content")
            
            success = await upload_to_notebooklm(context, os.path.abspath(test_file), logger)
            if success:
                print("SUCCESS: NotebookLM upload worked.")
            else:
                print("FAIL: NotebookLM upload failed.")
            
            await asyncio.sleep(10) # Let user see it
            await browser.close()
            if proc: proc.terminate()
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_upload())
