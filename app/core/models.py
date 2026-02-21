"""WeatherSnapshot, DerivedScenario, RiskScores."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WeatherSnapshot(BaseModel):
    """Point-in-time weather data from NWS."""

    temperature: float | None = None  # °F
    wind_speed: float | None = None  # mph
    wind_gust: float | None = None  # mph
    precipitation_probability: float | None = None  # 0–100
    heat_index: float | None = None  # °F, computed if not provided
    alerts: list[dict[str, Any]] = Field(default_factory=list)
    forecast_summary: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    lat: float | None = None
    lon: float | None = None
    zip_code: str | None = None


class DerivedScenario(BaseModel):
    """Weather-derived scenario from trigger engine."""

    event_type: str  # heat, wind, storm, critical, normal
    severity_level: str  # low, medium, high, critical
    trigger_reason: str
    confidence_score: float = Field(ge=0.0, le=1.0)


class RiskScores(BaseModel):
    """Deterministic risk scores 0–100."""

    load_stress: float = Field(ge=0, le=100)
    outage_likelihood: float = Field(ge=0, le=100)
    restoration_difficulty: float = Field(ge=0, le=100)
    crew_urgency: float = Field(ge=0, le=100)
    public_safety_risk: float = Field(ge=0, le=100)
