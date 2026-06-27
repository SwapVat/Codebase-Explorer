import re
import tree_sitter
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript
from .models import Chunk, ChunkType

# Initialize language parsers
PYTHON_LANG = tree_sitter.Language(tree_sitter_python.language())
JS_LANG = tree_sitter.Language(tree_sitter_javascript.language())
TS_LANG = tree_sitter.Language(tree_sitter_typescript.language_typescript())

# Query definitions
PYTHON_QUERY = PYTHON_LANG.query("""
(function_definition) @func
(class_definition) @class
""")

JS_QUERY = JS_LANG.query("""
(function_declaration) @func
(method_definition) @method
(class_declaration) @class
""")

TS_QUERY = TS_LANG.query("""
(function_declaration) @func
(method_definition) @method
(class_declaration) @class
(interface_declaration) @interface
""")

class CodeParser:
    def __init__(self):
        self.parsers = {
            ".py": (PYTHON_LANG, PYTHON_QUERY),
            ".js": (JS_LANG, JS_QUERY),
            ".ts": (TS_LANG, TS_QUERY),
            ".tsx": (TS_LANG, TS_QUERY),
        }

    def parse(self, file_path: str, content: str) -> list[Chunk]:
        # Handle file extension
        ext = ""
        if "." in file_path:
            ext = "." + file_path.split(".")[-1]
            
        if ext not in self.parsers:
            return []

        lang, query = self.parsers[ext]
        parser = tree_sitter.Parser()
        parser.language = lang
        
        tree = parser.parse(bytes(content, "utf8"))
        captures = query.captures(tree.root_node)
        
        chunks = []
        for capture_name, nodes in captures.items():
            for node in nodes:
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                node_text = node.text.decode("utf8")
                
                # Try to extract the name
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode("utf8") if name_node else "unknown"

                chunks.append(Chunk(
                    file_path=file_path,
                    content=node_text,
                    start_line=start_line,
                    end_line=end_line,
                    chunk_type=ChunkType.CODE,
                    metadata={"name": name, "type": capture_name}
                ))
            
        return chunks

class DocParser:
    def parse(self, file_path: str, content: str) -> list[Chunk]:
        # Split by markdown headers or RST underlines
        lines = content.split("\n")
        chunks = []
        
        current_chunk_lines = []
        start_line = 1
        current_heading = "Top"
        
        for i, line in enumerate(lines):
            md_match = re.match(r"^#{1,6}\s+(.*)", line)
            rst_match = re.match(r"^([=\-~^\*_+])\1{3,}$", line.strip())
            
            if md_match:
                if any(l.strip() for l in current_chunk_lines):
                    chunks.append(Chunk(
                        file_path=file_path,
                        content="\n".join(current_chunk_lines),
                        start_line=start_line,
                        end_line=i,
                        chunk_type=ChunkType.DOC,
                        metadata={"heading": current_heading}
                    ))
                current_chunk_lines = [line]
                start_line = i + 1
                current_heading = md_match.group(1).strip()
            elif rst_match and len(current_chunk_lines) > 0 and current_chunk_lines[-1].strip() and len(line.strip()) >= len(current_chunk_lines[-1].strip()):
                # The previous line was the heading text
                heading_text = current_chunk_lines.pop().strip()
                
                if any(l.strip() for l in current_chunk_lines):
                    chunks.append(Chunk(
                        file_path=file_path,
                        content="\n".join(current_chunk_lines),
                        start_line=start_line,
                        end_line=i - 1,
                        chunk_type=ChunkType.DOC,
                        metadata={"heading": current_heading}
                    ))
                
                current_chunk_lines = [heading_text, line]
                start_line = i
                current_heading = heading_text
            else:
                current_chunk_lines.append(line)
                
        # Add last chunk
        if any(l.strip() for l in current_chunk_lines):
            chunks.append(Chunk(
                file_path=file_path,
                content="\n".join(current_chunk_lines),
                start_line=start_line,
                end_line=len(lines),
                chunk_type=ChunkType.DOC,
                metadata={"heading": current_heading}
            ))
            
        return chunks
