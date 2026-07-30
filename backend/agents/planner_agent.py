from __future__ import annotations

import logging
from typing import Optional

from agents.base_agent import BaseAgent
from models.agent_result import AgentResult
from models.node import WorkflowNode
from services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt template — {domain} injected at call time from node.metadata
# ---------------------------------------------------------------------------
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

        if self.gemini is None:
            return AgentResult(
                answer="Planning completed (no Gemini client).",
                confidence=1.0,
                metadata={
                    "domain": domain,
                    "node_id": node.id,
                },
            )

        system = _SYSTEM_TEMPLATE.format(domain=domain)
        prompt = (
            f"{system}\n\n"
            f"Task: {task}\n"
            f"Node metadata: {node.metadata}"
        )

        try:
            raw = self.gemini.generate(prompt, temperature=0.3)
        except Exception as exc:  # noqa: BLE001
            logger.warning("PlannerAgent Gemini call failed: %s", exc)
            return AgentResult(
                answer=f"Planning failed: {exc}",
                confidence=0.0,
                metadata={"error": str(exc), "domain": domain},
            )

        confidence = _parse_confidence(raw, default=0.85)

        return AgentResult(
            answer=raw,
            confidence=confidence,
            metadata={
                "domain": domain,
                "node_id": node.id,
            },
        )


def _parse_confidence(text: str, *, default: float) -> float:
    import re
    m = re.search(r"CONFIDENCE:\s*([\d.]+)", text)
    if m:
        try:
            v = float(m.group(1))
            return max(0.0, min(1.0, v))
        except ValueError:
            pass
    return default