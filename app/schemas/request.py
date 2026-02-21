"""Request schemas for API endpoints."""

from pydantic import BaseModel
from typing import Optional

class AnalyzeRequest(BaseModel):
    """Request for /analyze endpoint."""
    latitude: float
    longitude: float
    scenario: Optional[str] = None
    include_playbook: bool = True
    
    class Config:
        title = "Analyze Request"
        example = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "scenario": None,
            "include_playbook": True
        }
