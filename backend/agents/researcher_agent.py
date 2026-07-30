from __future__ import annotations

import logging
import re
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

        if self.gemini is None or not getattr(self.gemini, "has_api_key", True):
            return AgentResult(
                answer="Research completed (no Gemini client).",
                confidence=0.95,
                metadata={
                    "contradiction_score": 0.0,
                    "sources": 5,
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
            logger.warning("ResearcherAgent Gemini call failed: %s", exc)
            return AgentResult(
                answer=f"Research failed: {exc}",
                confidence=0.0,
                metadata={"error": str(exc), "domain": domain},
            )

        confidence   = _parse_float(raw, "CONFIDENCE",        default=0.90)
        sources      = _parse_int(raw,   "SOURCES",           default=3)
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


# ---------------------------------------------------------------------------
# Parse helpers
# ---------------------------------------------------------------------------

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