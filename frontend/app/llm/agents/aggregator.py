"""Aggregator agent for consolidating recommendations."""

from typing import Dict, Any, List

from app.llm.prompts import AGGREGATOR_PROMPT, format_prompt


class AggregatorAgent:
    """Agent for aggregating recommendations from other agents."""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    async def run(self, agent_recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate recommendations into a unified action plan."""
        if not self.llm_client:
            return {"action_plan": "", "error": "No LLM client"}
        grid_ops = agent_recommendations.get("grid_ops", {}).get("recommendation", "")
        field_ops = agent_recommendations.get("field_ops", {}).get("recommendation", "")
        comms = agent_recommendations.get("comms", {}).get("recommendation", "")
        prompt = format_prompt(
            AGGREGATOR_PROMPT,
            grid_ops_recommendation=grid_ops,
            field_ops_recommendation=field_ops,
            comms_recommendation=comms,
        )
        out = await self.llm_client.call(prompt, temperature=0.2)
        action_plan = out.get("content", "")
        if out.get("error"):
            return {"action_plan": action_plan, "error": out["error"]}
        return {"action_plan": action_plan}
