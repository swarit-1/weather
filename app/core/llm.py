"""
LLM playbook generation module.

Uses OpenAI gpt-4o-mini to generate a structured Playbook from a ContextBundle.
Validates output with Pydantic. Retries once on validation failure.
"""

import json
import os

from openai import OpenAI

from app.retrieval.rag_schema import ContextBundle
from app.schemas.risk import Playbook


_PLAYBOOK_PROMPT = """\
You are an energy grid operations AI. Given the weather scenario, risk scores, \
and protocol excerpts below, produce an actionable playbook.

SCENARIO:
  event_type: {event_type}
  severity_level: {severity_level}
  trigger_reason: {trigger_reason}
  confidence_score: {confidence_score}

RISK SCORES:
  load_stress: {load_stress}
  outage_likelihood: {outage_likelihood}
  restoration_difficulty: {restoration_difficulty}
  crew_urgency: {crew_urgency}
  public_safety_risk: {public_safety_risk}

PROTOCOL EXCERPTS:
{rag_context}

Return ONLY a JSON object with this exact structure, no markdown, no commentary:
{{
  "summary": "<1-2 sentence overview>",
  "actions": [
    {{
      "role": "<grid_ops|field_ops|comms>",
      "action": "<what to do>",
      "priority": "<critical|high|medium|low>",
      "details": "<specific steps>"
    }}
  ],
  "estimated_duration": "<e.g. 2-4 hours>",
  "risk_mitigation_notes": "<key risk mitigation points>"
}}

Include 3-6 actions. Each action must have a different focus.
Do not include markdown formatting. Do not wrap in code blocks.
Return only the JSON object.
"""


def _build_rag_context(bundle: ContextBundle) -> str:
    """Format RAG snippets for the prompt."""
    all_snippets = bundle.general_snippets + bundle.role_specific_snippets
    seen_ids = set()
    parts = []
    for s in all_snippets:
        if s.id in seen_ids:
            continue
        seen_ids.add(s.id)
        parts.append(f"[{s.role_tag}] {s.title}\n{s.text.strip()}")
    return "\n\n---\n\n".join(parts) if parts else "(No protocol excerpts available.)"


def _parse_playbook(content: str) -> Playbook:
    """Parse LLM response into Playbook. Strips markdown fences if present."""
    text = content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    data = json.loads(text)
    return Playbook.model_validate(data)


def generate_playbook(context_bundle: ContextBundle) -> Playbook:
    """
    Generate a structured Playbook from a ContextBundle using gpt-4o-mini.
    Validates with Pydantic. Retries once if parsing/validation fails.
    """
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY") or ""
    if not api_key:
        raise ValueError("Set OPENAI_API_KEY or LLM_API_KEY in the environment")

    client = OpenAI(api_key=api_key)
    ds = context_bundle.derived_scenario
    rs = context_bundle.risk_scores

    prompt = _PLAYBOOK_PROMPT.format(
        event_type=ds.event_type,
        severity_level=ds.severity_level,
        trigger_reason=ds.trigger_reason,
        confidence_score=ds.confidence_score,
        load_stress=rs.load_stress,
        outage_likelihood=rs.outage_likelihood,
        restoration_difficulty=rs.restoration_difficulty,
        crew_urgency=rs.crew_urgency,
        public_safety_risk=rs.public_safety_risk,
        rag_context=_build_rag_context(context_bundle),
    )

    last_error = None
    for attempt in range(2):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500,
        )
        content = (response.choices[0].message.content or "").strip()
        try:
            return _parse_playbook(content)
        except (json.JSONDecodeError, Exception) as e:
            last_error = e

    raise ValueError(f"Playbook generation failed after 2 attempts: {last_error}")
