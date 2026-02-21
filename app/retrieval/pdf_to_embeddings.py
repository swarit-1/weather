"""
PDF → embeddings pipeline: extract text, embed via OpenAI, upsert into local JSON store.
Stores VectorRecord (id, title, url, text, embedding, tags). Tags are required for new records;
legacy records without tags get default_tags() when loaded.
"""

import argparse
import json
import os
import uuid
from pathlib import Path
from typing import List, Optional

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

from app.retrieval.rag_schema import (
    VectorRecord,
    VectorRecordTags,
    default_tags,
)
from app.retrieval.vector_store import VectorStore

load_dotenv()

# Default store path and embedding model
DEFAULT_STORE_PATH = Path(__file__).resolve().parent / "local_embeddings.json"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
DEFAULT_SIMILARITY_THRESHOLD = float(os.getenv("EMBEDDING_SIMILARITY_THRESHOLD", "0.92"))


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    return float(dot / (norm_a * norm_b)) if norm_a > 0 and norm_b > 0 else 0.0


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from a PDF file."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("pypdf is required. Install with: pip install pypdf")

    reader = PdfReader(pdf_path)
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks (by character count)."""
    if not text or chunk_size <= 0:
        return []
    text = text.strip()
    if not text:
        return []
    step = max(1, chunk_size - overlap)
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += step
    return chunks


def get_embeddings(client: OpenAI, texts: List[str], model: str = EMBEDDING_MODEL) -> List[List[float]]:
    """Get embedding vectors for a list of texts via OpenAI API."""
    if not texts:
        return []
    response = client.embeddings.create(model=model, input=texts)
    order = {e.index: e.embedding for e in response.data}
    return [order[i] for i in range(len(texts))]


def get_query_embedding(query: str, model: str = EMBEDDING_MODEL) -> List[float]:
    """
    Get embedding for a single query string (e.g. for retrieval).
    Uses OPENAI_API_KEY or LLM_API_KEY. Do not change embedding logic.
    """
    key = OPENAI_API_KEY
    if not key:
        raise ValueError("Set OPENAI_API_KEY or LLM_API_KEY in the environment")
    client = OpenAI(api_key=key)
    vectors = get_embeddings(client, [query], model=model)
    return vectors[0] if vectors else []


# --- Infer tags from chunk context (protocol/playbook content) ---

# Keyword cues for event_type and role_tag (energy company protocol)
_EVENT_CUES = {
    "heat": ("heat", "temperature", "cooling", "load management", "peak demand", "heat index", "extreme heat"),
    "wind": ("wind", "gust", "high wind", "elevated work", "wind speed", "wind advisory"),
    "storm": ("storm", "thunderstorm", "lightning", "precipitation", "flood", "severe weather"),
    "critical": ("tornado", "severe thunderstorm", "flash flood", "emergency", "evacuation", "warning", "critical"),
}
_ROLE_CUES = {
    "grid_ops": ("load", "transformer", "generation", "grid", "demand", "shedding", "capacity", "distribution", "voltage", "substation", "circuit"),
    "field_ops": ("crew", "field", "restoration", "safety", "work order", "dispatch", "bucket truck", "line crew", "elevated work", "personal protective"),
    "comms": ("public", "customer", "communication", "advisory", "notification", "message", "press", "media", "outage notification", "social media"),
}


def infer_tags_from_chunk_text(chunk: str, title: str = "") -> VectorRecordTags:
    """
    Infer event_types and role_tag from chunk (and title) content.
    Used when ingesting protocol/playbook so tags reflect what the chunk actually says.
    """
    text = (title + " " + chunk).lower()
    event_types = []
    for event, cues in _EVENT_CUES.items():
        if any(c in text for c in cues):
            event_types.append(event)
    if not event_types:
        event_types = ["normal"]

    role_scores = {}
    for role, cues in _ROLE_CUES.items():
        role_scores[role] = sum(1 for c in cues if c in text)
    best_role = max(role_scores, key=role_scores.get)
    role_tag = best_role if role_scores[best_role] > 0 else "general"

    return VectorRecordTags(
        event_types=event_types,
        severity_min="low",
        role_tag=role_tag,
    )


def get_tags_for_chunk_llm(
    client: OpenAI,
    chunk: str,
    title: str = "",
    model: str = "gpt-4o-mini",
) -> VectorRecordTags:
    """
    Use LLM to infer event_types and role_tag from chunk context.
    Falls back to infer_tags_from_chunk_text if parsing fails.
    """
    prompt = (
        "This is an excerpt from an energy company protocol/playbook.\n\n"
        f"Title: {title}\n\nExcerpt:\n{chunk[:2500]}\n\n"
        "Return a JSON object with exactly:\n"
        '"event_types": array of one or more of "normal", "heat", "wind", "storm", "critical",\n'
        '"role_tag": one of "grid_ops", "field_ops", "comms", "general"\n'
        "Base event_types and role_tag on what the excerpt is about (e.g. load/transformer → grid_ops + heat, crew safety in wind → field_ops + wind). "
        "Return only the JSON object, no other text."
    )
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = (response.choices[0].message.content or "").strip()
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()
        data = json.loads(content)
        event_types = data.get("event_types") or ["normal"]
        role_tag = data.get("role_tag") or "general"
        if role_tag not in ("grid_ops", "field_ops", "comms", "general"):
            role_tag = "general"
        return VectorRecordTags(
            event_types=[e for e in event_types if e in ("normal", "heat", "wind", "storm", "critical")] or ["normal"],
            severity_min="low",
            role_tag=role_tag,
        )
    except (json.JSONDecodeError, TypeError, KeyError):
        return infer_tags_from_chunk_text(chunk, title)


def get_keywords_for_chunk(client: OpenAI, chunk: str, model: str = "gpt-4o-mini") -> List[str]:
    """Use GPT to extract a short list of keywords for a text chunk."""
    prompt = (
        "Extract 3–8 important keywords or short phrases from the following text. "
        "Return only a JSON array of strings, no other text.\n\nText:\n"
    ) + chunk[:2000]
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    content = (response.choices[0].message.content or "").strip()
    # Handle possible markdown code block
    if content.startswith("```"):
        content = content.split("\n", 1)[-1].rsplit("```", 1)[0]
    try:
        keywords = json.loads(content)
        return [str(k).strip() for k in keywords if k][:10]
    except (json.JSONDecodeError, TypeError):
        return []


def _legacy_to_vector_record(item: dict) -> VectorRecord:
    """Convert legacy stored shape (id, vector, text, keywords) to VectorRecord with default tags."""
    tags = default_tags()
    if "keywords" in item and item["keywords"]:
        tags = VectorRecordTags(
            event_types=tags.event_types,
            severity_min=tags.severity_min,
            role_tag=tags.role_tag,
            risk_factor=tags.risk_factor,
            keywords=item["keywords"],
            source_quality=tags.source_quality,
        )
    return VectorRecord(
        id=item["id"],
        title=item.get("title", ""),
        url=item.get("url", ""),
        text=item["text"],
        embedding=item["vector"],
        tags=tags,
    )


def load_store(store_path: Path) -> List[VectorRecord]:
    """Load VectorRecords from the local JSON file. Legacy records get default_tags()."""
    if not store_path.exists():
        return []
    with open(store_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    out = []
    for item in data:
        if "tags" in item and item["tags"]:
            out.append(VectorRecord.model_validate(item))
        else:
            out.append(_legacy_to_vector_record(item))
    return out


def load_vector_store_from_json(
    store_path: Optional[Path] = None,
) -> VectorStore:
    """Load local_embeddings.json into an in-memory VectorStore for retrieval. Default path: app/retrieval/local_embeddings.json."""
    path = Path(store_path) if store_path is not None else DEFAULT_STORE_PATH
    records = load_store(path)
    store = VectorStore()
    store.add_records(records)
    return store


def save_store(store_path: Path, records: List[VectorRecord]) -> None:
    """Write VectorRecords to the local JSON file."""
    store_path.parent.mkdir(parents=True, exist_ok=True)
    with open(store_path, "w", encoding="utf-8") as f:
        json.dump([r.model_dump() for r in records], f, indent=2, ensure_ascii=False)


def max_similarity_to_store(new_vec: List[float], store: List[VectorRecord]) -> float:
    """Return the maximum cosine similarity between new_vec and any record in store."""
    if not store:
        return 0.0
    new_arr = np.array(new_vec, dtype=float)
    best = -1.0
    for r in store:
        sim = cosine_similarity(new_arr, np.array(r.embedding, dtype=float))
        if sim > best:
            best = sim
    return best


def run(
    pdf_path: str,
    store_path: Optional[str] = None,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    chunk_size: int = 512,
    overlap: int = 50,
    embedding_model: str = EMBEDDING_MODEL,
    keyword_model: str = "gpt-4o-mini",
    tags: Optional[VectorRecordTags] = None,
    title: Optional[str] = None,
    url: str = "",
    infer_tags_from_context: bool = False,
    infer_tags_with_llm: bool = False,
) -> int:
    """
    Process a PDF: extract text, chunk, embed, extract keywords, upsert VectorRecords.

    Tags:
    - If infer_tags_from_context=True, event_types and role_tag are inferred from each
      chunk's content (protocol/playbook). Use infer_tags_with_llm=True for LLM-based
      inference; else keyword-based heuristics. Recommended for energy company protocol docs.
    - Otherwise, tags come from the tags argument (or default_tags()).
    Only adds a record if its embedding is not already represented (max similarity < threshold).
    Returns the number of new records added.
    """
    if not OPENAI_API_KEY:
        raise ValueError("Set OPENAI_API_KEY or LLM_API_KEY in the environment")

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    record_tags = tags if tags is not None else default_tags()
    doc_title = title if title is not None else path.stem

    store_file = Path(store_path) if store_path else DEFAULT_STORE_PATH
    store = load_store(store_file)
    client = OpenAI(api_key=OPENAI_API_KEY)

    text = extract_text_from_pdf(str(path))
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        return 0

    vectors = get_embeddings(client, chunks, model=embedding_model)
    added = 0

    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        if max_similarity_to_store(vector, store) >= similarity_threshold:
            continue
        keywords = get_keywords_for_chunk(client, chunk, model=keyword_model)
        if infer_tags_from_context:
            if infer_tags_with_llm:
                base_tags = get_tags_for_chunk_llm(client, chunk, title=doc_title, model=keyword_model)
            else:
                base_tags = infer_tags_from_chunk_text(chunk, title=doc_title)
            chunk_tags = VectorRecordTags(
                event_types=base_tags.event_types,
                severity_min=base_tags.severity_min,
                role_tag=base_tags.role_tag,
                risk_factor=record_tags.risk_factor,
                keywords=keywords or base_tags.keywords,
                source_quality=record_tags.source_quality,
            )
        else:
            chunk_tags = VectorRecordTags(
                event_types=record_tags.event_types,
                severity_min=record_tags.severity_min,
                role_tag=record_tags.role_tag,
                risk_factor=record_tags.risk_factor,
                keywords=keywords or record_tags.keywords,
                source_quality=record_tags.source_quality,
            )
        record = VectorRecord(
            id=str(uuid.uuid4()),
            title=doc_title if len(chunks) == 1 else f"{doc_title} (excerpt {i + 1})",
            url=url,
            text=chunk,
            embedding=vector,
            tags=chunk_tags,
        )
        store.append(record)
        added += 1

    if added > 0:
        save_store(store_file, store)

    return added


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest a PDF: create VectorRecords (OpenAI embeddings + tags), upsert into local JSON store."
    )
    parser.add_argument("pdf_path", help="Path to the input PDF file")
    parser.add_argument(
        "--store",
        default=None,
        help=f"Path to local embeddings JSON file (default: {DEFAULT_STORE_PATH})",
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=DEFAULT_SIMILARITY_THRESHOLD,
        help="Only add embedding if max similarity to existing vectors is below this (default: 0.92)",
    )
    parser.add_argument("--chunk-size", type=int, default=512, help="Characters per chunk (default: 512)")
    parser.add_argument("--overlap", type=int, default=50, help="Overlap between chunks (default: 50)")
    parser.add_argument("--embedding-model", default=EMBEDDING_MODEL, help="OpenAI embedding model")
    parser.add_argument("--keyword-model", default="gpt-4o-mini", help="OpenAI model for keyword extraction")
    parser.add_argument(
        "--event-types",
        nargs="+",
        default=["normal"],
        choices=["normal", "heat", "wind", "storm", "critical"],
        help="Tag event_types for deterministic filtering (default: normal)",
    )
    parser.add_argument(
        "--severity-min",
        default="low",
        choices=["low", "medium", "high", "critical"],
        help="Tag severity_min for filtering (default: low)",
    )
    parser.add_argument(
        "--role-tag",
        default="general",
        choices=["grid_ops", "field_ops", "comms", "general"],
        help="Tag role_tag for snippet selection (default: general)",
    )
    parser.add_argument(
        "--risk-factor",
        type=int,
        default=None,
        metavar="0-100",
        help="Risk factor 0–100 for this weather event (optional)",
    )
    parser.add_argument("--title", default=None, help="Document title for stored records (default: PDF stem)")
    parser.add_argument("--url", default="", help="URL for stored records (default: empty)")
    parser.add_argument(
        "--infer-tags-from-context",
        action="store_true",
        help="Infer event_types and role_tag from each chunk's content (for protocol/playbook docs)",
    )
    parser.add_argument(
        "--infer-tags-with-llm",
        action="store_true",
        help="Use LLM to infer tags from chunk context (requires --infer-tags-from-context)",
    )
    args = parser.parse_args()

    tags = VectorRecordTags(
        event_types=args.event_types,
        severity_min=args.severity_min,
        role_tag=args.role_tag,
        risk_factor=args.risk_factor,
    )
    added = run(
        pdf_path=args.pdf_path,
        store_path=args.store,
        similarity_threshold=args.similarity_threshold,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        embedding_model=args.embedding_model,
        keyword_model=args.keyword_model,
        tags=tags,
        title=args.title,
        url=args.url,
        infer_tags_from_context=args.infer_tags_from_context,
        infer_tags_with_llm=args.infer_tags_with_llm,
    )
    print(f"Added {added} new embedding(s) to the store.")


if __name__ == "__main__":
    main()
