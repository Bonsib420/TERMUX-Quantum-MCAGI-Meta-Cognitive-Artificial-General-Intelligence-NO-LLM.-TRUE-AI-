#!/usr/bin/env python3
import subprocess, time, requests, json, sys

# Start server
proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", "8000"],
                        cwd="../backend", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(4)

try:
    r = requests.post("http://localhost:8000/api/image/generate",
                      json={"prompt":"two black holes merging","width":800,"height":600,"refine":False},
                      timeout=30)
    print("Status:", r.status_code)
    if r.status_code == 200:
        d = r.json()
        size = len(d.get('image', ''))
        print(f"Image base64: {size:,} chars")
    else:
        print("Error:", r.text)
finally:
    proc.terminate()
    proc.wait(timeout=5)