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
USER_DATA_SCRAPER = os.path.join(os.getcwd(), "user_data_scraper")

async def is_comet_running():
    try:
        output = subprocess.check_output('tasklist /FI "IMAGENAME eq comet.exe" /NH', shell=True).decode('utf-8', 'ignore')
        return "comet.exe" in output.lower()
    except:
        return False

async def launch_comet(p, port=9222, headless=False, logger=None):
    browser_running = None
    browser_context = None
    discover_url = "https://www.perplexity.ai/discover"
    
    logger.info(f"Connecting to Comet via Shared Session (Port {port})...")
    
    # 1. Try Shared Session connection (Preferred)
    try:
        browser_running = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}", timeout=3000)
        browser_context = browser_running.contexts[0]
        logger.success("Connected to active Comet session.")
    except Exception:
        # Check if already running but refused connection (locked)
        if await is_comet_running():
            logger.warning("Main Comet is open but 'locked' (no debugging port).")
            logger.info("Entering Parallel Mode: Launching a dedicated scraper window...")
            try:
                # OPTION C: Isolated Parallel Launch (Subprocess + CDP)
                cmd = [
                    DEFAULT_COMET_PATH,
                    "--remote-debugging-port=9223",
                    f"--user-data-dir={USER_DATA_SCRAPER}",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--restore-last-session",
                    "about:blank"
                ]
                comet_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                await asyncio.sleep(5)
                browser_running = await p.chromium.connect_over_cdp("http://127.0.0.1:9223", timeout=15000)
                browser_context = browser_running.contexts[0]
                
                logger.success("Dedicated Scraper Window launched (Parallel Mode).")
            except Exception as e:
                logger.error(f"Failed to launch parallel window: {e}")
                return None, None, None, None
        else:
            # Not running, launch standard persistent session via Subprocess
            logger.info("Launching Comet with debugging port enabled...")
            try:
                cmd = [
                    DEFAULT_COMET_PATH,
                    f"--remote-debugging-port={port}",
                    f"--user-data-dir={USER_DATA_SCRAPER}",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--restore-last-session",
                    "about:blank"
                ]
                comet_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                await asyncio.sleep(5)
                browser_running = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}", timeout=15000)
                browser_context = browser_running.contexts[0]
                logger.success("Comet launched successfully.")
            except Exception as e:
                logger.error(f"Failed to launch Comet: {e}")
                return None, None, None, None

    # 2. Scraper Isolation & Setup
    try:
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

        # Get/Create the page for the scraper
        page = browser_context.pages[0] if browser_context.pages else await browser_context.new_page()
        await setup_page(page)
        
        logger.info(f"Navigating to {discover_url}...")
        await page.goto(discover_url, wait_until="domcontentloaded", timeout=60000)
        
        browser_context.on("page", setup_page)
        return browser_running, browser_context, page, comet_proc
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
