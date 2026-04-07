
import asyncio
import sys
import os

# Emulate the environment
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from scraper import run_scraper
from unittest.mock import patch

async def test_run():
    # Mock input to select mode 1 (Last 24 hours) automatically
    with patch('builtins.input', return_value='1'):
        try:
            await run_scraper()
        except Exception as e:
            print(f"CRASH DETECTED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_run())
