from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel

class ChunkType(str, Enum):
    CODE = "code"
    DOC = "doc"

class Chunk(BaseModel):
    file_path: str
    content: str
    start_line: int
    end_line: int
    chunk_type: ChunkType
    metadata: Optional[Dict[str, Any]] = None
