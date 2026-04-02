import os
import sys

# Force the parent directory (project root) into the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import subprocess

from datetime import datetime, timezone
from utils.text_processor import parse_any_date

def test_parse_logic_strict():
    now = datetime.now(timezone.utc)
    
    # Test '14m ago'
    d = parse_any_date("14m ago")
    diff = (now - d).total_seconds()
    assert 13.5 * 60 < diff < 14.5 * 60
    
    # Test '2h ago'
    d = parse_any_date("2h ago")
    diff = (now - d).total_seconds()
    assert 1.9 * 3600 < diff < 2.1 * 3600
    
    # Test absolute 'Mar 25, 2026'
    d = parse_any_date("Mar 25, 2026")
    assert d.year == 2026
    assert d.month == 3
    assert d.day == 25

if __name__ == "__main__":
    print("Running Global Logic Tests...")
    # Run all tests in the tests directory to ensure full coverage
    tests_dir = os.path.dirname(__file__)
    result = subprocess.run([sys.executable, "-m", "pytest", tests_dir], capture_output=False)
    sys.exit(result.returncode)
