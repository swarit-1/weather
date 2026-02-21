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
