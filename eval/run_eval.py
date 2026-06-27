import json
import time
import requests
import os

DATASET_FILE = "dataset.json"
RESULTS_FILE = "../backend/eval_results.json"
ASK_ENDPOINT = "http://127.0.0.1:8020/ask"
REPO_URL = "https://github.com/psf/requests-html"

def run_evaluation():
    with open(DATASET_FILE, "r") as f:
        dataset = json.load(f)

    results = []
    print(f"Starting evaluation of {len(dataset)} questions...")

    for i, item in enumerate(dataset):
        question = item["question"]
        expected_file = item["expected_file_path"]
        
        payload = {
            "query": question,
            "repo_url_or_path": REPO_URL,
            "limit": 5
        }

        print(f"[{i+1}/{len(dataset)}] Asking: {question}")
        start_time = time.time()
        
        try:
            resp = requests.post(ASK_ENDPOINT, json=payload, timeout=60)
            latency = time.time() - start_time
            
            if resp.status_code == 200:
                data = resp.json()
                answer = data.get("answer", "")
                citations = data.get("citations", [])
                
                # Check for hit
                retrieved_files = [c.get("metadata", {}).get("file_path", "") for c in citations]
                is_hit = expected_file in retrieved_files
                
                results.append({
                    "question": question,
                    "expected_file": expected_file,
                    "answer": answer,
                    "latency_sec": round(latency, 2),
                    "is_hit": is_hit,
                    "retrieved_files": list(set(retrieved_files))
                })
            else:
                print(f"Error {resp.status_code}: {resp.text}")
                results.append({
                    "question": question,
                    "expected_file": expected_file,
                    "answer": f"Error: {resp.status_code}",
                    "latency_sec": round(latency, 2),
                    "is_hit": False,
                    "retrieved_files": []
                })
                
        except Exception as e:
            latency = time.time() - start_time
            print(f"Exception: {str(e)}")
            results.append({
                "question": question,
                "expected_file": expected_file,
                "answer": f"Exception: {str(e)}",
                "latency_sec": round(latency, 2),
                "is_hit": False,
                "retrieved_files": []
            })
            
    # Save results
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"Evaluation complete. Saved to {RESULTS_FILE}")

if __name__ == "__main__":
    run_evaluation()
