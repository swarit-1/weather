"""Retrieval pipeline: query_text → filter by ContextBundle → RAGSnippet lists."""

from typing import List, Optional, Callable, Tuple

from app.retrieval.rag_schema import ContextBundle, RAGSnippet, RoleTag
from app.retrieval.vector_store import VectorStore, retrieve_snippets as _retrieve_snippets


class Retriever:
    """
    Retrieval layer: uses vector store + embedding_fn to return general and role-specific RAGSnippets.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_fn: Callable[[str], List[float]],
    ) -> None:
        self.vector_store = vector_store
        self.embedding_fn = embedding_fn

    def retrieve_snippets(
        self,
        query_text: str,
        context_bundle: ContextBundle,
        top_k_general: int,
        top_k_role: int,
        desired_role: Optional[RoleTag] = None,
    ) -> Tuple[List[RAGSnippet], List[RAGSnippet]]:
        """
        Compute query embedding, filter by context, rank by similarity; return RAGSnippet lists.

        Returns:
            (general_snippets, role_specific_snippets) matching ContextBundle.general_snippets
            and ContextBundle.role_specific_snippets / RiskAnalysisOutput.rag_evidence.
        """
        query_embedding = self.embedding_fn(query_text)
        records = self.vector_store.get_all_records()
        return _retrieve_snippets(
            records,
            query_embedding,
            context_bundle,
            top_k_general,
            top_k_role,
            desired_role=desired_role,
        )
