"""LLM client for playbook decisions (OpenAI-compatible API)."""

import os
from typing import Dict, Any, Optional

from app.config import LLM_API_KEY, LLM_MODEL


def _get_api_key() -> str:
    return os.getenv("OPENAI_API_KEY") or LLM_API_KEY or ""


def _get_model() -> str:
    return os.getenv("LLM_MODEL", LLM_MODEL or "gpt-4o-mini")


class LLMClient:
    """Client for LLM calls (OpenAI chat completions). Used by agents for playbook decisions."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or _get_api_key()
        self.model = model or _get_model()

    async def call(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Call LLM with a single prompt. Returns content and raw response.

        Args:
            prompt: Full prompt text (e.g. formatted with playbook_context).
            **kwargs: Optional temperature, max_tokens, etc.

        Returns:
            {"content": str, "raw": response} or {"content": "", "error": str} on failure.
        """
        if not self.api_key:
            return {"content": "", "error": "No API key (set OPENAI_API_KEY or LLM_API_KEY)"}
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)
            temperature = kwargs.get("temperature", 0.3)
            max_tokens = kwargs.get("max_tokens", 1024)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = (response.choices[0].message.content or "").strip()
            return {"content": content, "raw": response}
        except Exception as e:
            return {"content": "", "error": str(e)}

    async def call_with_json_mode(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Call LLM with JSON mode; returns parsed JSON when possible."""
        out = await self.call(prompt, max_tokens=2048)
        if out.get("error"):
            return out
        import json
        try:
            text = out["content"]
            if "```json" in text:
                text = text.split("```json", 1)[-1].split("```", 1)[0].strip()
            out["parsed"] = json.loads(text)
        except json.JSONDecodeError:
            out["parsed"] = None
        return out
