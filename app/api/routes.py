"""StormOps Console API — stateless, no DB."""

from fastapi import APIRouter, HTTPException, Query

from app.core.models import DerivedScenario, RiskScores, WeatherSnapshot
from app.core.risk_engine import compute_risk_scores
from app.core.trigger_engine import derive_scenario
from app.core.weather_service import fetch_live_weather

router = APIRouter()


@router.get("/analyze")
async def analyze(
    zip: str = Query(..., description="ZIP code for weather and risk analysis"),
) -> dict:
    """
    Fetch live weather from NWS, derive scenario, compute risk scores.
    Stateless, no persistence. Target <3s for weather.
    """
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
