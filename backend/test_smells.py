import subprocess
import time
import requests

proc = subprocess.Popen([".venv/bin/python3", "-m", "uvicorn", "main:app", "--port", "8028"])

for i in range(15):
    try:
        if requests.get("http://127.0.0.1:8028/").status_code == 200:
            break
    except:
        time.sleep(1)

try:
    print("Sending POST /ingest ...")
    resp = requests.post("http://127.0.0.1:8028/ingest", json={"repo_url_or_path": "https://github.com/psf/requests-html"})
    print("Ingest returned:", resp.json())
    
    # Wait a second and check smells
    time.sleep(1)
    resp2 = requests.get("http://127.0.0.1:8028/code-smells?repo_url_or_path=https://github.com/psf/requests-html")
    data = resp2.json()
    print("Smells status:", data.get("status"))
    smells = data.get("smells", [])
    print(f"Total smells found: {len(smells)}")
    if smells:
        print("First smell:", smells[0])
finally:
    proc.terminate()
    proc.wait()
