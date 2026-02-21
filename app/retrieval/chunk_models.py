"""Chunk and embedding schemas for RAG system."""

from pydantic import BaseModel
from typing import List, Optional

class Chunk(BaseModel):
    """Text chunk from ingested documents."""
    chunk_id: str
    content: str
    source: str
    metadata: dict
    
    class Config:
        title = "Chunk"

class EmbeddedChunk(BaseModel):
    """Chunk with embedding vector."""
    chunk_id: str
    content: str
    embedding: List[float]
    source: str
    metadata: dict
    
    class Config:
        title = "Embedded Chunk"

class RetrievalResult(BaseModel):
    """Result from chunk retrieval."""
    chunk_id: str
    content: str
    similarity_score: float
    source: str
    role_filter: Optional[str] = None
    
    class Config:
        title = "Retrieval Result"
