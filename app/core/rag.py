"""
RAG retrieval wrapper for the autonomous cycle.

Uses the existing retrieval infrastructure (pdf_to_embeddings, protocol_retrieval)
to retrieve snippets given a RiskAnalysisOutput.
Returns a ContextBundle with general and role-specific snippets.
"""

from typing import List

from app.retrieval.rag_schema import (
    ContextBundle,
    RAGSnippet,
    RiskAnalysisOutput,
)
from app.retrieval.pdf_to_embeddings import get_query_embedding, load_vector_store_from_json
from app.retrieval.protocol_retrieval import (
    retrieve_protocol_snippets_from_risk,
    merge_rag_evidence,
    set_rag_evidence_from_bundle,
)


def retrieve_snippets(
    ra: RiskAnalysisOutput,
    top_k_general: int = 4,
    top_k_per_role: int = 3,
) -> ContextBundle:
    """
    Retrieve RAG snippets for a RiskAnalysisOutput.

    Loads the vector store, embeds the query, filters by metadata,
    ranks by cosine similarity, and returns a ContextBundle.
    """
    store = load_vector_store_from_json()
    get_records = store.get_all_records
    embed = get_query_embedding

    bundle = retrieve_protocol_snippets_from_risk(
        ra,
        get_records,
        embed,
        top_k_general=top_k_general,
        top_k_per_role=top_k_per_role,
    )
    set_rag_evidence_from_bundle(ra, bundle, k_total=top_k_general + top_k_per_role)
    return bundle


def get_all_snippets(bundle: ContextBundle, k_total: int = 8) -> List[RAGSnippet]:
    """Merge general + role-specific snippets, de-duped, top k_total."""
    return merge_rag_evidence(
        bundle.general_snippets,
        bundle.role_specific_snippets,
        k_total=k_total,
    )
