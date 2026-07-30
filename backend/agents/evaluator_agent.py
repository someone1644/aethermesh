from __future__ import annotations

import logging
from typing import Optional

from agents.base_agent import BaseAgent
from models.agent_result import AgentResult
from models.node import WorkflowNode

logger = logging.getLogger(__name__)


class EvaluatorAgent(BaseAgent):
    """Scores artifacts locally using heuristic metrics."""

    def __init__(
        self,
        gemini_client: Optional[object] = None,
    ) -> None:
        super().__init__("evaluator", None)

    def run(
        self,
        node: WorkflowNode,
    ) -> AgentResult:
        artifact: str = node.metadata.get(
            "artifact", node.metadata.get("task", node.name)
        )
        domain: str = node.metadata.get("domain", "general problem-solving")
        artifact_type: str = node.metadata.get("artifact_type", "output")
        shared = node.metadata.get("shared_context", {})

        score, completeness, correctness, clarity = _score_artifact(
            artifact, shared
        )

        raw = (
            f"SCORE: {score:.2f}\n"
            f"COMPLETENESS: {completeness:.2f}\n"
            f"CORRECTNESS: {correctness:.2f}\n"
            f"CLARITY: {clarity:.2f}\n"
            f"FEEDBACK: Local evaluation for {domain} {artifact_type}. "
            "Scores reflect structure, length, and use of shared planner/research context.\n"
            f"CONFIDENCE: {score:.2f}"
        )

        return AgentResult(
            answer=raw,
            confidence=score,
            metadata={
                "score": score,
                "completeness": completeness,
                "correctness": correctness,
                "clarity": clarity,
                "domain": domain,
                "artifact_type": artifact_type,
                "node_id": node.id,
                "local_fallback": True,
            },
        )


def _score_artifact(
    artifact: str,
    shared: dict,
) -> tuple[float, float, float, float]:
    text = (artifact or "").strip()
    
    # 1. Base length & specificity metric (longer, detailed artifacts score higher)
    char_len = len(text)
    length_score = min(1.0, max(0.40, char_len / 750.0))

    # 2. Upstream agent synergy bonus (rewards multi-agent execution)
    active_agents = len([k for k, v in shared.items() if v])
    synergy_score = min(1.0, 0.40 + (active_agents * 0.12))

    # 3. Domain artifact detection (code blocks, audits, or structured tables)
    has_code = 1.0 if "```" in text else 0.65
    has_structure = 1.0 if ("##" in text or "OUTPUT:" in text or "|" in text) else 0.50

    completeness = round(min(1.0, (length_score * 0.5) + (synergy_score * 0.5)), 2)
    correctness = round(min(1.0, (has_code * 0.6) + (0.4 if "TODO" not in text else 0.1)), 2)
    clarity = round(min(1.0, (has_structure * 0.7) + (0.3 if char_len > 150 else 0.1)), 2)

    score = round((completeness * 0.4) + (correctness * 0.3) + (clarity * 0.3), 2)
    return score, completeness, correctness, clarity
