import os
from openai import OpenAI
from typing import List, Dict, Any

class RAGGenerator:
    def __init__(self):
        # Initialize OpenAI client to point to Groq
        api_key = os.getenv("GROQ_API_KEY")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        ) if api_key else None

    def generate_answer(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        if not self.client:
            return "Error: GROQ_API_KEY is not set in the environment variables."
            
        # Format the context
        context_parts = []
        for i, chunk in enumerate(chunks):
            # chunks contain: id, content, metadata, rrf_score
            file_path = chunk.get("metadata", {}).get("file_path", "unknown")
            lines = f"Lines {chunk.get('metadata', {}).get('start_line', '?')}-{chunk.get('metadata', {}).get('end_line', '?')}"
            content = chunk.get('content', '')
            if len(content) > 1000:
                content = content[:1000] + "\n...[truncated]..."
            context_parts.append(f"[{i+1}] {file_path} ({lines}):\n{content}\n")
            
        context_str = "\n".join(context_parts)
        
        prompt = f"""You are a helpful coding assistant. 
Use the following context chunks to answer the user's question. 
If the answer is not contained within the context, simply say "I don't have enough information to answer that."
When you use information from a chunk, cite it using its bracketed number, e.g., [1] or [2].

Context:
{context_str}

Question:
{query}

Answer:"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating answer: {str(e)}"

    def build_onboarding_guide(self, repo_url_or_path: str, store):
        import hashlib
        repo_hash = hashlib.md5(repo_url_or_path.encode()).hexdigest()
        guide_path = os.path.join(store.data_dir, f"{repo_hash}_guide.md")
        
        # Mark as processing
        with open(guide_path, "w") as f:
            f.write("PROCESSING")
            
        prompts = [
            ("Project Structure Overview", "Provide a brief project structure overview and its purpose."),
            ("Key Entry Points", "What are the key entry points or main executable scripts?"),
            ("Main Modules", "Summarize the main modules and their responsibilities."),
            ("Data Flow", "Explain the primary data flow or architecture of the application.")
        ]
        
        guide_content = f"# Onboarding Guide: {repo_url_or_path}\n\n"
        
        for section_title, query in prompts:
            try:
                chunks = store.hybrid_search(
                    query_text=query,
                    repo_url_or_path=repo_url_or_path,
                    n_results=5
                )
                answer = self.generate_answer(query, chunks)
                guide_content += f"## {section_title}\n\n{answer}\n\n"
            except Exception as e:
                guide_content += f"## {section_title}\n\nError generating section: {str(e)}\n\n"
                
        # Save final guide
        with open(guide_path, "w") as f:
            f.write(guide_content)

    def explain_diff(self, diff_text: str, repo_url_or_path: str, store) -> str:
        import re
        # Extract additions and deletions from the diff to form a query
        lines = diff_text.split("\n")
        changed_code = []
        for line in lines:
            if line.startswith("+") and not line.startswith("+++"):
                changed_code.append(line[1:].strip())
            elif line.startswith("-") and not line.startswith("---"):
                changed_code.append(line[1:].strip())
                
        # Filter out empty lines or simple brackets
        keywords = [word for word in " ".join(changed_code).split() if len(word) > 3 and not word.startswith("//") and not word.startswith("#")]
        
        # Create a search query based on top keywords
        query = " ".join(list(dict.fromkeys(keywords))[:20]) # Take top 20 unique words
        if not query:
            query = "general code change"
            
        chunks = store.hybrid_search(
            query_text=query,
            repo_url_or_path=repo_url_or_path,
            n_results=5
        )
        
        context_text = ""
        for i, chunk in enumerate(chunks):
            content = chunk.get("content", "")
            meta = chunk.get("metadata", {})
            file_path = meta.get("file_path", "unknown")
            context_text += f"\n--- File: {file_path} ---\n{content}\n"
            
        prompt = f"""You are a senior software engineer reviewing a pull request or code diff.
        
Here is the git diff:
```diff
{diff_text}
```

Here is some surrounding context from the codebase retrieved via vector search:
```
{context_text}
```

Explain exactly what changed in plain English. Analyze the likely intent behind the change and its downstream impacts on the rest of the application. Keep it professional, structured, and easy to read.
"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a senior code reviewer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating explanation: {str(e)}"

    def compare_repos(self, query: str, repo_1: str, repo_2: str, store) -> str:
        # Retrieve from Repo 1
        chunks_1 = store.hybrid_search(
            query_text=query,
            repo_url_or_path=repo_1,
            n_results=3
        )
        
        # Retrieve from Repo 2
        chunks_2 = store.hybrid_search(
            query_text=query,
            repo_url_or_path=repo_2,
            n_results=3
        )
        
        context_1 = ""
        for i, chunk in enumerate(chunks_1):
            content = chunk.get('content', '')
            # Truncate content to roughly 800 characters to save tokens
            if len(content) > 800:
                content = content[:800] + "\n...[truncated]..."
            context_1 += f"[{i+1}] File: {chunk.get('metadata', {}).get('file_path')}\n{content}\n\n"
            
        context_2 = ""
        for i, chunk in enumerate(chunks_2):
            content = chunk.get('content', '')
            if len(content) > 800:
                content = content[:800] + "\n...[truncated]..."
            context_2 += f"[{i+1}] File: {chunk.get('metadata', {}).get('file_path')}\n{content}\n\n"

        prompt = f"""You are a senior software architect comparing two different codebases or branches.
        
A user asked: "{query}"

Here is relevant context extracted from Repository/Branch 1 ({repo_1}):
```
{context_1}
```

Here is relevant context extracted from Repository/Branch 2 ({repo_2}):
```
{context_2}
```

Compare and contrast the two codebases based on the user's question. Identify architectural differences, implementation choices, and how they approach the problem differently. Use clear headings and format your answer cleanly. Keep it professional, objective, and highlight specific code differences where applicable.
"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a senior codebase comparison tool."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error comparing repos: {str(e)}"

    def explain_smell(self, repo_url_or_path: str, smell_name: str, file_path: str, store) -> str:
        # Search for the function/class name in the specific file to get its full context
        query = f"{smell_name} in {file_path}"
        chunks = store.hybrid_search(
            query_text=query,
            repo_url_or_path=repo_url_or_path,
            n_results=3
        )
        
        context_text = ""
        for i, chunk in enumerate(chunks):
            if chunk.get('metadata', {}).get('file_path') == file_path:
                context_text += f"\n{chunk.get('content')}\n"
            
        if not context_text:
            context_text = "Could not retrieve the specific code block. Explain generally why high cyclomatic complexity is bad."
            
        prompt = f"""You are a senior code reviewer. Our static analysis tool flagged the following function/class '{smell_name}' in the file '{file_path}' as having dangerously high Cyclomatic Complexity.
        
Here is the retrieved code block:
```python
{context_text}
```

Explain exactly why this code is overly complex or risky. Identify the specific branching, nested loops, or large structures causing the smell. Suggest a concrete refactoring strategy to simplify the logic and lower the cyclomatic complexity.
"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a code refactoring expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating smell explanation: {str(e)}"
