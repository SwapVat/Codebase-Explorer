import os
import shutil
import tempfile
from pathlib import Path
from git import Repo
from .models import Chunk
from .parsers import CodeParser, DocParser
import radon.complexity as radon_cc

class IngestionPipeline:
    def __init__(self):
        self.code_parser = CodeParser()
        self.doc_parser = DocParser()
        self.ignore_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__", "build", "dist"}
        self.doc_extensions = {".md", ".txt", ".rst"}
        self.code_extensions = {".py", ".js", ".ts", ".tsx"}

    def process_repo_batched(self, path_or_url: str, branch: str = None, batch_size: int = 50):
        temp_dir = None
        target_path = path_or_url

        # Check if URL
        if path_or_url.startswith("http://") or path_or_url.startswith("https://") or path_or_url.startswith("git@"):
            temp_dir = tempfile.mkdtemp()
            print(f"Cloning {path_or_url} into {temp_dir} on branch {branch}")
            if branch:
                Repo.clone_from(path_or_url, temp_dir, branch=branch, depth=1)
            else:
                Repo.clone_from(path_or_url, temp_dir, depth=1)
            target_path = temp_dir
        
        target_path = Path(target_path).resolve()
        
        if not target_path.exists() or not target_path.is_dir():
            raise ValueError(f"Invalid path or repository could not be cloned: {target_path}")

        chunks_batch = []
        smells_batch = []
        file_count = 0

        for root, dirs, files in os.walk(target_path):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            for file in files:
                file_path = Path(root) / file
                ext = file_path.suffix.lower()
                
                # relative path for chunk metadata
                rel_path = str(file_path.relative_to(target_path))
                
                if ext in self.doc_extensions:
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        chunks_batch.extend(self.doc_parser.parse(rel_path, content))
                    except Exception as e:
                        print(f"Error parsing doc {rel_path}: {e}")
                
                elif ext in self.code_extensions:
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        chunks_batch.extend(self.code_parser.parse(rel_path, content))
                        
                        # Radon static analysis for Python files
                        if ext == ".py":
                            try:
                                results = radon_cc.cc_visit(content)
                                for block in results:
                                    if block.complexity > 10:
                                        smells_batch.append({
                                            "file_path": rel_path,
                                            "name": block.name,
                                            "type": type(block).__name__,
                                            "complexity": block.complexity,
                                            "start_line": block.lineno,
                                            "end_line": getattr(block, 'endline', block.lineno)
                                        })
                            except Exception as e:
                                print(f"Error running radon on {rel_path}: {e}")
                    except Exception as e:
                        print(f"Error parsing code {rel_path}: {e}")

                file_count += 1
                if file_count >= batch_size:
                    yield chunks_batch, smells_batch
                    chunks_batch = []
                    smells_batch = []
                    file_count = 0

        if chunks_batch or smells_batch:
            yield chunks_batch, smells_batch

        # Cleanup if cloned
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

