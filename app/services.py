"""Risk analysis service orchestration."""

from datetime import datetime, timezone

from app.schemas import WeatherSnapshot, RiskAnalysisOutput
from app.trigger_engine import derive_scenario
from app.risk_engine import calculate_risk_scores
from app.rag import retrieve_snippets


def run_risk_analysis(snapshot: WeatherSnapshot) -> RiskAnalysisOutput:
    """Execute the full risk analysis pipeline."""

    scenario = derive_scenario(snapshot)
    risk_scores = calculate_risk_scores(snapshot, scenario)

    # Determine top risk driver
    scores_dict = risk_scores.model_dump()
    top_risk_driver = max(scores_dict, key=scores_dict.get)

    # Build RAG query and retrieve snippets
    query = (
        f"Risk mitigation guidance for {scenario.event_type} event "
        f"with risk scores {risk_scores}"
    )
    rag_snippets = retrieve_snippets(query, k=3)

    return RiskAnalysisOutput(
        scenario=scenario,
        risk_scores=risk_scores,
        top_risk_driver=top_risk_driver,
        rag_snippets=rag_snippets,
        timestamp=datetime.now(timezone.utc),
    )
