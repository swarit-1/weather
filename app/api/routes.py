"""StormOps Console API — stateless, no DB."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.models import DerivedScenario, RiskScores, WeatherSnapshot
from app.core.orchestration import run_autonomous_cycle
from app.core.risk_engine import compute_risk_scores
from app.core.trigger_engine import derive_scenario
from app.core.weather_service import fetch_live_weather

router = APIRouter()


class AutonomousCycleRequest(BaseModel):
    weather_snapshot: WeatherSnapshot
    simulate: Optional[str] = None


@router.get("/analyze")
async def analyze(
    zip: str = Query(..., description="ZIP code for weather and risk analysis"),
) -> dict:
    """Fetch live weather from NWS, derive scenario, and compute risk scores."""
    zip_code = zip.strip()
    if not zip_code:
        raise HTTPException(status_code=400, detail="ZIP code required")

    weather_snapshot: WeatherSnapshot = await fetch_live_weather(zip_code)
    derived_scenario: DerivedScenario = derive_scenario(weather_snapshot)
    risk_scores: RiskScores = compute_risk_scores(weather_snapshot, derived_scenario)

    return {
        "weather_snapshot": weather_snapshot.model_dump(mode="json"),
        "derived_scenario": derived_scenario.model_dump(),
        "risk_scores": risk_scores.model_dump(),
    }


@router.post("/run-autonomous-cycle")
async def autonomous_cycle(request: AutonomousCycleRequest) -> dict:
    """
    Full autonomous cycle: trigger -> risk -> RAG -> LLM playbook -> RunRecord.

    Accepts a WeatherSnapshot and optional simulation override.
    """
    try:
        record = run_autonomous_cycle(
            snapshot=request.weather_snapshot,
            simulate=request.simulate,
        )
        return record.model_dump(mode="json")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
