import subprocess
import sys
import os

def run_tests():
    print("==========================================")
    print("   PERPLEXITY SCRAPER - GLOBAL TEST SUITE")
    print("==========================================\n")
    
    # 1. Run Logic and Date Tests
    print("[1/2] Running Logic and Time Tests...")
    result1 = subprocess.run([sys.executable, "-m", "pytest", "tests/test_logic.py", "tests/test_time_logic.py"], capture_output=False)
    
    if result1.returncode == 0:
        print("\n[SUCCESS] All logic tests passed.\n")
    else:
        print("\n[FAILURE] Some logic tests failed.\n")
        sys.exit(1)

    print("==========================================")
    print("   ALL TESTS PASSED (EXIT CODE 0)")
    print("==========================================")
    sys.exit(0)

if __name__ == "__main__":
    run_tests()
