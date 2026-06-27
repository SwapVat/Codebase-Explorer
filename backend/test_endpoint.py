import subprocess
import time
import requests
import json

proc = subprocess.Popen(["uvicorn", "main:app", "--port", "8002"])
time.sleep(2)

try:
    print("Sending request...")
    resp = requests.post("http://127.0.0.1:8002/ingest", json={"repo_url_or_path": "https://github.com/psf/requests-html"})
    
    if resp.status_code != 200:
        print(f"Error {resp.status_code}: {resp.text}")
    else:
        data = resp.json()
        print(f"\nTotal chunks returned: {len(data)}")
        
        code_samples = [c for c in data if c['chunk_type'] == 'code'][:2]
        doc_samples = [c for c in data if c['chunk_type'] == 'doc'][:2]
        
        print("\n--- CODE SAMPLE 1 ---")
        if code_samples:
            print(json.dumps(code_samples[0], indent=2))
            
        print("\n--- CODE SAMPLE 2 ---")
        if len(code_samples) > 1:
            print(json.dumps(code_samples[1], indent=2))
            
        print("\n--- DOC SAMPLE 1 ---")
        if doc_samples:
            print(json.dumps(doc_samples[0], indent=2))
            
        print("\n--- DOC SAMPLE 2 ---")
        if len(doc_samples) > 1:
            print(json.dumps(doc_samples[1], indent=2))
            
finally:
    proc.terminate()
    proc.wait()
