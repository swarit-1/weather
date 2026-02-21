"""Agent orchestration and execution."""

import asyncio
from typing import Dict, Any, List, Optional, Union

from app.llm.llm_client import LLMClient
from app.llm.agents.grid_ops import GridOpsAgent
from app.llm.agents.field_ops import FieldOpsAgent
from app.llm.agents.comms import CommsAgent
from app.llm.agents.aggregator import AggregatorAgent


class AgentOrchestrator:
    """Orchestrate execution of multiple LLM agents with playbook context."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
        self.grid_ops = GridOpsAgent(self.llm_client)
        self.field_ops = FieldOpsAgent(self.llm_client)
        self.comms = CommsAgent(self.llm_client)
        self.aggregator = AggregatorAgent(self.llm_client)

    async def run_agents(
        self,
        weather_context: Union[Dict[str, Any], str],
        scenarios: Union[List[str], str],
        risk_scores: Union[Dict[str, Any], str],
        playbook_context: str = "",
        playbook_context_per_agent: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Run GridOps, FieldOps, and Comms agents in parallel, then aggregate.

        Context window behavior:
        - If playbook_context_per_agent is provided (keys: grid_ops, field_ops, comms),
          each agent gets only the playbook text for its role (role-specific context window).
        - Otherwise, all agents share the same playbook_context (shared context window).
        """
        if playbook_context_per_agent:
            grid_ctx = playbook_context_per_agent.get("grid_ops") or playbook_context or "(No playbook context.)"
            field_ctx = playbook_context_per_agent.get("field_ops") or playbook_context or "(No playbook context.)"
            comms_ctx = playbook_context_per_agent.get("comms") or playbook_context or "(No playbook context.)"
        else:
            grid_ctx = field_ctx = comms_ctx = playbook_context or "(No playbook context provided.)"

        # Run role agents in parallel (each with its own or shared context)
        grid_result, field_result, comms_result = await asyncio.gather(
            self.grid_ops.run(weather_context, scenarios, risk_scores, grid_ctx),
            self.field_ops.run(weather_context, scenarios, risk_scores, field_ctx),
            self.comms.run(weather_context, scenarios, risk_scores, comms_ctx),
        )
        agent_recommendations = {
            "grid_ops": grid_result,
            "field_ops": field_result,
            "comms": comms_result,
        }
        agg_result = await self.aggregator.run(agent_recommendations)
        return {
            "grid_ops_recommendation": grid_result.get("recommendation", ""),
            "field_ops_recommendation": field_result.get("recommendation", ""),
            "comms_recommendation": comms_result.get("recommendation", ""),
            "action_plan": agg_result.get("action_plan", ""),
            "recommendations": agent_recommendations,
            "aggregator_error": agg_result.get("error"),
        }
