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
            "CONFIDENCE: 0.80"
        )

        return AgentResult(
            answer=raw,
            confidence=0.80,
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
    length_score = min(1.0, len(text) / 400.0)
    has_plan = bool(shared.get("planner"))
    has_research = bool(shared.get("researcher"))
    context_bonus = 0.1 * int(has_plan) + 0.1 * int(has_research)

    completeness = min(1.0, length_score * 0.7 + context_bonus + 0.1)
    correctness = 0.75 if "TODO" not in text else 0.45
    clarity = 0.80 if ("##" in text or "OUTPUT:" in text) else 0.55
    score = round((completeness + correctness + clarity) / 3.0, 2)
    return score, round(completeness, 2), round(correctness, 2), round(clarity, 2)
