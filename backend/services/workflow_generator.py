from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from models.node import WorkflowNode
from models.workflow import Workflow
from services.gemini_client import GeminiClient, GeminiRateLimitError

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
    "debugger",
    "security_auditor",
    "optimizer",
    "sandbox_runner",
]

# ---------------------------------------------------------------------------
# Combined domain + workflow planning prompt (single Gemini call)
# ---------------------------------------------------------------------------
_COMBINED_PROMPT = """\
You are a workflow planning assistant for an AI agent runtime system.

Given the task description you must:
1. Classify the primary domain (e.g. "cybersecurity", "web development", "data science")
2. Identify the primary artifact type to produce (e.g. "Python module", "REST API")
3. Return a JSON array of workflow nodes

Each node MUST have exactly these fields:
  - "name"          : string — a short, descriptive label for the step
  - "agent_type"    : string — one of: {agent_types}
  - "metadata"      : object — MUST include "domain", "artifact_type", and "task"

Guidelines:
- Always start with a "planner" node to decompose the task.
- Include a "researcher" node when information gathering is required.
- Include one or more "coder" nodes to produce the artifact.
- Include a "reviewer" node to quality-check the artifact.
- End with an "evaluator" node to score the final result.
- Keep the sequence logical and minimal — avoid redundant nodes.
- Name each node after its role, not its action: "Planner", "Researcher",
  "Coder", "Reviewer", "Evaluator" (if there are multiple nodes of the same
  agent_type, number them, e.g. "Coder 2").

Respond in this exact format:
DOMAIN: <domain string>
ARTIFACT_TYPE: <artifact type string>
NODES:
<JSON array only — no markdown fences, no explanation>

Task: {task}
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
        Ask Gemini to plan a workflow for *task* in a single API call.

        Falls back to a sensible default workflow on any parsing failure
        so the runtime is never left without a usable plan.
        """
        try:
            prompt = _COMBINED_PROMPT.format(
                task=task,
                agent_types=", ".join(f'"{t}"' for t in _KNOWN_AGENT_TYPES),
            )
            raw = self._client.generate(
                prompt,
                temperature=0.2,
                max_output_tokens=1024,
            )
            domain = _parse_field(raw, "DOMAIN") or "general problem-solving"
            artifact_type = _parse_field(raw, "ARTIFACT_TYPE") or "solution"
            node_defs = self._parse_nodes(raw)
            logger.info(
                "WorkflowGenerator: domain=%r artifact_type=%r for task=%r",
                domain, artifact_type, task[:60],
            )
            workflow = self._build_workflow(
                node_defs, task=task, domain=domain, artifact_type=artifact_type
            )
            logger.info(
                "WorkflowGenerator: created %d-node workflow for task=%r",
                len(workflow.nodes),
                task[:60],
            )
            return workflow

        except GeminiRateLimitError as exc:
            logger.warning(
                "WorkflowGenerator: rate limited, using default workflow. Reason: %s",
                exc,
            )
            return self._default_workflow(task)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "WorkflowGenerator: falling back to default workflow. Reason: %s",
                exc,
            )
            return self._default_workflow(task)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_nodes(self, raw: str) -> List[Dict[str, Any]]:
        """Extract and parse the JSON array after the NODES: marker."""
        nodes_section = raw
        marker = re.search(r"^NODES:\s*", raw, re.IGNORECASE | re.MULTILINE)
        if marker:
            nodes_section = raw[marker.end() :]
        return self._parse_json(nodes_section)

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
            WorkflowNode(name="Planner",    agent_type="planner",    metadata=dict(base_meta)),
            WorkflowNode(name="Researcher", agent_type="researcher", metadata=dict(base_meta)),
            WorkflowNode(name="Coder",      agent_type="coder",      metadata=dict(base_meta)),
            WorkflowNode(name="Reviewer",   agent_type="reviewer",   metadata=dict(base_meta)),
            WorkflowNode(name="Evaluator",  agent_type="evaluator",  metadata=dict(base_meta)),
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
