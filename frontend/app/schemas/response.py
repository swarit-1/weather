"""Response schemas for API endpoints."""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class RunRecord(BaseModel):
    """Complete analysis run record."""
    run_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    status: str
    weather_data: Optional[Dict[str, Any]] = None
    scenarios: Optional[List[str]] = None
    risk_scores: Optional[Dict[str, Any]] = None
    recommendations: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        title = "Run Record"
