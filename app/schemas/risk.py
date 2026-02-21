<<<<<<< HEAD
"""Risk analysis schemas for Engineer 2 scope."""

from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


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
    event_type: str
    severity: str
    confidence: float = Field(ge=0.0, le=1.0)
    trigger_reason: str


class RiskScores(BaseModel):
    load_stress: int = Field(ge=0, le=100)
    outage_likelihood: int = Field(ge=0, le=100)
    restoration_difficulty: int = Field(ge=0, le=100)
    crew_urgency: int = Field(ge=0, le=100)
    public_safety_risk: int = Field(ge=0, le=100)


class RAGSnippet(BaseModel):
    id: str
    title: str
    url: str
    text: str
    relevance_score: float
    role_tag: str = "general"


class RiskAnalysisOutput(BaseModel):
    scenario: DerivedScenario
    risk_scores: RiskScores
    top_risk_driver: str
    rag_snippets: List[RAGSnippet]
    timestamp: datetime
=======
"""
Consolidated risk analysis schemas.

Imports canonical types from app.retrieval.rag_schema (solidified, DO NOT redefine).
Adds Playbook and RunRecord for the autonomous cycle endpoint.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

# Re-export canonical types from rag_schema (single source of truth)
from app.retrieval.rag_schema import (
    Alert,
    ContextBundle,
    DerivedScenario,
    RAGSnippet,
    RiskAnalysisOutput,
    RiskScores,
    WeatherSnapshot,
)

# Re-export core WeatherSnapshot for callers that need the NWS-shaped model
from app.core.models import WeatherSnapshot as CoreWeatherSnapshot


class PlaybookAction(BaseModel):
    role: str
    action: str
    priority: str
    details: str


class Playbook(BaseModel):
    summary: str
    actions: List[PlaybookAction]
    estimated_duration: str
    risk_mitigation_notes: str


class RunRecord(BaseModel):
    timestamp: datetime
    zip_code: str
    weather_snapshot: Dict[str, Any]
    derived_scenario: Dict[str, Any]
    risk_scores: Dict[str, Any]
    top_risk_driver: str
    rag_snippets: List[Dict[str, Any]]
    playbook: Dict[str, Any]
    simulation: Optional[str] = None
>>>>>>> origin/main
