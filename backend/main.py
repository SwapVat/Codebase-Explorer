import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Dict, Any
from ingestion.models import Chunk
from ingestion.pipeline import IngestionPipeline

from database.store import ChromaStore

load_dotenv()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="RepoMind Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IngestRequest(BaseModel):
    repo_url_or_path: str
    branch: str = None

class IngestResponse(BaseModel):
    status: str
    chunks_indexed: int

class SearchRequest(BaseModel):
    query: str
    repo_url_or_path: str
    limit: int = 5

class AskRequest(BaseModel):
    query: str
    repo_url_or_path: str
    limit: int = 5

class AskResponse(BaseModel):
    answer: str
    citations: List[dict]

class DiffRequest(BaseModel):
    repo_url_or_path: str
    diff_text: str

class CompareRequest(BaseModel):
    repo_url_1: str
    repo_url_2: str
    query: str

class SmellRequest(BaseModel):
    repo_url_or_path: str
    file_path: str
    smell_name: str

@app.get("/")
def read_root():
    return {"message": "Welcome to RepoMind API"}

@app.post("/ingest", response_model=IngestResponse)
def ingest_repo(request: IngestRequest, background_tasks: BackgroundTasks):
    pipeline = IngestionPipeline()
    store = ChromaStore()
    try:
        chunks, smells = pipeline.process_repo(request.repo_url_or_path, request.branch)
        indexed_count = store.refresh_repo(request.repo_url_or_path, chunks, smells)
        
        # trigger guide generation in background
        from generation import RAGGenerator
        generator = RAGGenerator()
        background_tasks.add_task(generator.build_onboarding_guide, request.repo_url_or_path, store)
        
        return IngestResponse(status="success", chunks_indexed=indexed_count)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/explain-diff")
def explain_diff(request: DiffRequest):
    from generation import RAGGenerator
    store = ChromaStore()
    generator = RAGGenerator()
    try:
        explanation = generator.explain_diff(request.diff_text, request.repo_url_or_path, store)
        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/compare-repos")
def compare_repos(request: CompareRequest):
    from generation import RAGGenerator
    store = ChromaStore()
    generator = RAGGenerator()
    try:
        comparison = generator.compare_repos(request.query, request.repo_url_1, request.repo_url_2, store)
        return {"comparison": comparison}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/code-smells")
def get_code_smells(repo_url_or_path: str):
    import hashlib
    import json
    store = ChromaStore()
    repo_hash = hashlib.md5(repo_url_or_path.encode()).hexdigest()
    smells_path = os.path.join(store.data_dir, f"{repo_hash}_smells.json")
    
    if not os.path.exists(smells_path):
        return {"status": "not_found", "smells": []}
        
    with open(smells_path, "r") as f:
        smells_data = json.load(f)
        
    return {"status": "ready", "smells": smells_data}

@app.post("/explain-smell")
def explain_smell(request: SmellRequest):
    from generation import RAGGenerator
    store = ChromaStore()
    generator = RAGGenerator()
    try:
        explanation = generator.explain_smell(request.repo_url_or_path, request.smell_name, request.file_path, store)
        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/onboarding-guide")
def get_onboarding_guide(repo_url_or_path: str):
    import hashlib
    store = ChromaStore()
    repo_hash = hashlib.md5(repo_url_or_path.encode()).hexdigest()
    guide_path = os.path.join(store.data_dir, f"{repo_hash}_guide.md")
    
    if not os.path.exists(guide_path):
        return {"status": "not_found", "markdown": None}
        
    with open(guide_path, "r") as f:
        content = f.read()
        
    if content == "PROCESSING":
        return {"status": "processing", "markdown": None}
        
    return {"status": "ready", "markdown": content}

@app.get("/architecture-diagram")
def get_architecture_diagram(repo_url_or_path: str):
    import hashlib
    import json
    store = ChromaStore()
    repo_hash = hashlib.md5(repo_url_or_path.encode()).hexdigest()
    graph_path = os.path.join(store.data_dir, f"{repo_hash}_graph.json")
    
    if not os.path.exists(graph_path):
        return {"status": "not_found", "graph": None}
        
    with open(graph_path, "r") as f:
        graph_data = json.load(f)
        
    return {"status": "ready", "graph": graph_data}

@app.post("/search")
def search_repo(request: SearchRequest):
    store = ChromaStore()
    try:
        results = store.hybrid_search(
            query_text=request.query,
            repo_url_or_path=request.repo_url_or_path,
            n_results=request.limit
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

from generation import RAGGenerator

@app.post("/ask", response_model=AskResponse)
def ask_repo(request: AskRequest):
    store = ChromaStore()
    generator = RAGGenerator()
    try:
        chunks = store.hybrid_search(
            query_text=request.query,
            repo_url_or_path=request.repo_url_or_path,
            n_results=request.limit
        )
        answer = generator.generate_answer(request.query, chunks)
        return AskResponse(answer=answer, citations=chunks)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/eval/results")
def get_eval_results():
    import json
    import os
    results_path = os.path.join(os.path.dirname(__file__), "eval_results.json")
    if not os.path.exists(results_path):
        return {"error": "Evaluation has not been run yet."}
    with open(results_path, "r") as f:
        return json.load(f)




