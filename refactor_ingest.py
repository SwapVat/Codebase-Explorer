import re
import os

# 1. Update pipeline.py
with open("backend/ingestion/pipeline.py", "r") as f:
    content = f.read()

# Replace process_repo with process_repo_batched
# Also add depth=1 to git clone

new_pipeline = content.replace("def process_repo(self, path_or_url: str, branch: str = None) -> tuple[list[Chunk], list[dict]]:", 
"def process_repo_batched(self, path_or_url: str, branch: str = None, batch_size: int = 50):")

new_pipeline = new_pipeline.replace("Repo.clone_from(path_or_url, temp_dir, branch=branch)", "Repo.clone_from(path_or_url, temp_dir, branch=branch, depth=1)")
new_pipeline = new_pipeline.replace("Repo.clone_from(path_or_url, temp_dir)", "Repo.clone_from(path_or_url, temp_dir, depth=1)")

# Replace the chunks/smells accumulation with yield
new_pipeline = new_pipeline.replace("        chunks = []\n        smells = []", "        chunks_batch = []\n        smells_batch = []\n        file_count = 0")

new_pipeline = new_pipeline.replace("chunks.extend(", "chunks_batch.extend(")
new_pipeline = new_pipeline.replace("smells.append(", "smells_batch.append(")

# Add yield logic at the end of file loop
loop_replacement = """
                file_count += 1
                if file_count >= batch_size:
                    yield chunks_batch, smells_batch
                    chunks_batch = []
                    smells_batch = []
                    file_count = 0

        if chunks_batch or smells_batch:
            yield chunks_batch, smells_batch"""

new_pipeline = new_pipeline.replace("""
        # Cleanup if cloned""", loop_replacement + "\n\n        # Cleanup if cloned")

new_pipeline = new_pipeline.replace("        return chunks, smells\n", "")

with open("backend/ingestion/pipeline.py", "w") as f:
    f.write(new_pipeline)

