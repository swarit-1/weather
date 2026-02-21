"""
Example: ContextBundle + VectorRecords with tags → retrieve_snippets → RAGSnippet lists.
Uses mock embeddings so it runs without OPENAI_API_KEY. For real retrieval, use
get_query_embedding from pdf_to_embeddings as the Retriever's embedding_fn.
"""

from datetime import datetime

from app.retrieval.rag_schema import (
    Alert,
    ContextBundle,
    DerivedScenario,
    RiskScores,
    VectorRecord,
    VectorRecordTags,
    WeatherSnapshot,
)
from app.retrieval.vector_store import VectorStore, retrieve_snippets
from app.retrieval.retriever import Retriever

# Dimension for mock embeddings (match typical OpenAI embedding size)
DIM = 1536


def _mock_embedding(seed: int) -> list[float]:
    """Deterministic mock vector for examples (no API call)."""
    return [0.1 * (seed + i) % 1.0 for i in range(DIM)]


def _mock_embedding_fn(text: str) -> list[float]:
    """Use hash of text so similar queries get similar vectors in the example."""
    return _mock_embedding(hash(text) % 1000)


def build_example_context_bundle() -> ContextBundle:
    """Build a ContextBundle with heat scenario and non-empty risk scores."""
    return ContextBundle(
        weather_snapshot=WeatherSnapshot(
            zip="90210",
            latitude=34.05,
            longitude=-118.25,
            temperature=98.0,
            wind_speed=8.0,
            wind_gust=12.0,
            precipitation_probability=0.0,
            heat_index=102.0,
            alerts=[
                Alert(
                    event="Excessive Heat Warning",
                    severity="Extreme",
                    headline="Excessive Heat Warning",
                    description="Heat index above 100.",
                    effective=datetime(2025, 7, 1, 12, 0),
                    expires=datetime(2025, 7, 1, 20, 0),
                )
            ],
            forecast_summary="Hot and dry.",
            timestamp=datetime(2025, 7, 1, 12, 0),
        ),
        derived_scenario=DerivedScenario(
            event_type="heat",
            severity_level="high",
            trigger_reason="Heat index above threshold",
            confidence_score=0.9,
        ),
        risk_scores=RiskScores(
            load_stress=85,
            outage_likelihood=40,
            restoration_difficulty=50,
            crew_urgency=60,
            public_safety_risk=70,
        ),
        general_snippets=[],
        role_specific_snippets=[],
    )


def build_example_records() -> list[VectorRecord]:
    """Build 2–3 VectorRecords with realistic tags (heat/wind/storm and roles)."""
    return [
        VectorRecord(
            id="rec-heat-grid",
            title="Heat load management procedures",
            url="https://example.com/heat-grid",
            text="During extreme heat, reduce non-essential load and monitor transformer temperatures.",
            embedding=_mock_embedding(1),
            tags=VectorRecordTags(
                event_types=["heat", "critical"],
                severity_min="medium",
                role_tag="grid_ops",
                risk_factor=75,
                keywords=["heat", "load", "transformer", "warning"],
            ),
        ),
        VectorRecord(
            id="rec-wind-field",
            title="Field ops wind safety",
            url="https://example.com/wind-field",
            text="When wind gusts exceed 40 mph, suspend elevated work and secure equipment.",
            embedding=_mock_embedding(2),
            tags=VectorRecordTags(
                event_types=["wind", "storm"],
                severity_min="high",
                role_tag="field_ops",
                risk_factor=60,
                keywords=["wind", "gust", "advisory", "safety"],
            ),
        ),
        VectorRecord(
            id="rec-general-heat",
            title="General heat advisory guidance",
            url="https://example.com/general-heat",
            text="Stay hydrated and limit outdoor exposure during heat advisories.",
            embedding=_mock_embedding(3),
            tags=VectorRecordTags(
                event_types=["normal", "heat"],
                severity_min="low",
                role_tag="general",
                risk_factor=40,
                keywords=["heat", "advisory", "hydration"],
            ),
        ),
    ]


def main() -> None:
    # 1) Construct ContextBundle
    context = build_example_context_bundle()

    # 2) Insert VectorRecords into store
    store = VectorStore()
    records = build_example_records()
    store.add_records(records)

    # 3) Retrieve snippets (query embedding from mock fn; no API)
    query_text = "How to handle heat and load?"
    query_embedding = _mock_embedding_fn(query_text)
    general_snippets, role_specific_snippets = retrieve_snippets(
        store.get_all_records(),
        query_embedding,
        context,
        top_k_general=2,
        top_k_role=2,
        desired_role=None,  # derived from risk_scores: load_stress=85 highest => grid_ops
    )

    # 4) Show results (role is derived: public_safety_risk=70 is highest so comms)
    print("Query:", query_text)
    print("\n--- general_snippets ---")
    for s in general_snippets:
        print(f"  [{s.role_tag}] {s.title}: score={s.relevance_score:.4f}")
    print("\n--- role_specific_snippets (derived role) ---")
    for s in role_specific_snippets:
        print(f"  [{s.role_tag}] {s.title}: score={s.relevance_score:.4f}")

    # 5) Optional: use Retriever with same mock embedding fn
    retriever = Retriever(store, _mock_embedding_fn)
    gen2, role2 = retriever.retrieve_snippets(
        query_text, context, top_k_general=2, top_k_role=2, desired_role="grid_ops"
    )
    print("\n--- role_specific_snippets (desired_role=grid_ops) ---")
    for s in role2:
        print(f"  [{s.role_tag}] {s.title}: score={s.relevance_score:.4f}")


if __name__ == "__main__":
    main()
