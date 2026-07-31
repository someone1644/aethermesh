from __future__ import annotations

import logging
from typing import Optional

from agents.base_agent import BaseAgent
from agents.context_utils import (
    excerpt, parse_bool, parse_csv_field, parse_field,
    parse_float, parse_int, parse_list_field,
)
from models.agent_result import AgentResult
from models.node import WorkflowNode
from services.gemini_client import GeminiClient, GeminiRateLimitError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt — Orchestration Intelligence
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """\
ROLE
You are AetherMesh's Orchestration Intelligence — the first agent to execute in every \
workflow. Your sole responsibility is to decompose a task and produce structured planning \
metadata that downstream agents depend on. You do not execute tasks yourself.

INPUTS
- task: the raw user-supplied task description
- domain_hint: optional domain hint from node metadata (may be empty)

RESPONSIBILITIES
1. Identify the primary domain (e.g. "cybersecurity", "web development", "data science", \
"business strategy", "education", "AI/ML", "research", "creative writing").
2. Classify the task type: one of [coding, research, analysis, writing, design, mixed].
3. Estimate complexity: one of [low, medium, high, expert].
4. Determine whether code production is strictly required.
5. Determine whether external research/factual grounding is needed.
6. List which agents are REQUIRED for this workflow (from the set: \
planner, researcher, coder, reviewer, evaluator, debugger, \
security_auditor, optimizer, sandbox_runner, summarizer, analyst, critic).
7. List which agents are OPTIONAL (would add value but are not mandatory).
8. Estimate the number of execution steps.
9. Output a concise deterministic execution plan.

BOUNDARIES
- Do NOT produce code, prose artifacts, or research findings.
- Do NOT suggest agents outside the known registry.
- Do NOT include agents that are irrelevant to the task type.
- Required and optional agent lists must be non-overlapping.

EXPECTED OUTPUT FORMAT — return exactly this, nothing else:
PLAN: <one-sentence summary of the overall goal>
DOMAIN: <detected domain>
TASK_TYPE: <coding|research|analysis|writing|design|mixed>
COMPLEXITY: <low|medium|high|expert>
REQUIRES_CODE: <true|false>
REQUIRES_RESEARCH: <true|false>
REQUIRED_AGENTS: <comma-separated agent names>
OPTIONAL_AGENTS: <comma-separated agent names>
ESTIMATED_STEPS: <integer>
STEPS:
1. <first concrete action>
2. <second concrete action>
...
CONFIDENCE: <float 0.0-1.0>

WHAT NOT TO DO
- Do not produce markdown headers or fences outside of STEPS.
- Do not explain your reasoning outside the format.
- Do not repeat the task verbatim as the plan.
- Do not list more than 8 steps.
"""


class PlannerAgent(BaseAgent):
    """Orchestration intelligence: decomposes tasks and emits structured workflow metadata."""

    def __init__(self, gemini_client: Optional[GeminiClient] = None) -> None:
        super().__init__("planner", gemini_client)

    def run(self, node: WorkflowNode) -> AgentResult:
        task: str = node.metadata.get("task", node.name)
        domain_hint: str = node.metadata.get("domain", "")

        if self.gemini is None or not getattr(self.gemini, "has_api_key", True):
            return _local_plan(task, domain_hint, node.id, rate_limited=False)

        prompt = (
            f"{_SYSTEM_PROMPT}\n\n"
            f"task: {task}\n"
            f"domain_hint: {domain_hint or '(none)'}\n"
        )

        try:
            raw = self.gemini.generate(prompt, temperature=0.2)
        except GeminiRateLimitError as exc:
            logger.warning("PlannerAgent rate limited: %s", exc)
            return _local_plan(task, domain_hint, node.id, rate_limited=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("PlannerAgent Gemini call failed: %s", exc)
            return _local_plan(task, domain_hint, node.id, rate_limited=True)

        return _build_result(raw, node.id)


# ---------------------------------------------------------------------------
# Result builder (shared by Gemini path and local fallback)
# ---------------------------------------------------------------------------

def _build_result(raw: str, node_id: str) -> AgentResult:
    confidence = parse_float(raw, "CONFIDENCE", default=0.80)
    return AgentResult(
        answer=raw,
        confidence=confidence,
        metadata={
            "node_id": node_id,
            "domain": parse_field(raw, "DOMAIN", default="general problem-solving"),
            "task_type": parse_field(raw, "TASK_TYPE", default="mixed"),
            "complexity": parse_field(raw, "COMPLEXITY", default="medium"),
            "requires_code": parse_bool(raw, "REQUIRES_CODE", default=False),
            "requires_research": parse_bool(raw, "REQUIRES_RESEARCH", default=True),
            "required_agents": parse_csv_field(raw, "REQUIRED_AGENTS"),
            "optional_agents": parse_csv_field(raw, "OPTIONAL_AGENTS"),
            "estimated_steps": parse_int(raw, "ESTIMATED_STEPS", default=4),
            "confidence": confidence,
        },
    )


# ---------------------------------------------------------------------------
# Local deterministic fallback
# ---------------------------------------------------------------------------

def _local_plan(
    task: str,
    domain_hint: str,
    node_id: str,
    *,
    rate_limited: bool,
) -> AgentResult:
    domain = domain_hint or "general problem-solving"
    note = " (rate-limited fallback)" if rate_limited else " (local fallback)"
    raw = (
        f"PLAN: Decompose and execute the task — {task}{note}\n"
        f"DOMAIN: {domain}\n"
        "TASK_TYPE: mixed\n"
        "COMPLEXITY: medium\n"
        "REQUIRES_CODE: false\n"
        "REQUIRES_RESEARCH: true\n"
        "REQUIRED_AGENTS: planner, researcher, coder, reviewer, evaluator\n"
        "OPTIONAL_AGENTS: summarizer, analyst\n"
        "ESTIMATED_STEPS: 5\n"
        "STEPS:\n"
        f"1. Analyse requirements for: {task}\n"
        "2. Gather domain-specific context and constraints\n"
        "3. Produce the primary artifact\n"
        "4. Review the artifact for quality and correctness\n"
        "5. Evaluate and score the final output\n"
        "CONFIDENCE: 0.65"
    )
    return AgentResult(
        answer=raw,
        confidence=0.65,
        metadata={
            "node_id": node_id,
            "domain": domain,
            "task_type": "mixed",
            "complexity": "medium",
            "requires_code": False,
            "requires_research": True,
            "required_agents": ["planner", "researcher", "coder", "reviewer", "evaluator"],
            "optional_agents": ["summarizer", "analyst"],
            "estimated_steps": 5,
            "confidence": 0.65,
            "rate_limited": rate_limited,
            "local_fallback": True,
        },
    )
