"""In-memory cosine similarity vector store."""

from typing import List, Dict
import numpy as np
from app.retrieval.chunk_models import EmbeddedChunk, RetrievalResult

class VectorStore:
    """In-memory vector store with cosine similarity search."""
    
    def __init__(self):
        self.chunks: Dict[str, EmbeddedChunk] = {}
        self.embeddings: Dict[str, np.ndarray] = {}
    
    def add_chunks(self, chunks: List[EmbeddedChunk]) -> None:
        """Add embedded chunks to the store."""
        for chunk in chunks:
            self.chunks[chunk.chunk_id] = chunk
            self.embeddings[chunk.chunk_id] = np.array(chunk.embedding)
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[RetrievalResult]:
        """
        Search vector store using cosine similarity.
        
        Args:
            query_embedding: Query vector
            top_k: Number of top results to return
            
        Returns:
            List of RetrievalResult sorted by similarity
        """
        query_vec = np.array(query_embedding)
        similarities = {}
        
        for chunk_id, embedding in self.embeddings.items():
            similarity = self._cosine_similarity(query_vec, embedding)
            similarities[chunk_id] = similarity
        
        # Sort by similarity and get top-k
        top_chunks = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        results = []
        for chunk_id, score in top_chunks:
            chunk = self.chunks[chunk_id]
            results.append(RetrievalResult(
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                similarity_score=float(score),
                source=chunk.source
            ))
        
        return results
    
    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        return dot_product / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0.0
