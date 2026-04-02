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
    
    # Pre-check if port 9222 is already open
    try:
        browser_running = await p.chromium.connect_over_cdp(f"http://localhost:{port}", timeout=5000)
        logger.success("Connected to existing Comet session via CDP.")
        context = browser_running.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        return browser_running, context, page
    except Exception:
        logger.info(f"Comet not detected on port {port}. Launching in App-Mode...")
        
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
            logger.info("Comet process started. Waiting for initialization...")
        except Exception as e:
            logger.error(f"Failed to launch comet.exe: {e}")
            return None, None, None
            
        # Retry loop for CDP connection (3 attempts)
        for attempt in range(1, 4):
            wait_time = 5 + (attempt * 3) # Jittered wait
            logger.info(f"Connection attempt {attempt}/3 (Waiting {wait_time}s for port {port})...")
            await asyncio.sleep(wait_time)
            
            try:
                browser_running = await p.chromium.connect_over_cdp(f"http://localhost:{port}", timeout=15000)
                logger.success("Successfully connected to App-Mode session via CDP.")
                context = browser_running.contexts[0]
                page = context.pages[0] if context.pages else await context.new_page()
                
                stealth = Stealth()
                await stealth.apply_stealth_async(page)
                
                # Strict resource blocking
                await page.route("**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2,ttf,otf,ico,css,mp4,webm}", lambda route: route.abort())
                
                return browser_running, context, page
            except Exception as e:
                if attempt == 3:
                    logger.error(f"CDP connection failed after {attempt} attempts: {e}")
                else:
                    logger.warning(f"Attempt {attempt} failed, retrying...")
                    
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
