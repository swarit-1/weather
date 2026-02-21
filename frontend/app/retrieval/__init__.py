"""RAG retrieval package."""

from app.retrieval.rag_schema import (
    ContextBundle,
    RAGSnippet,
    RiskAnalysisOutput,
    VectorRecord,
    VectorRecordTags,
)
from app.retrieval.vector_store import (
    VectorStore,
    filter_records,
    retrieve_snippets,
    top_k_by_similarity,
)
from app.retrieval.retriever import Retriever
# load_vector_store_from_json lives in pdf_to_embeddings; import it as:
#   from app.retrieval.pdf_to_embeddings import load_vector_store_from_json
# (not re-exported here to avoid loading pdf_to_embeddings when the package is imported,
#  which would trigger RuntimeWarning when running python -m app.retrieval.pdf_to_embeddings)
from app.retrieval.protocol_retrieval import (
    build_query_text,
    context_bundle_to_playbook_context,
    context_bundle_to_playbook_context_per_role,
    format_snippets_for_llm,
    metadata_filter,
    merge_rag_evidence,
    record_to_ragsnippet,
    retrieve_protocol_snippets_from_risk,
    retrieve_top_k,
    select_roles,
    set_rag_evidence_from_bundle,
    severity_ge,
    severity_to_int,
)

__all__ = [
    "ContextBundle",
    "RAGSnippet",
    "RiskAnalysisOutput",
    "VectorRecord",
    "VectorRecordTags",
    "VectorStore",
    "filter_records",
    "retrieve_snippets",
    "top_k_by_similarity",
    "Retriever",
    "build_query_text",
    "context_bundle_to_playbook_context",
    "context_bundle_to_playbook_context_per_role",
    "format_snippets_for_llm",
    "metadata_filter",
    "merge_rag_evidence",
    "record_to_ragsnippet",
    "retrieve_protocol_snippets_from_risk",
    "retrieve_top_k",
    "select_roles",
    "set_rag_evidence_from_bundle",
    "severity_ge",
    "severity_to_int",
]
