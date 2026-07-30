from __future__ import annotations

import logging
from typing import Optional

from agents.base_agent import BaseAgent
from models.agent_result import AgentResult
from models.node import WorkflowNode

logger = logging.getLogger(__name__)


class ReviewerAgent(BaseAgent):
    """Reviews artifacts locally using deterministic quality heuristics."""

    def __init__(
        self,
        gemini_client: Optional[object] = None,
    ) -> None:
        super().__init__("reviewer", None)

    def run(
        self,
        node: WorkflowNode,
    ) -> AgentResult:
        artifact: str = node.metadata.get(
            "artifact", node.metadata.get("task", node.name)
        )
        domain: str = node.metadata.get("domain", "general problem-solving")
        artifact_type: str = node.metadata.get("artifact_type", "output")

        issues = _check_artifact(artifact)
        verdict = "APPROVE" if len(issues) <= 1 else "REQUEST_CHANGES"
        issue_lines = "\n".join(f"- {issue}" for issue in issues) or "- None"
        suggestions = (
            "- None"
            if verdict == "APPROVE"
            else "- Expand sections marked as incomplete\n- Add domain-specific validation"
        )

        conf_score = round(max(0.60, 0.95 - (len(issues) * 0.12)), 2)

        raw = (
            f"VERDICT: {verdict}\n"
            f"ISSUES:\n{issue_lines}\n"
            f"SUGGESTIONS:\n{suggestions}\n"
            f"CONFIDENCE: {conf_score:.2f}"
        )

        return AgentResult(
            answer=raw,
            confidence=conf_score,
            metadata={
                "verdict": verdict,
                "score": conf_score,
                "domain": domain,
                "artifact_type": artifact_type,
                "node_id": node.id,
                "local_fallback": True,
            },
        )


def _check_artifact(artifact: str) -> list[str]:
    issues: list[str] = []
    text = (artifact or "").strip()
    if len(text) < 80:
        issues.append("Artifact is very short")
    if "## Task" not in text and "Task:" not in text:
        issues.append("Missing explicit task section")
    if "OUTPUT:" not in text and len(text) < 120:
        issues.append("Missing structured output block")
    if text.count("TODO") > 0:
        issues.append("Contains TODO placeholders")
    return issues
