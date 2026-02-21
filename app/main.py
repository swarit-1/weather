"""FastAPI entrypoint for weather analysis service."""

from fastapi import FastAPI
from pydantic import BaseModel
from app.api import routes
from app.utils import logging
from app.schemas import WeatherSnapshot, RiskAnalysisOutput
from app.services import run_risk_analysis

app = FastAPI(title="Weather Analysis API")

# Include routers
app.include_router(routes.router)


class RiskAnalysisRequest(BaseModel):
    weather_snapshot: WeatherSnapshot


@app.post("/risk-analysis", response_model=RiskAnalysisOutput)
async def risk_analysis(request: RiskAnalysisRequest) -> RiskAnalysisOutput:
    return run_risk_analysis(request.weather_snapshot)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import json
    from datetime import datetime, timezone

    mock_snapshot = WeatherSnapshot(
        zip="78701",
        latitude=30.2672,
        longitude=-97.7431,
        temperature=98.0,
        wind_speed=25.0,
        wind_gust=48.0,
        precipitation_probability=75.0,
        heat_index=112.0,
        alerts=[
            {
                "event": "Severe Thunderstorm Warning",
                "severity": "Severe",
                "headline": "Severe Thunderstorm Warning for Travis County",
                "description": "Damaging winds and large hail expected.",
                "effective": datetime.now(timezone.utc).isoformat(),
                "expires": datetime.now(timezone.utc).isoformat(),
            }
        ],
        forecast_summary="Severe thunderstorms expected with high winds and extreme heat.",
        timestamp=datetime.now(timezone.utc),
    )

    result = run_risk_analysis(mock_snapshot)
    print(json.dumps(result.model_dump(), indent=2, default=str))
