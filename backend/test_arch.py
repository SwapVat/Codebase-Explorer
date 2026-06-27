import subprocess
import time
import requests

proc = subprocess.Popen([".venv/bin/python3", "-m", "uvicorn", "main:app", "--port", "8026"])

for i in range(15):
    try:
        if requests.get("http://127.0.0.1:8026/").status_code == 200:
            break
    except:
        time.sleep(1)

try:
    print("Sending POST /ingest ...")
    resp = requests.post("http://127.0.0.1:8026/ingest", json={"repo_url_or_path": "https://github.com/psf/requests-html"})
    print("Ingest returned:", resp.json())
    
    # Wait a second for graph saving (it's synchronous inside store.py before returning, so it should be there)
    resp2 = requests.get("http://127.0.0.1:8026/architecture-diagram?repo_url_or_path=https://github.com/psf/requests-html")
    data = resp2.json()
    print("Diagram status:", data.get("status"))
    graph = data.get("graph")
    if graph:
        print(f"Nodes: {len(graph.get('nodes', []))}, Edges: {len(graph.get('edges', []))}")
finally:
    proc.terminate()
    proc.wait()
