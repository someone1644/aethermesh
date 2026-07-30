from __future__ import annotations

import logging
import re
from typing import Optional

from agents.base_agent import BaseAgent
from agents.context_utils import excerpt, format_shared_context
from models.agent_result import AgentResult
from models.node import WorkflowNode
from services.gemini_client import GeminiClient, GeminiRateLimitError

logger = logging.getLogger(__name__)

_SYSTEM_TEMPLATE = """\
You are a senior expert planner with deep knowledge in {domain}.
Your job is to analyse the task below and produce a clear, actionable execution plan
suitable for a team of specialised AI agents working in the {domain} field.

Respond in this exact format:
PLAN: <one-sentence summary of the overall goal>
STEPS:
1. <first concrete action>
2. <second concrete action>
...
CONFIDENCE: <float between 0.0 and 1.0>

Rules:
- Be specific and actionable for the {domain} domain.
- Do NOT add any text outside the format above.
"""


class PlannerAgent(BaseAgent):
    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
    ) -> None:
        super().__init__("planner", gemini_client)

    def run(
        self,
        node: WorkflowNode,
    ) -> AgentResult:
        task: str = node.metadata.get("task", node.name)
        domain: str = node.metadata.get("domain", "general problem-solving")

        if self.gemini is None or not getattr(self.gemini, "has_api_key", True):
            return _local_plan(task, domain, node.id, rate_limited=False)

        system = _SYSTEM_TEMPLATE.format(domain=domain)
        prompt = (
            f"{system}\n\n"
            f"Task: {task}\n"
            f"Node metadata: {node.metadata}"
        )

        try:
            raw = self.gemini.generate(prompt, temperature=0.3)
        except GeminiRateLimitError as exc:
            logger.warning("PlannerAgent rate limited: %s", exc)
            return _local_plan(task, domain, node.id, rate_limited=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("PlannerAgent Gemini call failed: %s", exc)
            return _local_plan(task, domain, node.id, rate_limited=True)

        confidence = _parse_confidence(raw, default=0.85)
        return AgentResult(
            answer=raw,
            confidence=confidence,
            metadata={
                "domain": domain,
                "node_id": node.id,
            },
        )


def _local_plan(
    task: str,
    domain: str,
    node_id: str,
    *,
    rate_limited: bool,
) -> AgentResult:
    note = " (rate-limited fallback)" if rate_limited else ""
    answer = (
        f"PLAN: Execute the {domain} task{note}\n"
        "STEPS:\n"
        f"1. Analyse requirements for: {task}\n"
        "2. Gather context and constraints\n"
        "3. Produce the primary artifact\n"
        "4. Review and evaluate quality\n"
        "CONFIDENCE: 0.65"
    )
    return AgentResult(
        answer=answer,
        confidence=0.65,
        metadata={
            "domain": domain,
            "node_id": node_id,
            "rate_limited": rate_limited,
            "local_fallback": True,
        },
    )


def _parse_confidence(text: str, *, default: float) -> float:
    m = re.search(r"CONFIDENCE:\s*([\d.]+)", text)
    if m:
        try:
            v = float(m.group(1))
            return max(0.0, min(1.0, v))
        except ValueError:
            pass
    return default
