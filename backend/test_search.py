import subprocess
import time
import requests
import json

proc = subprocess.Popen(["uvicorn", "main:app", "--port", "8008"])

for i in range(15):
    try:
        if requests.get("http://127.0.0.1:8008/").status_code == 200:
            break
    except:
        time.sleep(1)

try:
    print("Ingesting to build BM25 index...")
    requests.post("http://127.0.0.1:8008/ingest", json={"repo_url_or_path": "https://github.com/psf/requests-html"})

    print("Searching for exact keyword: '_make_request'")
    resp = requests.post("http://127.0.0.1:8008/search", json={
        "query": "_make_request",
        "repo_url_or_path": "https://github.com/psf/requests-html",
        "limit": 3
    })
    print(json.dumps(resp.json(), indent=2)[:500] + "...\n")
    
    print("Searching for semantic concept: 'render javascript'")
    resp = requests.post("http://127.0.0.1:8008/search", json={
        "query": "render javascript",
        "repo_url_or_path": "https://github.com/psf/requests-html",
        "limit": 3
    })
    print(json.dumps(resp.json(), indent=2)[:500] + "...")
finally:
    proc.terminate()
    proc.wait()
