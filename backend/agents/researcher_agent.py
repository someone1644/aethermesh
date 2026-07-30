from __future__ import annotations

import logging
import re
from typing import Optional

from agents.base_agent import BaseAgent
from models.agent_result import AgentResult
from models.node import WorkflowNode
from services.gemini_client import GeminiClient, GeminiRateLimitError

logger = logging.getLogger(__name__)

_SYSTEM_TEMPLATE = """\
You are a research specialist with expertise in {domain}.
Your job is to gather, summarise, and critically assess available information
relevant to the task, specifically within the {domain} field.

Respond in this exact format:
SUMMARY: <concise summary of findings>
SOURCES: <integer — estimated number of relevant sources consulted>
CONTRADICTION_SCORE: <float between 0.0 (no contradictions) and 1.0 (highly contradictory)>
CONFIDENCE: <float between 0.0 and 1.0>

Rules:
- Be factual and precise.
- Tailor your research focus to the {domain} domain.
- Do NOT add any text outside the format above.
"""


class ResearcherAgent(BaseAgent):
    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
    ) -> None:
        super().__init__("researcher", gemini_client)

    def run(
        self,
        node: WorkflowNode,
    ) -> AgentResult:
        task: str = node.metadata.get("task", node.name)
        domain: str = node.metadata.get("domain", "general problem-solving")
        shared = node.metadata.get("shared_context", {})
        plan_context = shared.get("planner", "")

        if self.gemini is None or not getattr(self.gemini, "has_api_key", True):
            return _local_research(task, domain, node.id, plan_context, rate_limited=False)

        system = _SYSTEM_TEMPLATE.format(domain=domain)
        prompt = (
            f"{system}\n\n"
            f"Task: {task}\n"
            f"Prior plan:\n{plan_context}\n"
            f"Node metadata: {node.metadata}"
        )

        try:
            raw = self.gemini.generate(prompt, temperature=0.3)
        except GeminiRateLimitError as exc:
            logger.warning("ResearcherAgent rate limited: %s", exc)
            return _local_research(task, domain, node.id, plan_context, rate_limited=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("ResearcherAgent Gemini call failed: %s", exc)
            return _local_research(task, domain, node.id, plan_context, rate_limited=True)

        confidence = _parse_float(raw, "CONFIDENCE", default=0.90)
        sources = _parse_int(raw, "SOURCES", default=3)
        contradiction = _parse_float(raw, "CONTRADICTION_SCORE", default=0.0)

        return AgentResult(
            answer=raw,
            confidence=confidence,
            metadata={
                "contradiction_score": contradiction,
                "sources": sources,
                "domain": domain,
                "node_id": node.id,
            },
        )


def _local_research(
    task: str,
    domain: str,
    node_id: str,
    plan_context: str,
    *,
    rate_limited: bool,
) -> AgentResult:
    note = " Rate-limited — using task description and prior plan only." if rate_limited else ""
    summary = (
        f"Task scoped to {domain}: {task}."
        if not plan_context
        else f"Aligned with prior plan for {domain}. Key focus: {task}."
    )
    answer = (
        f"SUMMARY: {summary}{note}\n"
        "SOURCES: 1\n"
        "CONTRADICTION_SCORE: 0.0\n"
        "CONFIDENCE: 0.60"
    )
    return AgentResult(
        answer=answer,
        confidence=0.60,
        metadata={
            "contradiction_score": 0.0,
            "sources": 1,
            "domain": domain,
            "node_id": node_id,
            "rate_limited": rate_limited,
            "local_fallback": True,
        },
    )


def _parse_float(text: str, key: str, *, default: float) -> float:
    m = re.search(rf"{key}:\s*([\d.]+)", text, re.IGNORECASE)
    if m:
        try:
            return max(0.0, min(1.0, float(m.group(1))))
        except ValueError:
            pass
    return default


def _parse_int(text: str, key: str, *, default: int) -> int:
    m = re.search(rf"{key}:\s*(\d+)", text, re.IGNORECASE)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    return default
