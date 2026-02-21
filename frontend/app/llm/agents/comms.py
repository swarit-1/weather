"""Communications agent."""

from typing import Dict, Any

from app.llm.prompts import COMMS_PROMPT, format_prompt


class CommsAgent:
    """Agent for communications decisions."""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    async def run(
        self,
        weather_context: Dict[str, Any],
        scenarios: list,
        risk_scores: Dict[str, Any],
        playbook_context: str
    ) -> Dict[str, Any]:
        """Execute communications analysis; returns recommendation from LLM."""
        if not self.llm_client:
            return {"recommendation": "", "error": "No LLM client"}
        prompt = format_prompt(
            COMMS_PROMPT,
            weather=weather_context,
            scenarios=scenarios,
            risk_scores=risk_scores,
            playbook_context=playbook_context or "(No playbook context provided.)",
        )
        out = await self.llm_client.call(prompt, temperature=0.3)
        recommendation = out.get("content", "")
        if out.get("error"):
            return {"recommendation": recommendation, "error": out["error"]}
        return {"recommendation": recommendation}
