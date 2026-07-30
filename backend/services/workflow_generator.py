from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from models.node import WorkflowNode
from models.workflow import Workflow
from services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Known agent types the runtime understands
# ---------------------------------------------------------------------------
_KNOWN_AGENT_TYPES = [
    "planner",
    "researcher",
    "coder",
    "reviewer",
    "evaluator",
]

# ---------------------------------------------------------------------------
# Domain detection prompt
# Used once per generate() call to classify the task before planning nodes.
# ---------------------------------------------------------------------------
_DOMAIN_PROMPT = """\
You are a task classifier. Given a task description, identify:
1. The primary domain (e.g. "cybersecurity", "web development", "data science",
   "software engineering", "devops", "machine learning", "content writing",
   "network engineering", "cloud infrastructure", "general problem-solving", etc.)
2. The primary artifact type the workflow should produce (e.g. "Python module",
   "penetration test report", "React component", "SQL schema", "CI/CD pipeline",
   "research summary", "threat model", "data pipeline", "REST API", etc.)

Respond in this exact format:
DOMAIN: <domain string>
ARTIFACT_TYPE: <artifact type string>

Rules:
- Be concise — one line each.
- Do NOT add any text outside the format above.

Task: {task}
"""

# ---------------------------------------------------------------------------
# Workflow planning prompt
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """\
You are a workflow planning assistant for an AI agent runtime system.

The task belongs to the domain: {domain}
The primary artifact to produce is: {artifact_type}

Given the task description you must return a JSON array of workflow nodes.
Each node MUST have exactly these fields:
  - "name"          : string — a short, descriptive label for the step
  - "agent_type"    : string — one of: {agent_types}
  - "metadata"      : object — MUST include "domain", "artifact_type", and "task";
                      add any other relevant key/value pairs for this step

Guidelines:
- Always start with a "planner" node to decompose the task.
- Include a "researcher" node when information gathering is required.
- Include one or more "coder" nodes to produce the {artifact_type}.
- Include a "reviewer" node to quality-check the {artifact_type}.
- End with an "evaluator" node to score the final result.
- Keep the sequence logical and minimal — avoid redundant nodes.
- Return ONLY the JSON array, no markdown fences, no explanation.

Example output:
[
  {{"name": "Plan task", "agent_type": "planner",
    "metadata": {{"domain": "{domain}", "artifact_type": "{artifact_type}", "task": "..."}}}},
  {{"name": "Research context", "agent_type": "researcher",
    "metadata": {{"domain": "{domain}", "artifact_type": "{artifact_type}", "task": "..."}}}},
  {{"name": "Produce {artifact_type}", "agent_type": "coder",
    "metadata": {{"domain": "{domain}", "artifact_type": "{artifact_type}", "task": "..."}}}},
  {{"name": "Review {artifact_type}", "agent_type": "reviewer",
    "metadata": {{"domain": "{domain}", "artifact_type": "{artifact_type}", "task": "..."}}}},
  {{"name": "Evaluate result", "agent_type": "evaluator",
    "metadata": {{"domain": "{domain}", "artifact_type": "{artifact_type}", "task": "..."}}}}
]
"""


class WorkflowGenerator:
    """
    Generates a :class:`~models.workflow.Workflow` from a plain-text task
    description by asking Gemini to:

    1. Classify the task domain and artifact type.
    2. Propose an ordered list of nodes, each with domain context embedded
       in ``metadata`` so that every agent can adapt its prompt accordingly.
    """

    def __init__(self, gemini_client: GeminiClient) -> None:
        self._client = gemini_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, task: str) -> Workflow:
        """
        Ask Gemini to plan a workflow for *task* and return a populated
        :class:`~models.workflow.Workflow` ready for the RuntimeEngine.

        Falls back to a sensible default workflow on any parsing failure
        so the runtime is never left without a usable plan.
        """
        try:
            domain, artifact_type = self._detect_domain(task)
            logger.info(
                "WorkflowGenerator: domain=%r artifact_type=%r for task=%r",
                domain, artifact_type, task[:60],
            )

            prompt = self._build_prompt(task, domain, artifact_type)
            raw = self._client.generate(
                prompt,
                temperature=0.2,
                max_output_tokens=1024,
            )
            node_defs = self._parse_json(raw)
            workflow = self._build_workflow(
                node_defs, task=task, domain=domain, artifact_type=artifact_type
            )
            logger.info(
                "WorkflowGenerator: created %d-node workflow for task=%r",
                len(workflow.nodes),
                task[:60],
            )
            return workflow

        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "WorkflowGenerator: falling back to default workflow. Reason: %s",
                exc,
            )
            return self._default_workflow(task)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_domain(self, task: str) -> tuple[str, str]:
        """
        Ask Gemini to classify the task and return (domain, artifact_type).
        Falls back to safe defaults if parsing fails.
        """
        prompt = _DOMAIN_PROMPT.format(task=task)
        try:
            raw = self._client.generate(prompt, temperature=0.1, max_output_tokens=64)
            domain = _parse_field(raw, "DOMAIN") or "general problem-solving"
            artifact_type = _parse_field(raw, "ARTIFACT_TYPE") or "solution"
            return domain, artifact_type
        except Exception as exc:  # noqa: BLE001
            logger.warning("WorkflowGenerator domain detection failed: %s", exc)
            return "general problem-solving", "solution"

    def _build_prompt(
        self, task: str, domain: str, artifact_type: str
    ) -> str:
        system = _SYSTEM_PROMPT.format(
            domain=domain,
            artifact_type=artifact_type,
            agent_types=", ".join(f'"{t}"' for t in _KNOWN_AGENT_TYPES),
        )
        return f"{system}\n\nTask: {task}"

    def _parse_json(self, raw: str) -> List[Dict[str, Any]]:
        """Extract and parse the JSON array from the model response."""
        cleaned = re.sub(r"```(?:json)?", "", raw).strip()

        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start == -1 or end == -1:
            raise ValueError("No JSON array found in model response.")

        data = json.loads(cleaned[start : end + 1])

        if not isinstance(data, list):
            raise TypeError("Expected a JSON array at top level.")

        return data

    def _build_workflow(
        self,
        node_defs: List[Dict[str, Any]],
        *,
        task: str,
        domain: str,
        artifact_type: str,
    ) -> Workflow:
        workflow = Workflow()
        previous_id: Optional[str] = None

        for raw_node in node_defs:
            agent_type: str = str(raw_node.get("agent_type", "planner"))
            name: str = str(raw_node.get("name", agent_type.capitalize()))
            node_meta: Dict[str, Any] = raw_node.get("metadata", {}) or {}

            if agent_type not in _KNOWN_AGENT_TYPES:
                logger.warning(
                    "WorkflowGenerator: unknown agent_type %r — skipping.",
                    agent_type,
                )
                continue

            # Always guarantee domain context is present in every node,
            # even if Gemini forgot to include it in the metadata object.
            metadata: Dict[str, Any] = {
                "domain": domain,
                "artifact_type": artifact_type,
                "task": task,
                **node_meta,  # node-specific fields override only if present
            }

            node = WorkflowNode(
                name=name,
                agent_type=agent_type,
                metadata=metadata,
            )
            workflow.add_node(node)

            if previous_id is not None:
                workflow.add_edge(previous_id, node.id)

            previous_id = node.id

        if not workflow.nodes:
            raise ValueError(
                "Gemini returned no valid nodes; triggering fallback."
            )

        return workflow

    @staticmethod
    def _default_workflow(task: str = "") -> Workflow:
        """Minimal safe workflow used when Gemini planning fails."""
        wf = Workflow()
        base_meta = {
            "domain": "general problem-solving",
            "artifact_type": "solution",
            "task": task,
        }
        nodes = [
            WorkflowNode(name="Plan task",          agent_type="planner",    metadata=dict(base_meta)),
            WorkflowNode(name="Research context",   agent_type="researcher", metadata=dict(base_meta)),
            WorkflowNode(name="Produce solution",   agent_type="coder",      metadata=dict(base_meta)),
            WorkflowNode(name="Review work",        agent_type="reviewer",   metadata=dict(base_meta)),
            WorkflowNode(name="Evaluate result",    agent_type="evaluator",  metadata=dict(base_meta)),
        ]
        prev: Optional[str] = None
        for node in nodes:
            wf.add_node(node)
            if prev:
                wf.add_edge(prev, node.id)
            prev = node.id
        return wf


# ---------------------------------------------------------------------------
# Parse helper
# ---------------------------------------------------------------------------

def _parse_field(text: str, key: str) -> Optional[str]:
    """Return the value of a ``KEY: value`` line, or None."""
    m = re.search(rf"^{key}:\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
    return m.group(1).strip() if m else None
