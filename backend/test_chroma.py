import os
from database.store import ChromaStore
from ingestion.pipeline import IngestionPipeline

print("Ingesting current folder...")
pipeline = IngestionPipeline()
chunks = pipeline.process_repo(".")
print(f"Found {len(chunks)} chunks.")

print("Refreshing ChromaDB...")
store = ChromaStore()
count = store.refresh_repo(".", chunks)
print(f"Inserted {count} chunks into ChromaDB.")

print("Querying ChromaDB for 'BaseModel'...")
results = store.query_repo("BaseModel", repo_url_or_path=".")
if results and results['documents']:
    for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
        print(f"\n--- MATCH: {meta['file_path']} ({meta['chunk_type']}) ---")
        print(doc[:100] + "...")
