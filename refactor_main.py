with open("backend/main.py", "r") as f:
    content = f.read()

replacement = """@app.post("/ingest", response_model=IngestResponse)
def ingest_repo(request: IngestRequest, background_tasks: BackgroundTasks):
    pipeline = IngestionPipeline()
    store = ChromaStore()
    import gc
    try:
        store.delete_repo(request.repo_url_or_path)
        
        indexed_count = 0
        all_smells = []
        
        for chunks_batch, smells_batch in pipeline.process_repo_batched(request.repo_url_or_path, request.branch, batch_size=50):
            count = store.add_chunks(request.repo_url_or_path, chunks_batch)
            indexed_count += count
            all_smells.extend(smells_batch)
            
            del chunks_batch
            del smells_batch
            gc.collect()
            
        store.build_indices(request.repo_url_or_path, all_smells)
        
        # trigger guide generation in background
        from generation import RAGGenerator
        generator = RAGGenerator()
        background_tasks.add_task(generator.build_onboarding_guide, request.repo_url_or_path, store)
        
        return IngestResponse(status="success", chunks_indexed=indexed_count)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))"""

import re
start_idx = content.find("@app.post(\"/ingest\", response_model=IngestResponse)")
end_idx = content.find("@app.post(\"/explain-diff\")")

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + replacement + "\n\n" + content[end_idx:]
    with open("backend/main.py", "w") as f:
        f.write(new_content)
else:
    print("Could not find boundaries")

