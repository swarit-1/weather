"""StormOps Console API — stateless, no DB."""

from fastapi import APIRouter, HTTPException, Query

from app.core.models import DerivedScenario, RiskScores, WeatherSnapshot
from app.core.risk_engine import compute_risk_scores
from app.core.trigger_engine import derive_scenario
from app.core.weather_service import fetch_live_weather
from app.core.rag_adapter import core_to_rag_risk_analysis_output
from app.retrieval import (
    retrieve_protocol_snippets_from_risk,
    set_rag_evidence_from_bundle,
)
from app.retrieval.pdf_to_embeddings import get_query_embedding, load_vector_store_from_json
from app.llm import run_playbook_decisions

router = APIRouter()


@router.get("/analyze")
async def analyze(
    zip: str = Query(..., description="ZIP code for weather and risk analysis"),
    include_decision: bool = Query(
        False,
        description="If true, run RAG retrieval and LLM agents to return action_plan and recommendations",
    ),
) -> dict:
    """
    Fetch live weather from NWS, derive scenario, compute risk scores.
    If include_decision=true: retrieve top-k playbook snippets, build context,
    run GridOps/FieldOps/Comms agents and aggregator, return action_plan and recommendations.
    """
    zip_code = zip.strip()
    if not zip_code:
        raise HTTPException(status_code=400, detail="ZIP code required")

    weather_snapshot: WeatherSnapshot = await fetch_live_weather(zip_code)
    derived_scenario: DerivedScenario = derive_scenario(weather_snapshot)
    risk_scores: RiskScores = compute_risk_scores(weather_snapshot, derived_scenario)

    out = {
        "weather_snapshot": weather_snapshot.model_dump(mode="json"),
        "derived_scenario": derived_scenario.model_dump(),
        "risk_scores": risk_scores.model_dump(),
    }

    if not include_decision:
        return out

    # Full pipeline: parametrize → retrieve top-k → build context → agents → decision
    try:
        ra = core_to_rag_risk_analysis_output(
            weather_snapshot, derived_scenario, risk_scores
        )
        store = load_vector_store_from_json()
        get_records = store.get_all_records
        embed = get_query_embedding

        bundle = retrieve_protocol_snippets_from_risk(
            ra,
            get_records,
            embed,
            top_k_general=4,
            top_k_per_role=3,
        )
        set_rag_evidence_from_bundle(ra, bundle, k_total=8)

        decisions = await run_playbook_decisions(
            bundle,
            playbook_context_max_chars=8000,
            use_role_specific_context=True,
        )

        out["rag_evidence"] = [s.model_dump() for s in ra.rag_evidence]
        out["action_plan"] = decisions.get("action_plan", "")
        out["recommendations"] = {
            "grid_ops": decisions.get("grid_ops_recommendation", ""),
            "field_ops": decisions.get("field_ops_recommendation", ""),
            "comms": decisions.get("comms_recommendation", ""),
        }
    except Exception as e:
        out["decision_error"] = str(e)
        out["action_plan"] = ""
        out["recommendations"] = {}

    return out
