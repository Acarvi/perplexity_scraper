
import subprocess
import time
import os

def run_test():
    cmd = [r".\venv\Scripts\python.exe", "scraper.py"]
    # We'll use a pipe to send the input '1' for the mode
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    
    # Send '1\n' for the first prompt
    try:
        print("Sending input '1' to scraper...")
        process.stdin.write("1\n")
        process.stdin.flush()
        
        # Now wait and see what happens
        start_time = time.time()
        while time.time() - start_time < 30: # Wait up to 30 seconds
            line = process.stdout.readline()
            if not line:
                break
            print(f"OUT: {line.strip()}")
            if "Browser initialization failed" in line or "Traceback" in line:
                print("CRASH DETECTED!")
                break
            if "Successfully connected" in line:
                print("SUCCESS: Browser initialized!")
                break
        
        # Check stderr
        err = process.stderr.read()
        if err:
            print(f"ERR: {err}")
            
    finally:
        process.terminate()

if __name__ == "__main__":
    run_test()
