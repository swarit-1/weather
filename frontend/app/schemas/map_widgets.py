"""Map widget schemas for visualization."""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Overlay(BaseModel):
    """Map overlay layer."""
    overlay_id: str
    name: str
    type: str  # heatmap, polygon, geojson, etc.
    data: Dict[str, Any]
    opacity: float = 0.7
    
    class Config:
        title = "Overlay"

class Pin(BaseModel):
    """Map pin/marker."""
    pin_id: str
    latitude: float
    longitude: float
    label: str
    icon_type: str
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        title = "Pin"

class MapWidgets(BaseModel):
    """Container for map visualization widgets."""
    overlays: List[Overlay] = []
    pins: List[Pin] = []
    
    class Config:
        title = "Map Widgets"
