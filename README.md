# Codebase Explorer

Codebase Explorer is an intelligent codebase navigation and intelligence platform. It allows developers to ingest remote Git repositories and instantly gain insights through RAG-powered Q&A, automated architecture diagramming, code risk tracking, diff impact analysis, and multi-repo comparisons.

## Setup Instructions

### 1. Backend Setup

The backend is built with FastAPI, ChromaDB, and Tree-sitter.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Environment Variables**:
Create a `.env` file in the `backend` directory and add your Groq API key:
```env
GROQ_API_KEY=your_groq_api_key_here
```

**Running the Server**:
```bash
uvicorn main:app --port 8000 --reload
```

### 2. Frontend Setup

The frontend is a React application built with Vite and TailwindCSS.

```bash
cd frontend
npm install
npm run dev
```

The application will be available at `http://localhost:5173`.

---

## Architecture Overview

Codebase Explorer follows a decoupled client-server architecture:

1. **Ingestion Pipeline**: 
   - Uses `GitPython` to clone target repositories into temporary directories.
   - Leverages `tree-sitter` to parse code symbols (functions, classes, import dependencies) while ignoring boilerplate.
   - Extracts semantic blocks from Markdown/TXT files.
   - Uses `radon` for Python static analysis to flag functions with a Cyclomatic Complexity > 10.
2. **Vector Store**: 
   - Backed by local `ChromaDB`.
   - Stores both semantic embeddings (using standard dense embeddings) and BM25 inverted indices for keyword searches.
3. **LLM Generation**: 
   - Uses the `Groq` API (`llama-3.1-8b-instant`) for blazing-fast inference.
   - Features dedicated prompts for Architecture synthesis, Diff analysis, and Comparative repo explanations.
4. **React Dashboard**: 
   - A dark-mode Tailwind UI that visualizes the graph data (via Mermaid.js) and streams markdown output for guides and Q&A.

---

## Design Decisions

*(Please fill out these placeholders with your specific architectural rationale)*

### Chunking Strategy
> *[TODO: Describe how source code files are split (e.g. by AST node, token count, or line length), how symbols are preserved in metadata, and how docstrings are handled.]*

### Hybrid Retrieval Methodology
> *[TODO: Detail the combination of ChromaDB vector search and BM25 keyword search. Explain the use of Reciprocal Rank Fusion (RRF) and why the constant k=60 was chosen.]*

### Eval Methodology
> *[TODO: Explain how the `/eval/run_eval.py` script benchmarks the retrieval precision. Discuss how the manually curated test set compares against the hybrid pipeline's top-k results and latency tracking.]*

### Multi-Repo Isolation
> *[TODO: Describe how chunks from different repositories/branches are safely isolated within a single ChromaDB collection using metadata filtering.]*
