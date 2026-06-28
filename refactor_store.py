with open("backend/database/store.py", "r") as f:
    content = f.read()

import re

# We will replace the entire refresh_repo method.
# We need to extract the parts and create delete_repo, add_chunks, build_indices

replacement = """    def delete_repo(self, repo_url_or_path: str):
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

        tokenized_corpus = [re.findall(r'\\w+', doc.lower()) for doc in documents]
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
            file_contents[fp] += "\\n" + documents[i]
            
        for fp, content in file_contents.items():
            calls = re.findall(r'\\b([a-zA-Z_][a-zA-Z0-9_]*)\\s*\\(', content)
            imports = re.findall(r'^import\\s+([a-zA-Z0-9_\\.]+)', content, re.MULTILINE)
            from_imports = re.findall(r'^from\\s+([a-zA-Z0-9_\\.]+)\\s+import', content, re.MULTILINE)
            
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
"""

# We need to find the start and end of refresh_repo
# start: def refresh_repo(
# end: return len(ids)

start_idx = content.find("def refresh_repo(")
end_idx = content.find("return len(ids)", start_idx) + len("return len(ids)")

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + replacement + content[end_idx:]
    with open("backend/database/store.py", "w") as f:
        f.write(new_content)
else:
    print("Could not find refresh_repo")

