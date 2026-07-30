from __future__ import annotations

import logging
from typing import Optional

from agents.base_agent import BaseAgent
from agents.context_utils import excerpt, format_shared_context
from models.agent_result import AgentResult
from models.node import WorkflowNode

logger = logging.getLogger(__name__)


class CoderAgent(BaseAgent):
    """Produces artifacts locally from planner/researcher shared context."""

    def __init__(
        self,
        gemini_client: Optional[object] = None,
    ) -> None:
        super().__init__("coder", None)

    def run(
        self,
        node: WorkflowNode,
    ) -> AgentResult:
        task: str = node.metadata.get("task", node.name)
        domain: str = node.metadata.get("domain", "general problem-solving")
        artifact_type: str = node.metadata.get("artifact_type", "solution")
        shared = node.metadata.get("shared_context", {})
        context = node.metadata.get("context") or format_shared_context(shared)

        plan = excerpt(shared.get("planner", ""), max_chars=800)
        research = excerpt(shared.get("researcher", ""), max_chars=800)

        output_body = _build_artifact(
            task=task,
            domain=domain,
            artifact_type=artifact_type,
            plan=plan,
            research=research,
        )

        conf_score = round(min(0.96, max(0.68, 0.75 + (0.05 if plan else 0) + (0.05 if research else 0) + (0.06 if "```" in output_body else 0))), 2)

        raw = (
            f"ARTIFACT_TYPE: {artifact_type}\n"
            f"OUTPUT:\n{output_body}\n"
            "EXPLANATION: Generated locally from planner and researcher context. "
            f"Domain: {domain}.\n"
            f"CONFIDENCE: {conf_score:.2f}"
        )

        return AgentResult(
            answer=raw,
            confidence=conf_score,
            metadata={
                "domain": domain,
                "artifact_type": artifact_type,
                "node_id": node.id,
                "local_fallback": True,
            },
        )


def _build_artifact(
    *,
    task: str,
    domain: str,
    artifact_type: str,
    plan: str,
    research: str,
) -> str:
    sections = [
        f"# {artifact_type.title()} — {domain}",
        "",
        f"## Task\n{task}",
        "",
    ]
    if plan:
        sections.extend(["## Execution Plan", plan, ""])
    if research:
        sections.extend(["## Research Summary", research, ""])
    sections.extend([
        f"## Deliverable ({artifact_type})",
        _artifact_scaffold(domain, artifact_type, task),
    ])
    return "\n".join(sections)


def _artifact_scaffold(domain: str, artifact_type: str, task: str) -> str:
    lowered = artifact_type.lower()
    if "api" in lowered or "rest" in lowered:
        return (
            "```python\n"
            "# FastAPI scaffold — extend with business logic\n"
            "from fastapi import FastAPI\n\n"
            "app = FastAPI(title='Generated API')\n\n"
            "@app.get('/health')\n"
            "def health():\n"
            "    return {'status': 'ok'}\n"
            "```"
        )
    if "react" in lowered or "component" in lowered:
        return (
            "```tsx\n"
            "export function GeneratedComponent() {\n"
            f"  return <section>{task}</section>;\n"
            "}\n"
            "```"
        )
    return (
        f"A structured {artifact_type} outline for {domain}, covering requirements, "
        f"approach, and next steps for: {task}"
    )
