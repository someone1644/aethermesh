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
# Prompt template — {domain} and {artifact_type} injected at call time
# ---------------------------------------------------------------------------
_SYSTEM_TEMPLATE = """\
You are a rigorous quality reviewer specialising in {domain}.
Your job is to critically assess the provided {artifact_type} and identify
any issues, gaps, or improvements needed — applying the standards of the {domain} field.

Respond in this exact format:
VERDICT: <APPROVE | REQUEST_CHANGES>
ISSUES:
- <specific issue 1, or "None" if there are no issues>
- <specific issue 2>
...
SUGGESTIONS:
- <actionable suggestion 1, or "None">
...
CONFIDENCE: <float between 0.0 and 1.0>

Rules:
- Apply {domain}-specific quality standards.
- APPROVE only when the artifact genuinely meets domain best practices.
- Be direct and specific — no vague feedback.
- Do NOT add any text outside the format above.
"""


class ReviewerAgent(BaseAgent):
    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
    ) -> None:
        super().__init__("reviewer", gemini_client)

    def run(
        self,
        node: WorkflowNode,
    ) -> AgentResult:
        artifact: str = node.metadata.get(
            "artifact", node.metadata.get("task", node.name)
        )
        domain: str = node.metadata.get("domain", "general problem-solving")
        artifact_type: str = node.metadata.get("artifact_type", "output")

        if self.gemini is None:
            return AgentResult(
                answer="Review completed (no Gemini client).",
                confidence=0.96,
                metadata={
                    "domain": domain,
                    "artifact_type": artifact_type,
                    "node_id": node.id,
                },
            )

        system = _SYSTEM_TEMPLATE.format(
            domain=domain,
            artifact_type=artifact_type,
        )
        prompt = (
            f"{system}\n\n"
            f"Artifact to review:\n{artifact}\n"
            f"Node metadata: {node.metadata}"
        )

        try:
            raw = self.gemini.generate(prompt, temperature=0.2)
        except Exception as exc:  # noqa: BLE001
            logger.warning("ReviewerAgent Gemini call failed: %s", exc)
            return AgentResult(
                answer=f"Review failed: {exc}",
                confidence=0.0,
                metadata={"error": str(exc), "domain": domain},
            )

        confidence = _parse_confidence(raw, default=0.92)
        verdict = _parse_verdict(raw)

        return AgentResult(
            answer=raw,
            confidence=confidence,
            metadata={
                "verdict": verdict,
                "domain": domain,
                "artifact_type": artifact_type,
                "node_id": node.id,
            },
        )


# ---------------------------------------------------------------------------
# Parse helpers
# ---------------------------------------------------------------------------

def _parse_confidence(text: str, *, default: float) -> float:
    m = re.search(r"CONFIDENCE:\s*([\d.]+)", text, re.IGNORECASE)
    if m:
        try:
            return max(0.0, min(1.0, float(m.group(1))))
        except ValueError:
            pass
    return default


def _parse_verdict(text: str) -> str:
    m = re.search(
        r"VERDICT:\s*(APPROVE|REQUEST_CHANGES)", text, re.IGNORECASE
    )
    return m.group(1).upper() if m else "UNKNOWN"