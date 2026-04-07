import os
import json
import asyncio
import subprocess
from playwright_stealth import Stealth

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
    
    # 0. Rigorous Cleanup (Phase 6)
    # Ensure no other comet instances are fighting for the same user-data-dir or port
    # REMOVED: taskkill - As per Gold Rules, process management is handled via Playwright.
    try:
        await asyncio.sleep(1)
    except: pass

    # 1. Launch comet.exe directly
    logger.info(f"Launching Comet in Clean App-Mode (Port {port})...")
    
    comet_proc = None
    try:
        cmd = [
            DEFAULT_COMET_PATH,
            f"--app={discover_url}",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={USER_DATA_DIR}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-gpu",
            "--remote-allow-origins=*"
        ]
        comet_proc = subprocess.Popen(cmd)
        logger.info("Comet process spawned.")
    except Exception as e:
        logger.error(f"Failed to launch comet.exe: {e}")
        return None, None, None, None
        
    # 2. Retry loop for CDP connection (5 attempts - More Aggressive)
    for attempt in range(1, 6):
        wait_time = 3 + attempt # Progressive wait
        logger.info(f"Connection attempt {attempt}/5 (Waiting {wait_time}s for port {port})...")
        await asyncio.sleep(wait_time)
        
        try:
            # Use localhost instead of 127.0.0.1 for potential IPv6/v4 resolution issues
            browser_running = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}", timeout=15000)
            logger.success("Successfully connected to Comet via CDP.")
            
            # Ensure we have at least one page
            context = browser_running.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            # Application-level stealth
            stealth = Stealth()
            await stealth.apply_stealth_async(page)
            
            # Strict resource blocking for performance
            await page.route("**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2,ttf,otf,ico,css,mp4,webm}", lambda route: route.abort())
            
            return browser_running, context, page, comet_proc
        except Exception as e:
            if attempt == 5:
                logger.error(f"CDP connection failed after {attempt} attempts: {e}")
                # Log actual network error for debugging
                try:
                    import urllib.request
                    urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1).read()
                except Exception as net_err:
                    logger.error(f"Network Check Failed: {net_err}")
            else:
                logger.warning(f"Attempt {attempt} failed, retrying...")
                
    return None, None, None, comet_proc

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
