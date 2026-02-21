"""RAG system for risk evidence retrieval using FAISS and OpenAI embeddings."""

import os
import hashlib
from pathlib import Path
from typing import List

import faiss
import numpy as np
from openai import OpenAI

from app.schemas import RAGSnippet

DOCS_DIR = Path(__file__).parent / "data" / "austin_energy_docs"
INDEX_PATH = Path(__file__).parent / "data" / "faiss_index.bin"
CHUNKS_PATH = Path(__file__).parent / "data" / "chunks.npy"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
CHUNK_SIZE = 500

_index: faiss.IndexFlatIP = None
_chunks: List[dict] = []
_client: OpenAI = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def _chunk_text(text: str, source: str, chunk_size: int = CHUNK_SIZE) -> List[dict]:
    """Split text into chunks of approximately chunk_size tokens (estimated by words)."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk_words = words[i : i + chunk_size]
        chunk_text = " ".join(chunk_words)
        chunk_id = hashlib.md5(f"{source}:{i}".encode()).hexdigest()
        chunks.append({
            "id": chunk_id,
            "title": Path(source).stem.replace("_", " ").title(),
            "url": source,
            "text": chunk_text,
        })
    return chunks


def _embed(texts: List[str]) -> np.ndarray:
    """Embed a list of texts using OpenAI."""
    client = _get_client()
    response = client.embeddings.create(input=texts, model=EMBEDDING_MODEL)
    vectors = [item.embedding for item in response.data]
    return np.array(vectors, dtype=np.float32)


def _build_index() -> None:
    """Load docs, chunk, embed, and build FAISS index."""
    global _index, _chunks

    if not DOCS_DIR.exists():
        DOCS_DIR.mkdir(parents=True, exist_ok=True)

    all_chunks = []
    for filepath in sorted(DOCS_DIR.glob("*.txt")):
        text = filepath.read_text(encoding="utf-8")
        if text.strip():
            all_chunks.extend(_chunk_text(text, str(filepath)))

    if not all_chunks:
        _index = faiss.IndexFlatIP(EMBEDDING_DIM)
        _chunks = []
        return

    texts = [c["text"] for c in all_chunks]
    embeddings = _embed(texts)

    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(EMBEDDING_DIM)
    index.add(embeddings)

    faiss.write_index(index, str(INDEX_PATH))
    np.save(str(CHUNKS_PATH), all_chunks, allow_pickle=True)

    _index = index
    _chunks = all_chunks


def _load_or_build_index() -> None:
    """Load persisted index or build from scratch."""
    global _index, _chunks

    if _index is not None:
        return

    if INDEX_PATH.exists() and CHUNKS_PATH.exists():
        _index = faiss.read_index(str(INDEX_PATH))
        _chunks = list(np.load(str(CHUNKS_PATH), allow_pickle=True))
    else:
        _build_index()


def retrieve_snippets(query: str, k: int = 3) -> List[RAGSnippet]:
    """Retrieve top-k relevant snippets for a query."""
    _load_or_build_index()

    if _index is None or _index.ntotal == 0:
        return []

    query_vec = _embed([query])
    faiss.normalize_L2(query_vec)

    scores, indices = _index.search(query_vec, min(k, _index.ntotal))

    snippets = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        chunk = _chunks[idx]
        snippets.append(
            RAGSnippet(
                id=chunk["id"],
                title=chunk["title"],
                url=chunk["url"],
                text=chunk["text"],
                relevance_score=round(float(score), 4),
                role_tag="general",
            )
        )

    return snippets
