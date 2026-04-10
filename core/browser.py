import os
import json
import asyncio
import subprocess
from playwright_stealth import Stealth
from playwright.async_api import Error as PlaywrightError

user_home = os.path.expanduser("~")
DEFAULT_COMET_PATH = os.path.join(user_home, "AppData", "Local", "Perplexity", "Comet", "Application", "comet.exe")
COMET_LNK = r"C:\Users\Acarvi\Desktop\Comet.lnk"
CONFIG_FILE = os.path.join(os.getcwd(), "config.json")
USER_DATA_DIR = os.path.join(os.getcwd(), "user_data")

def open_url_in_comet(url, logger=None):
    """
    Deprecated: Using internal Playwright tabs for stability.
    """
    if logger:
        logger.info(f"Opening internal tab for: {url}")

async def launch_comet(p, port=9222, headless=False, logger=None):
    browser_running = None
    discover_url = "https://www.perplexity.ai/discover"
    
    logger.info(f"Connecting to Comet via Shared Session (Port {port})...")
    
    # 1. Try to connect first
    try:
        browser_running = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}", timeout=3000)
        logger.success("Connected to active Comet session.")
    except Exception:
        logger.info("No active session. Launching Comet via system shortcut...")
        try:
            # USANDO LA TECLA: Lanzamos Comet usando el acceso directo y le pasamos la URL de Discover
            cmd = r'cmd /c start "" "C:\Users\Acarvi\Desktop\Comet.lnk" "https://www.perplexity.ai/discover"'
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            await asyncio.sleep(5)
            browser_running = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}", timeout=15000)
            logger.success("Comet launched and connected via CDP.")
        except Exception as e:
            logger.error(f"Failed to launch Comet: {e}")
            return None, None, None, None

    # 2. Scraper Isolation
    try:
        context = browser_running.contexts[0]
        stealth = Stealth()
        
        async def abort_route(route):
            try: await route.abort()
            except: pass

        async def setup_page(page):
            try:
                if page.is_closed(): return
                await stealth.apply_stealth_async(page)
                await page.set_extra_http_headers({
                    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
                    "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                    "Sec-Ch-Ua-Mobile": "?0",
                    "Sec-Ch-Ua-Platform": '"Windows"',
                })
                # Performance optimization (skip images/css)
                await page.route("**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2,ttf,otf,ico,css,mp4,webm}", abort_route)
            except: pass

        # Open a new tab for the scraper
        page = await context.new_page()
        await setup_page(page)
        
        logger.info(f"Navigating to {discover_url}...")
        await page.goto(discover_url, wait_until="domcontentloaded", timeout=60000)
        
        context.on("page", setup_page)
        return browser_running, context, page, None
    except Exception as e:
        logger.error(f"Failed to setup context: {e}")
        return None, None, None, None


async def check_for_challenges(page, logger):
    try:
        title = await page.title()
        content = await page.content()
        if "Just a moment..." in title or "Verify you are human" in content or "cf-challenge" in content:
            logger.warning("Bot challenge detected. Please verify humanity in the browser.")
            while "Just a moment..." in title or "Verify you are human" in content:
                await asyncio.sleep(5)
                title = await page.title()
                content = await page.content()
    except: pass
