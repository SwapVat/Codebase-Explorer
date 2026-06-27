import subprocess
import time
import requests
import json
import os

# mock API key so that we don't crash, but it will return an error answer from generator if invalid.
os.environ["OPENAI_API_KEY"] = "sk-mock-key"

proc = subprocess.Popen(["uvicorn", "main:app", "--port", "8010"])

for i in range(15):
    try:
        if requests.get("http://127.0.0.1:8010/").status_code == 200:
            break
    except:
        time.sleep(1)

try:
    print("Testing /ask endpoint...")
    resp = requests.post("http://127.0.0.1:8010/ask", json={
        "query": "How does the BaseParser class work?",
        "repo_url_or_path": "https://github.com/psf/requests-html",
        "limit": 3
    })
    print("\n--- RESPONSE ---")
    data = resp.json()
    print("Answer:", data.get("answer"))
    print("\nCitations:")
    for i, c in enumerate(data.get("citations", [])):
        print(f"[{i+1}] {c['metadata']['file_path']} (Lines {c['metadata']['start_line']}-{c['metadata']['end_line']})")
finally:
    proc.terminate()
    proc.wait()
