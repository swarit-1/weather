"""
Adapter: core weather/scenario/risk models → retrieval RiskAnalysisOutput (rag_schema).
Bridges the live pipeline (weather_service, trigger_engine, risk_engine) to the
RAG + LLM pipeline (retrieve_protocol_snippets_from_risk, run_playbook_decisions).
"""

from datetime import datetime, timezone

from app.core.models import DerivedScenario, RiskScores, WeatherSnapshot as CoreWeatherSnapshot
from app.retrieval.rag_schema import (
    Alert,
    DerivedScenario as RAGDerivedScenario,
    RiskAnalysisOutput,
    RiskScores as RAGRiskScores,
    WeatherSnapshot as RAGWeatherSnapshot,
)


def _core_alerts_to_rag(alerts: list) -> list:
    """Convert core alert dicts to rag_schema.Alert (default effective/expires if missing)."""
    out = []
    now = datetime.now(timezone.utc)
    for a in alerts or []:
        if not isinstance(a, dict):
            continue
        effective = now
        expires = now
        # If NWS payload has start/end, could parse here
        out.append(
            Alert(
                event=(a.get("event") or "").strip(),
                severity=(a.get("severity") or "").strip(),
                headline=(a.get("headline") or "").strip(),
                description=(a.get("description") or "").strip(),
                effective=effective,
                expires=expires,
            )
        )
    return out


def _top_risk_driver(risk_scores: RiskScores) -> str:
    """Which risk score is highest (deterministic tie-break: load_stress, then crew_urgency, etc.)."""
    d = {
        "load_stress": float(risk_scores.load_stress),
        "outage_likelihood": float(risk_scores.outage_likelihood),
        "restoration_difficulty": float(risk_scores.restoration_difficulty),
        "crew_urgency": float(risk_scores.crew_urgency),
        "public_safety_risk": float(risk_scores.public_safety_risk),
    }
    best = max(d.items(), key=lambda x: (x[1], ["load_stress", "outage_likelihood", "restoration_difficulty", "crew_urgency", "public_safety_risk"].index(x[0])))
    return best[0]


def core_to_rag_risk_analysis_output(
    weather_snapshot: CoreWeatherSnapshot,
    derived_scenario: DerivedScenario,
    risk_scores: RiskScores,
) -> RiskAnalysisOutput:
    """
    Build retrieval RiskAnalysisOutput from core pipeline outputs.
    Use this after fetch_live_weather → derive_scenario → compute_risk_scores.
    """
    ws = weather_snapshot
    rag_weather = RAGWeatherSnapshot(
        zip=(ws.zip_code or "").strip() or "unknown",
        latitude=float(ws.lat if ws.lat is not None else 0.0),
        longitude=float(ws.lon if ws.lon is not None else 0.0),
        temperature=float(ws.temperature if ws.temperature is not None else 0.0),
        wind_speed=float(ws.wind_speed if ws.wind_speed is not None else 0.0),
        wind_gust=float(ws.wind_gust if ws.wind_gust is not None else 0.0),
        precipitation_probability=float(ws.precipitation_probability if ws.precipitation_probability is not None else 0.0),
        heat_index=float(ws.heat_index if ws.heat_index is not None else (ws.temperature or 0.0)),
        alerts=_core_alerts_to_rag(ws.alerts),
        forecast_summary=(ws.forecast_summary or "").strip(),
        timestamp=ws.timestamp,
    )
    rag_scenario = RAGDerivedScenario(
        event_type=derived_scenario.event_type,
        severity_level=derived_scenario.severity_level,
        trigger_reason=derived_scenario.trigger_reason,
        confidence_score=derived_scenario.confidence_score,
    )
    rag_risk = RAGRiskScores(
        load_stress=int(round(risk_scores.load_stress)),
        outage_likelihood=int(round(risk_scores.outage_likelihood)),
        restoration_difficulty=int(round(risk_scores.restoration_difficulty)),
        crew_urgency=int(round(risk_scores.crew_urgency)),
        public_safety_risk=int(round(risk_scores.public_safety_risk)),
    )
    return RiskAnalysisOutput(
        zip=rag_weather.zip,
        weather_snapshot=rag_weather,
        derived_scenario=rag_scenario,
        risk_scores=rag_risk,
        top_risk_driver=_top_risk_driver(risk_scores),
        rag_evidence=[],
    )
