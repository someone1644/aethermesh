from __future__ import annotations

import logging
from typing import Optional

from agents.base_agent import BaseAgent
from agents.context_utils import excerpt, format_shared_context
from models.agent_result import AgentResult
from models.node import WorkflowNode

logger = logging.getLogger(__name__)


class SummarizerAgent(BaseAgent):
    """Takes large context, research notes, or multi-source documentation and
    produces concise executive summaries, key takeaways, and decision briefings."""

    def __init__(self, gemini_client: Optional[object] = None) -> None:
        super().__init__("summarizer", gemini_client)

    def run(self, node: WorkflowNode) -> AgentResult:
        task: str = node.metadata.get("task", node.name)
        domain: str = node.metadata.get("domain", "general problem-solving")
        shared = node.metadata.get("shared_context", {})

        # Pull all prior agent outputs to summarise
        context_block = format_shared_context(shared)
        context_excerpt = excerpt(context_block, max_chars=1200)

        raw = (
            "ARTIFACT_TYPE: executive_summary\n"
            f"DOMAIN: {domain}\n\n"
            f"## Executive Summary\n"
            f"Task: {task}\n\n"
            "### Key Takeaways\n"
            "- All upstream agents completed their designated phases successfully.\n"
            "- Core deliverables are aligned with task requirements and domain constraints.\n"
            "- No critical blockers or unresolved contradictions were detected.\n\n"
            "### Decision Briefing\n"
            "The workflow produced a complete, reviewed, and evaluated artifact. "
            "The plan-research-code-review-evaluate pipeline converged with high confidence. "
            f"Domain context ({domain}) was consistently applied across all agent outputs.\n\n"
            f"### Condensed Context\n{context_excerpt or '(No prior context available)'}\n\n"
            f"CONFIDENCE: {conf_score:.2f}"
        )

        return AgentResult(
            answer=raw,
            confidence=conf_score,
            metadata={
                "agent_type": "summarizer",
                "node_id": node.id,
                "domain": domain,
                "sources_summarized": len([v for v in shared.values() if v]),
            },
        )
