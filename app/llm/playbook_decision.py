"""
Bridge: retrieved context (ContextBundle) → LLM agents → playbook decisions.

Use this after retrieval has produced a ContextBundle (e.g. from
retrieve_protocol_snippets_from_risk). This module builds the playbook_context
string and weather/scenario/risk summaries, then runs the agent orchestrator.
"""

import json
from typing import Dict, Any, Optional

from app.retrieval.rag_schema import ContextBundle
from app.retrieval.protocol_retrieval import (
    context_bundle_to_playbook_context,
    context_bundle_to_playbook_context_per_role,
)
from app.llm.llm_client import LLMClient
from app.llm.orchestration import AgentOrchestrator


def _bundle_to_weather_context(bundle: ContextBundle) -> Dict[str, Any]:
    """Summarize weather_snapshot for LLM prompts."""
    ws = bundle.weather_snapshot
    return {
        "zip": ws.zip,
        "temperature": ws.temperature,
        "wind_speed": ws.wind_speed,
        "wind_gust": ws.wind_gust,
        "heat_index": ws.heat_index,
        "precipitation_probability": ws.precipitation_probability,
        "forecast_summary": ws.forecast_summary,
        "alerts_count": len(ws.alerts),
        "alerts": [{"event": a.event, "headline": a.headline} for a in ws.alerts[:5]],
    }


def _bundle_to_scenarios(bundle: ContextBundle) -> list:
    """Derive scenario summary for LLM prompts."""
    ds = bundle.derived_scenario
    return [
        f"{ds.event_type} (severity: {ds.severity_level})",
        ds.trigger_reason,
        f"confidence: {ds.confidence_score:.0%}",
    ]


def _bundle_to_risk_scores(bundle: ContextBundle) -> Dict[str, Any]:
    """Risk scores for LLM prompts."""
    rs = bundle.risk_scores
    return {
        "load_stress": rs.load_stress,
        "outage_likelihood": rs.outage_likelihood,
        "restoration_difficulty": rs.restoration_difficulty,
        "crew_urgency": rs.crew_urgency,
        "public_safety_risk": rs.public_safety_risk,
    }


async def run_playbook_decisions(
    bundle: ContextBundle,
    llm_client: Optional[LLMClient] = None,
    playbook_context_max_chars: Optional[int] = 8000,
    use_role_specific_context: bool = True,
) -> Dict[str, Any]:
    """
    Bridge from retrieved ContextBundle to LLM playbook decisions.

    Context windows:
    - use_role_specific_context=True (default): Each agent gets a context window
      tailored to its role (GridOps only grid_ops + general snippets, FieldOps
      only field_ops + general, Comms only comms + general). Matches each agent's
      decision-making task.
    - use_role_specific_context=False: All agents share the same merged
      playbook context (general + role_specific combined).

    Steps:
    1. Build playbook context (per-role or shared) from bundle's RAG snippets.
    2. Build weather_context, scenarios, risk_scores from bundle.
    3. Run GridOps, FieldOps, Comms agents, then Aggregator.
    4. Return action_plan and per-role recommendations.
    """
    weather_context = _bundle_to_weather_context(bundle)
    scenarios = _bundle_to_scenarios(bundle)
    risk_scores = _bundle_to_risk_scores(bundle)

    weather_str = json.dumps(weather_context, indent=2)
    scenarios_str = "\n".join(str(s) for s in scenarios)
    risk_str = json.dumps(risk_scores, indent=2)

    if use_role_specific_context:
        playbook_per_agent = context_bundle_to_playbook_context_per_role(
            bundle, max_chars_per_role=playbook_context_max_chars or 6000
        )
        playbook_context = ""
    else:
        playbook_per_agent = None
        playbook_context = context_bundle_to_playbook_context(
            bundle, max_chars=playbook_context_max_chars
        )

    orchestrator = AgentOrchestrator(llm_client=llm_client or LLMClient())
    return await orchestrator.run_agents(
        weather_context=weather_str,
        scenarios=scenarios_str,
        risk_scores=risk_str,
        playbook_context=playbook_context,
        playbook_context_per_agent=playbook_per_agent,
    )
