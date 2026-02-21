"""Core data models for weather analysis."""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class WeatherSnapshot(BaseModel):
    """Current weather conditions snapshot."""
    timestamp: datetime
    temperature: float
    humidity: float
    wind_speed: float
    wind_direction: str
    precipitation: float
    visibility: float
    pressure: float
    cloud_cover: int
    
    class Config:
        title = "Weather Snapshot"

class DerivedScenario(BaseModel):
    """Derived scenario from weather data."""
    scenario_id: str
    name: str
    severity: str  # low, medium, high, critical
    triggers: List[str]
    affected_operations: List[str]
    
    class Config:
        title = "Derived Scenario"

class RiskScores(BaseModel):
    """Deterministic risk scoring."""
    overall_risk: float
    risk_by_category: Dict[str, float]
    affected_roles: List[str]
    confidence: float
    
    class Config:
        title = "Risk Scores"
