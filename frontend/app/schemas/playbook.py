"""Playbook and action models."""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Action(BaseModel):
    """Individual action recommendation."""
    id: str
    role: str
    description: str
    priority: str  # low, medium, high, critical
    deadline: Optional[str] = None
    
    class Config:
        title = "Action"

class Playbook(BaseModel):
    """Playbook containing predefined actions."""
    playbook_id: str
    name: str
    description: str
    scenarios: List[str]
    actions: List[Action]
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        title = "Playbook"
