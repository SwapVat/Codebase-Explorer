import subprocess
import time
import requests

proc = subprocess.Popen([".venv/bin/python3", "-m", "uvicorn", "main:app", "--port", "8025"])

for i in range(15):
    try:
        if requests.get("http://127.0.0.1:8025/").status_code == 200:
            break
    except:
        time.sleep(1)

try:
    print("Sending POST /ingest ...")
    resp = requests.post("http://127.0.0.1:8025/ingest", json={"repo_url_or_path": "https://github.com/psf/requests-html"})
    print("Ingest returned:", resp.json())
    
    print("Polling /onboarding-guide every 5 seconds...")
    for _ in range(12): # Wait up to 60 seconds
        time.sleep(5)
        resp2 = requests.get("http://127.0.0.1:8025/onboarding-guide?repo_url_or_path=https://github.com/psf/requests-html")
        data = resp2.json()
        status = data.get("status")
        print(f"Status: {status}")
        if status == "ready":
            print("\n--- GENERATED GUIDE ---")
            print(data.get("markdown")[:500] + "...\n(truncated for brevity)")
            break
finally:
    proc.terminate()
    proc.wait()
