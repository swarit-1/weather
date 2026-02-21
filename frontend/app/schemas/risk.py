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
