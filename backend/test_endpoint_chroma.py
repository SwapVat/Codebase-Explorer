import subprocess
import time
import requests

proc = subprocess.Popen(["uvicorn", "main:app", "--port", "8006"])

for i in range(15):
    try:
        resp = requests.get("http://127.0.0.1:8006/")
        if resp.status_code == 200:
            break
    except:
        pass
    time.sleep(1)

try:
    print("Calling /ingest endpoint for requests-html...")
    resp = requests.post("http://127.0.0.1:8006/ingest", json={"repo_url_or_path": "https://github.com/psf/requests-html"})
    if resp.status_code == 200:
        print("Success:", resp.json())
    else:
        print("Error:", resp.status_code, resp.text)
finally:
    proc.terminate()
    proc.wait()
