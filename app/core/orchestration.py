"""
Orchestration layer: WeatherSnapshot → full autonomous cycle → RunRecord.

Flow: simulation override → derive_scenario → compute_risk_scores →
      build RiskAnalysisOutput → retrieve RAG snippets → generate playbook → RunRecord.
"""

from copy import deepcopy
from datetime import datetime, timezone
from typing import Optional

from app.core.models import WeatherSnapshot, DerivedScenario, RiskScores
from app.core.trigger_engine import derive_scenario
from app.core.risk_engine import compute_risk_scores
from app.core.rag_adapter import core_to_rag_risk_analysis_output
from app.core.rag import retrieve_snippets, get_all_snippets
from app.core.llm import generate_playbook
from app.schemas.risk import RunRecord


SIMULATION_OVERRIDES = {
    "high_wind": {
        "wind_gust": 65.0,
        "wind_speed": 50.0,
    },
    "extreme_heat": {
        "heat_index": 115.0,
        "temperature": 108.0,
    },
}


def _apply_simulation(snapshot: WeatherSnapshot, simulate: str) -> WeatherSnapshot:
    """Return a copy of the snapshot with simulation overrides applied."""
    overrides = SIMULATION_OVERRIDES.get(simulate)
    if not overrides:
        raise ValueError(f"Unknown simulation: {simulate!r}. Options: {list(SIMULATION_OVERRIDES)}")
    data = snapshot.model_dump()
    data.update(overrides)
    return WeatherSnapshot.model_validate(data)


def _top_risk_driver(risk_scores: RiskScores) -> str:
    """Return the name of the highest risk score field."""
    fields = {
        "load_stress": float(risk_scores.load_stress),
        "outage_likelihood": float(risk_scores.outage_likelihood),
        "restoration_difficulty": float(risk_scores.restoration_difficulty),
        "crew_urgency": float(risk_scores.crew_urgency),
        "public_safety_risk": float(risk_scores.public_safety_risk),
    }
    return max(fields, key=fields.get)


def run_autonomous_cycle(
    snapshot: WeatherSnapshot,
    simulate: Optional[str] = None,
) -> RunRecord:
    """
    Execute the full autonomous analysis cycle.

    1. Apply simulation override (if present) to a copy of the snapshot
    2. Derive scenario (deterministic)
    3. Compute risk scores (deterministic)
    4. Build RiskAnalysisOutput and retrieve RAG snippets
    5. Generate LLM playbook
    6. Return RunRecord
    """
    working_snapshot = snapshot
    if simulate:
        working_snapshot = _apply_simulation(snapshot, simulate)

    scenario: DerivedScenario = derive_scenario(working_snapshot)
    risk_scores: RiskScores = compute_risk_scores(working_snapshot, scenario)

    ra = core_to_rag_risk_analysis_output(working_snapshot, scenario, risk_scores)

    bundle = retrieve_snippets(ra, top_k_general=4, top_k_per_role=3)
    all_snippets = get_all_snippets(bundle, k_total=8)

    playbook = generate_playbook(bundle)

    return RunRecord(
        timestamp=datetime.now(timezone.utc),
        zip_code=working_snapshot.zip_code or "unknown",
        weather_snapshot=working_snapshot.model_dump(mode="json"),
        derived_scenario=scenario.model_dump(),
        risk_scores=risk_scores.model_dump(),
        top_risk_driver=_top_risk_driver(risk_scores),
        rag_snippets=[s.model_dump() for s in all_snippets],
        playbook=playbook.model_dump(),
        simulation=simulate,
    )
