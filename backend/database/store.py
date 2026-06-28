import os
import hashlib
import chromadb
import pickle
import re
from chromadb.utils import embedding_functions
from ingestion.models import Chunk
from rank_bm25 import BM25Okapi

class ChromaStore:
    def __init__(self, data_dir: str = "chroma_data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.data_dir)
        self._embedding_fn = None
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            # Setup the sentence-transformer embedding function lazily
            self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            # Get or create the main repos collection lazily
            self._collection = self.client.get_or_create_collection(
                name="repos",
                embedding_function=self._embedding_fn
            )
        return self._collection

    def _generate_id(self, repo_url: str, chunk: Chunk) -> str:
        # Create a stable ID based on repo, file path, and line numbers
        unique_str = f"{repo_url}::{chunk.file_path}::{chunk.start_line}::{chunk.end_line}"
        return hashlib.md5(unique_str.encode("utf-8")).hexdigest()

        def delete_repo(self, repo_url_or_path: str):
        try:
            self.collection.delete(where={"repo": repo_url_or_path})
        except Exception:
            pass

    def add_chunks(self, repo_url_or_path: str, chunks: list[Chunk]) -> int:
        if not chunks:
            return 0
        ids = []
        documents = []
        metadatas = []
        for chunk in chunks:
            ids.append(self._generate_id(repo_url_or_path, chunk))
            documents.append(chunk.content)
            meta = {
                "repo": repo_url_or_path,
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "chunk_type": chunk.chunk_type.value
            }
            if chunk.metadata:
                for k, v in chunk.metadata.items():
                    if v is not None:
                        meta[k] = str(v)
            metadatas.append(meta)

        BATCH_SIZE = 500
        for i in range(0, len(ids), BATCH_SIZE):
            self.collection.add(
                ids=ids[i:i+BATCH_SIZE],
                documents=documents[i:i+BATCH_SIZE],
                metadatas=metadatas[i:i+BATCH_SIZE]
            )
        return len(ids)

    def build_indices(self, repo_url_or_path: str, smells: list[dict] = None):
        import json
        import hashlib
        from rank_bm25 import BM25Okapi
        import pickle

        repo_hash = hashlib.md5(repo_url_or_path.encode()).hexdigest()
        
        if smells is not None:
            smells_path = os.path.join(self.data_dir, f"{repo_hash}_smells.json")
            with open(smells_path, "w") as f:
                json.dump(smells, f)
        
        # Get all documents for this repo to build BM25 and graph
        results = self.collection.get(where={"repo": repo_url_or_path})
        if not results or not results['ids']:
            return

        documents = results['documents']
        ids = results['ids']
        metadatas = results['metadatas']

        tokenized_corpus = [re.findall(r'\w+', doc.lower()) for doc in documents]
        bm25 = BM25Okapi(tokenized_corpus)
        bm25_data = {
            "bm25": bm25,
            "ids": ids,
            "documents": documents,
            "metadatas": metadatas
        }
        bm25_path = os.path.join(self.data_dir, f"{repo_hash}_bm25.pkl")
        with open(bm25_path, "wb") as f:
            pickle.dump(bm25_data, f)

        symbol_map = {}
        for meta in metadatas:
            name = meta.get("name")
            if name and name != "unknown":
                if name not in symbol_map:
                    symbol_map[name] = set()
                symbol_map[name].add(meta["file_path"])
                
        nodes = set()
        edges = []
        
        file_contents = {}
        for i, meta in enumerate(metadatas):
            fp = meta["file_path"]
            nodes.add(fp)
            if fp not in file_contents:
                file_contents[fp] = ""
            file_contents[fp] += "\n" + documents[i]
            
        for fp, content in file_contents.items():
            calls = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
            imports = re.findall(r'^import\s+([a-zA-Z0-9_\.]+)', content, re.MULTILINE)
            from_imports = re.findall(r'^from\s+([a-zA-Z0-9_\.]+)\s+import', content, re.MULTILINE)
            
            for call in calls:
                if call in symbol_map:
                    for target_fp in symbol_map[call]:
                        if target_fp != fp:
                            edges.append({"source": fp, "target": target_fp, "type": "call"})
                            
            for imp in imports + from_imports:
                target_fp = f"{imp.replace('.', '/')}.py"
                if target_fp in nodes and target_fp != fp:
                    edges.append({"source": fp, "target": target_fp, "type": "import"})
                    
        unique_edges = []
        seen = set()
        for e in edges:
            sig = f"{e['source']}->{e['target']}"
            if sig not in seen:
                seen.add(sig)
                unique_edges.append(e)

        graph_data = {
            "nodes": list(nodes),
            "edges": unique_edges
        }
        
        graph_path = os.path.join(self.data_dir, f"{repo_hash}_graph.json")
        with open(graph_path, "w") as f:
            json.dump(graph_data, f)


    def query_repo(self, query_text: str, repo_url_or_path: str = None, n_results: int = 5):
        where_clause = {"repo": repo_url_or_path} if repo_url_or_path else None
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_clause
        )
        return results

    def hybrid_search(self, query_text: str, repo_url_or_path: str, n_results: int = 5, k: int = 60):
        """
        Combines Vector Search (Chroma) and Keyword Search (BM25) using RRF.
        """
        # 1. Vector Search
        vector_results = self.query_repo(query_text, repo_url_or_path, n_results=20)
        vector_ranks = {}
        if vector_results and vector_results['ids'] and len(vector_results['ids']) > 0:
            for rank, doc_id in enumerate(vector_results['ids'][0]):
                vector_ranks[doc_id] = rank + 1

        # 2. BM25 Search
        bm25_ranks = {}
        repo_hash = hashlib.md5(repo_url_or_path.encode()).hexdigest()
        bm25_path = os.path.join(self.data_dir, f"{repo_hash}_bm25.pkl")
        
        bm25_data = None
        if os.path.exists(bm25_path):
            with open(bm25_path, "rb") as f:
                bm25_data = pickle.load(f)
                
        if bm25_data:
            bm25 = bm25_data["bm25"]
            tokenized_query = re.findall(r'\w+', query_text.lower())
            scores = bm25.get_scores(tokenized_query)
            
            # Sort scores
            scored_docs = list(zip(bm25_data["ids"], scores))
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            
            # Take top 20 non-zero
            for rank, (doc_id, score) in enumerate(scored_docs[:20]):
                if score > 0:
                    bm25_ranks[doc_id] = rank + 1
                    
        # 3. Reciprocal Rank Fusion (RRF)
        all_ids = set(vector_ranks.keys()).union(set(bm25_ranks.keys()))
        rrf_scores = {}
        for doc_id in all_ids:
            v_rank = vector_ranks.get(doc_id, 1000)
            b_rank = bm25_ranks.get(doc_id, 1000)
            
            score = 0
            if v_rank < 1000:
                score += 1.0 / (k + v_rank)
            if b_rank < 1000:
                score += 1.0 / (k + b_rank)
                
            rrf_scores[doc_id] = score
            
        # 4. Sort and return
        sorted_ids = sorted(rrf_scores.keys(), key=lambda doc_id: rrf_scores[doc_id], reverse=True)[:n_results]
        
        final_results = []
        if bm25_data:
            id_to_idx = {doc_id: i for i, doc_id in enumerate(bm25_data["ids"])}
            for doc_id in sorted_ids:
                idx = id_to_idx.get(doc_id)
                if idx is not None:
                    final_results.append({
                        "id": doc_id,
                        "content": bm25_data["documents"][idx],
                        "metadata": bm25_data["metadatas"][idx],
                        "rrf_score": rrf_scores[doc_id]
                    })
        return final_results
