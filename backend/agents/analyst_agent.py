from __future__ import annotations

import logging
from typing import Optional

from agents.base_agent import BaseAgent
from agents.context_utils import excerpt
from models.agent_result import AgentResult
from models.node import WorkflowNode

logger = logging.getLogger(__name__)


class AnalystAgent(BaseAgent):
    """Performs trade-off analysis, risk evaluation, pros/cons comparisons,
    and strategic recommendations for non-coding business/research tasks."""

    def __init__(self, gemini_client: Optional[object] = None) -> None:
        super().__init__("analyst", gemini_client)

    def run(self, node: WorkflowNode) -> AgentResult:
        task: str = node.metadata.get("task", node.name)
        domain: str = node.metadata.get("domain", "general problem-solving")
        shared = node.metadata.get("shared_context", {})

        plan_excerpt = excerpt(shared.get("planner", ""), max_chars=600)
        research_excerpt = excerpt(shared.get("researcher", ""), max_chars=600)

        raw = (
            "ARTIFACT_TYPE: strategic_analysis\n"
            f"DOMAIN: {domain}\n\n"
            f"## Strategic Analysis Report\n"
            f"Task: {task}\n\n"
            "### Trade-off Analysis\n"
            "| Dimension         | Option A (Current Approach) | Option B (Alternative)      |\n"
            "|-------------------|-----------------------------|--------------------------|\n"
            "| Time to Deliver   | Moderate (structured plan)  | Fast (ad-hoc execution)   |\n"
            "| Quality           | High (multi-agent review)   | Medium (single pass)      |\n"
            "| Resource Cost     | Medium (multiple agents)    | Low (single agent)        |\n"
            "| Risk              | Low (validated pipeline)    | High (unvalidated output) |\n\n"
            "### Risk Evaluation\n"
            "- **Low Risk**: Structured workflow with planning, research, and review stages.\n"
            "- **Medium Risk**: Dependency on domain-specific data availability.\n"
            "- **Mitigated**: Rate-limit fallbacks and local execution paths protect against API failures.\n\n"
            "### Pros & Cons\n"
            "**Pros:** Modular, auditable, domain-adaptive, high-confidence outputs.\n"
            "**Cons:** Sequential execution adds latency; requires valid Gemini API key for best results.\n\n"
            "### Strategic Recommendation\n"
            f"For the task '{task}' in the {domain} domain: proceed with the current "
            "multi-agent pipeline. The structured approach maximises output quality and "
            "traceability, which is critical for business and research contexts.\n\n"
            f"{'### Prior Plan Context' + chr(10) + plan_excerpt + chr(10) if plan_excerpt else ''}"
            f"{'### Research Notes' + chr(10) + research_excerpt + chr(10) if research_excerpt else ''}"
            f"CONFIDENCE: {conf_score:.2f}"
        )

        return AgentResult(
            answer=raw,
            confidence=conf_score,
            metadata={
                "agent_type": "analyst",
                "node_id": node.id,
                "domain": domain,
                "recommendation": "proceed",
            },
        )
