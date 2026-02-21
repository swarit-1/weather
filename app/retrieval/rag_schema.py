"""
SOLIDIFIED SCHEMA (DO NOT CHANGE).
RAG snippet, context bundle, and risk analysis types for retrieval pipeline.
"""

from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, field_validator

# --- Schema enums (must match exactly) ---
EventType = Literal["normal", "heat", "wind", "storm", "critical"]
SeverityLevel = Literal["low", "medium", "high", "critical"]
RoleTag = Literal["grid_ops", "field_ops", "comms", "general"]
SourceQuality = Literal["authoritative", "industry_guidance", "internal_playbook"]

# Severity ordering for deterministic filter: low < medium < high < critical
SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def severity_level_rank(level: SeverityLevel) -> int:
    """Numeric rank for severity comparison. Higher = more severe."""
    return SEVERITY_RANK.get(level, 0)


def satisfies_severity_min(context_level: SeverityLevel, record_min: SeverityLevel) -> bool:
    """True iff context severity is >= record's severity_min."""
    return severity_level_rank(context_level) >= severity_level_rank(record_min)


# --- SOLIDIFIED SCHEMA ---


class Alert(BaseModel):
    event: str
    severity: str
    headline: str
    description: str
    effective: datetime
    expires: datetime


class WeatherSnapshot(BaseModel):
    zip: str
    latitude: float
    longitude: float
    temperature: float
    wind_speed: float
    wind_gust: float
    precipitation_probability: float
    heat_index: float
    alerts: List[Alert]
    forecast_summary: str
    timestamp: datetime


class DerivedScenario(BaseModel):
    event_type: EventType
    severity_level: SeverityLevel
    trigger_reason: str
    confidence_score: float  # 0–1


class RiskScores(BaseModel):
    load_stress: int  # 0–100
    outage_likelihood: int  # 0–100
    restoration_difficulty: int
    crew_urgency: int
    public_safety_risk: int


class RAGSnippet(BaseModel):
    id: str
    title: str
    url: str
    text: str
    relevance_score: float
    role_tag: RoleTag


class ContextBundle(BaseModel):
    weather_snapshot: WeatherSnapshot
    derived_scenario: DerivedScenario
    risk_scores: RiskScores
    general_snippets: List[RAGSnippet]
    role_specific_snippets: List[RAGSnippet]


class RiskAnalysisOutput(BaseModel):
    zip: str
    weather_snapshot: WeatherSnapshot
    derived_scenario: DerivedScenario
    risk_scores: RiskScores
    top_risk_driver: str
    rag_evidence: List[RAGSnippet]


# --- Vector store record (stored in local DB) ---


class VectorRecordTags(BaseModel):
    """Tags for deterministic filtering. Must match schema enums."""
    event_types: List[EventType]
    severity_min: SeverityLevel
    role_tag: RoleTag
    risk_factor: Optional[int] = None  # 0–100, per weather event; aligns with RiskScores scale
    keywords: Optional[List[str]] = None
    source_quality: Optional[SourceQuality] = None

    @field_validator("event_types")
    @classmethod
    def validate_event_types(cls, v: List[str]) -> List[EventType]:
        allowed = {"normal", "heat", "wind", "storm", "critical"}
        for e in v:
            if e not in allowed:
                raise ValueError(f"event_type must be one of {allowed}, got {e!r}")
        return [e for e in v]

    @field_validator("severity_min")
    @classmethod
    def validate_severity_min(cls, v: str) -> SeverityLevel:
        if v not in ("low", "medium", "high", "critical"):
            raise ValueError("severity_min must be low|medium|high|critical")
        return v

    @field_validator("role_tag")
    @classmethod
    def validate_role_tag(cls, v: str) -> RoleTag:
        if v not in ("grid_ops", "field_ops", "comms", "general"):
            raise ValueError("role_tag must be grid_ops|field_ops|comms|general")
        return v

    @field_validator("risk_factor")
    @classmethod
    def validate_risk_factor(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if not 0 <= v <= 100:
            raise ValueError("risk_factor must be 0–100")
        return v


def default_tags() -> VectorRecordTags:
    """Safe default for records without metadata (legacy content)."""
    return VectorRecordTags(
        event_types=["normal"],
        severity_min="low",
        role_tag="general",
    )


class VectorRecord(BaseModel):
    """Single record in the local vector store. Maps to RAGSnippet on retrieval."""
    id: str
    title: str
    url: str
    text: str
    embedding: List[float]
    tags: VectorRecordTags


def vector_record_to_snippet(record: VectorRecord, relevance_score: float) -> RAGSnippet:
    """Map a VectorRecord to RAGSnippet with the given relevance score."""
    return RAGSnippet(
        id=record.id,
        title=record.title,
        url=record.url,
        text=record.text,
        relevance_score=relevance_score,
        role_tag=record.tags.role_tag,
    )
