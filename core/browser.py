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

def open_url_in_comet(url):
    """
    Opens a URL in a new tab of the existing Comet session using the 'Magic Command'.
    Mandatory per skill_comet_navigation.md.
    """
    # Exact magic command from directive
    cmd = f'cmd /c start "" "{COMET_LNK}" "{url}"'
    os.system(cmd)

async def launch_comet(p, port=9222, headless=False, logger=None):
    browser_running = None
    discover_url = "https://www.perplexity.ai/discover"
    try:
        # Try to connect to existing instance on port 9222
        browser_running = await p.chromium.connect_over_cdp(f"http://localhost:{port}", timeout=5000)
        logger.info("Connected to existing Comet session via CDP.")
        context = browser_running.contexts[0]
        # Force navigation to Discover in the current context if needed, or open new tab via Magic Command
        page = context.pages[0] if context.pages else await context.new_page()
        return browser_running, context, page
    except Exception:
        # Restoration of Comet App-Mode: Launch specifically in clean window
        logger.info(f"Comet not detected. Launching in App-Mode: {discover_url}")
        
        # Launch comet.exe directly with provided clean UX flags
        try:
            cmd = [
                DEFAULT_COMET_PATH,
                f"--app={discover_url}", # CLEAN UX BOX
                f"--remote-debugging-port={port}",
                f"--user-data-dir={USER_DATA_DIR}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-gpu"
            ]
            subprocess.Popen(cmd)
        except Exception as e:
            logger.error(f"Failed to launch comet.exe: {e}")
            return None, None, None
            
        # Give it time to initialize and open the port
        await asyncio.sleep(8)
        
        try:
            browser_running = await p.chromium.connect_over_cdp(f"http://localhost:{port}", timeout=20000)
            logger.info("Successfully connected to App-Mode session via CDP.")
            context = browser_running.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            stealth = Stealth()
            await stealth.apply_stealth_async(page)
            
            # Strict resource blocking
            await page.route("**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2,ttf,otf,ico,css,mp4,webm}", lambda route: route.abort())
            
            return browser_running, context, page
        except Exception as e:
            logger.error(f"CDP connection failed after App-Mode Launch: {e}")
            return None, None, None

async def check_for_challenges(page, logger):
    title = await page.title()
    content = await page.content()
    if "Just a moment..." in title or "Verify you are human" in content or "cf-challenge" in content:
        logger.warning("Bot challenge detected. Please verify humanity in the browser.")
        while "Just a moment..." in title or "Verify you are human" in content:
            await asyncio.sleep(5)
            title = await page.title()
            content = await page.content()
