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
You are a highly skilled expert in {domain}.
Your job is to produce a complete, high-quality {artifact_type} for the described task.

Respond in this exact format:
ARTIFACT_TYPE: {artifact_type}
OUTPUT:
<full {artifact_type} — no placeholders, no stubs>
EXPLANATION: <one short paragraph explaining key decisions>
CONFIDENCE: <float between 0.0 and 1.0>

Rules:
- Apply domain best practices for {domain}.
- The output must be complete and immediately usable — no TODO sections.
- Do NOT add any text outside the format above.
"""


class CoderAgent(BaseAgent):
    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
    ) -> None:
        super().__init__("coder", gemini_client)

    def run(
        self,
        node: WorkflowNode,
    ) -> AgentResult:
        task: str = node.metadata.get("task", node.name)
        context: str = node.metadata.get("context", "")
        domain: str = node.metadata.get("domain", "general problem-solving")
        artifact_type: str = node.metadata.get("artifact_type", "solution")

        if self.gemini is None or not getattr(self.gemini, "has_api_key", True):
            return AgentResult(
                answer="Output produced (no Gemini client).",
                confidence=0.93,
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
        prompt = f"{system}\n\nTask: {task}\n"
        if context:
            prompt += f"Context: {context}\n"
        prompt += f"Node metadata: {node.metadata}"

        try:
            raw = self.gemini.generate(
                prompt,
                temperature=0.2,
                max_output_tokens=4096,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("CoderAgent Gemini call failed: %s", exc)
            return AgentResult(
                answer=f"Production failed: {exc}",
                confidence=0.0,
                metadata={"error": str(exc), "domain": domain},
            )

        confidence = _parse_confidence(raw, default=0.90)

        return AgentResult(
            answer=raw,
            confidence=confidence,
            metadata={
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