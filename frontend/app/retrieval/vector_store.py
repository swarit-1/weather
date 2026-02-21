"""In-memory vector store with VectorRecord schema and deterministic filtering."""

from typing import List, Optional, Tuple

import numpy as np

from app.retrieval.rag_schema import (
    ContextBundle,
    RAGSnippet,
    RiskScores,
    VectorRecord,
    VectorRecordTags,
    satisfies_severity_min,
    vector_record_to_snippet,
    RoleTag,
)

# Alert-related keywords for optional boost when context has alerts
ALERT_KEYWORDS = frozenset({"warning", "watch", "advisory", "alert", "emergency"})


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    return float(dot / (norm_a * norm_b)) if norm_a > 0 and norm_b > 0 else 0.0


def _alert_boost(record: VectorRecord, context_bundle: ContextBundle) -> float:
    """Return boost multiplier (>= 1.0) when context has alerts and record suggests alerts."""
    if not context_bundle.weather_snapshot.alerts:
        return 1.0
    keywords = (record.tags.keywords or []) + [record.title, record.text[:200]]
    text_lower = " ".join(str(k).lower() for k in keywords)
    if any(term in text_lower for term in ALERT_KEYWORDS):
        return 1.1
    return 1.0


def filter_records(
    records: List[VectorRecord],
    context_bundle: ContextBundle,
    desired_role: RoleTag,
) -> List[VectorRecord]:
    """
    Deterministic filter: keep only records eligible for this context and role.

    Rules:
    - context_bundle.derived_scenario.event_type must be in record.tags.event_types
    - context_bundle.derived_scenario.severity_level >= record.tags.severity_min
    - record.tags.role_tag == desired_role OR record.tags.role_tag == "general"
    """
    event_type = context_bundle.derived_scenario.event_type
    severity_level = context_bundle.derived_scenario.severity_level
    eligible = []
    for r in records:
        if event_type not in r.tags.event_types:
            continue
        if not satisfies_severity_min(severity_level, r.tags.severity_min):
            continue
        if r.tags.role_tag != desired_role and r.tags.role_tag != "general":
            continue
        eligible.append(r)
    return eligible


def top_k_by_similarity(
    records: List[VectorRecord],
    query_embedding: List[float],
    top_k: int,
    context_bundle: Optional[ContextBundle] = None,
) -> List[Tuple[VectorRecord, float]]:
    """
    Rank records by cosine similarity to query, optionally apply alert boost.
    Returns list of (record, score) sorted by score descending, length <= top_k.
    """
    if not records:
        return []
    query_vec = np.array(query_embedding, dtype=float)
    scored = []
    for r in records:
        sim = _cosine_similarity(query_vec, np.array(r.embedding, dtype=float))
        if context_bundle:
            sim *= _alert_boost(r, context_bundle)
        scored.append((r, sim))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


class VectorStore:
    """In-memory vector store keyed by VectorRecord.id with cosine similarity search."""

    def __init__(self) -> None:
        self._records: dict[str, VectorRecord] = {}
        self._embeddings: dict[str, np.ndarray] = {}

    def add_record(self, record: VectorRecord) -> None:
        """Add or replace a single VectorRecord."""
        self._records[record.id] = record
        self._embeddings[record.id] = np.array(record.embedding, dtype=float)

    def add_records(self, records: List[VectorRecord]) -> None:
        """Add or replace multiple VectorRecords."""
        for r in records:
            self.add_record(r)

    def get_all_records(self) -> List[VectorRecord]:
        """Return all stored records (order not guaranteed)."""
        return list(self._records.values())

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        context_bundle: Optional[ContextBundle] = None,
    ) -> List[Tuple[VectorRecord, float]]:
        """
        Search all records by cosine similarity; optionally apply alert boost.
        Returns [(record, score), ...] sorted by score descending.
        """
        records = self.get_all_records()
        return top_k_by_similarity(
            records, query_embedding, top_k, context_bundle=context_bundle
        )


def retrieve_snippets(
    records: List[VectorRecord],
    query_embedding: List[float],
    context_bundle: ContextBundle,
    top_k_general: int,
    top_k_role: int,
    desired_role: Optional[RoleTag] = None,
) -> Tuple[List[RAGSnippet], List[RAGSnippet]]:
    """
    Filter by context, rank by similarity, return (general_snippets, role_specific_snippets).

    - general_snippets: desired_role="general", filter + top_k_general, map to RAGSnippet.
    - role_specific_snippets: desired_role if provided, else derived from context_bundle.risk_scores
      (load_stress => grid_ops; crew_urgency/restoration_difficulty => field_ops; public_safety_risk => comms).
    """
    # General: filter for role "general", rank, take top_k_general
    general_eligible = filter_records(records, context_bundle, "general")
    general_scored = top_k_by_similarity(
        general_eligible, query_embedding, top_k_general, context_bundle=context_bundle
    )
    general_snippets = [
        vector_record_to_snippet(r, score) for r, score in general_scored
    ]

    # Role-specific: determine role then filter + rank
    role = desired_role if desired_role is not None else _derive_role_from_risk_scores(
        context_bundle.risk_scores
    )
    role_eligible = filter_records(records, context_bundle, role)
    role_scored = top_k_by_similarity(
        role_eligible, query_embedding, top_k_role, context_bundle=context_bundle
    )
    role_snippets = [
        vector_record_to_snippet(r, score) for r, score in role_scored
    ]

    return general_snippets, role_snippets


def _derive_role_from_risk_scores(risk_scores: RiskScores) -> RoleTag:
    """Pick role to prioritize from risk_scores (single role)."""
    load = risk_scores.load_stress
    crew = risk_scores.crew_urgency
    restoration = risk_scores.restoration_difficulty
    public = risk_scores.public_safety_risk
    # Prioritize: load_stress => grid_ops; crew/restoration => field_ops; public_safety => comms
    if load >= crew and load >= restoration and load >= public:
        return "grid_ops"
    if public >= load and public >= crew and public >= restoration:
        return "comms"
    return "field_ops"
