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
You are an objective quality evaluator specialising in {domain}.
Your job is to holistically score the final {artifact_type} produced by an agent workflow,
applying the quality standards of the {domain} field.

Respond in this exact format:
SCORE: <float between 0.0 (completely wrong/useless) and 1.0 (perfect)>
COMPLETENESS: <float between 0.0 and 1.0>
CORRECTNESS: <float between 0.0 and 1.0>
CLARITY: <float between 0.0 and 1.0>
FEEDBACK: <one concise paragraph with actionable observations for {domain}>
CONFIDENCE: <float between 0.0 and 1.0>

Rules:
- Apply {domain}-specific quality criteria when scoring.
- Be objective and evidence-based.
- Do NOT add any text outside the format above.
"""


class EvaluatorAgent(BaseAgent):
    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
    ) -> None:
        super().__init__("evaluator", gemini_client)

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
                answer="Evaluation completed (no Gemini client).",
                confidence=0.97,
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
            f"Output to evaluate:\n{artifact}\n"
            f"Node metadata: {node.metadata}"
        )

        try:
            raw = self.gemini.generate(prompt, temperature=0.1)
        except Exception as exc:  # noqa: BLE001
            logger.warning("EvaluatorAgent Gemini call failed: %s", exc)
            return AgentResult(
                answer=f"Evaluation failed: {exc}",
                confidence=0.0,
                metadata={"error": str(exc), "domain": domain},
            )

        parse_errors: list[str] = []

        score        = _parse_required_float(raw, "SCORE",        node.id, parse_errors)
        confidence   = _parse_required_float(raw, "CONFIDENCE",   node.id, parse_errors)
        completeness = _parse_required_float(raw, "COMPLETENESS", node.id, parse_errors)
        correctness  = _parse_required_float(raw, "CORRECTNESS",  node.id, parse_errors)
        clarity      = _parse_required_float(raw, "CLARITY",      node.id, parse_errors)

        return AgentResult(
            answer=raw,
            confidence=confidence if confidence is not None else 0.0,
            metadata={
                "score":         score,
                "completeness":  completeness,
                "correctness":   correctness,
                "clarity":       clarity,
                "domain":        domain,
                "artifact_type": artifact_type,
                "node_id":       node.id,
                "parse_errors":  parse_errors,
            },
        )


# ---------------------------------------------------------------------------
# Parse helpers
# ---------------------------------------------------------------------------

def _parse_float(text: str, key: str) -> Optional[float]:
    """
    Return the parsed float for *key* in *text*, or ``None`` if the key
    is absent or the value cannot be converted.
    """
    m = re.search(rf"{key}:\s*([\d.]+)", text, re.IGNORECASE)
    if m:
        try:
            return max(0.0, min(1.0, float(m.group(1))))
        except ValueError:
            pass
    return None


def _parse_required_float(
    text: str,
    key: str,
    node_id: str,
    errors: list[str],
) -> Optional[float]:
    """
    Like :func:`_parse_float` but appends a warning to *errors* and logs
    it when the key is missing so the caller has full visibility.
    """
    value = _parse_float(text, key)
    if value is None:
        msg = f"EvaluatorAgent: '{key}' not found in model response (node={node_id})"
        logger.warning(msg)
        errors.append(msg)
    return value