
import sys
import os

# Emulate scraper.py path logic
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from playwright_stealth.stealth import Stealth
    print("SUCCESS: Imported Stealth from playwright_stealth.stealth")
    s = Stealth()
    print("SUCCESS: Created Stealth instance")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    from playwright_stealth import Stealth
    print("SUCCESS: Imported Stealth from playwright_stealth")
except Exception as e:
    print(f"FAILED: {e}")
