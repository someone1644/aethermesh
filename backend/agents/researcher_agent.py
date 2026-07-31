from __future__ import annotations

import logging
from typing import Optional

from agents.base_agent import BaseAgent
from agents.context_utils import (
    excerpt, parse_field, parse_float, parse_int, parse_list_field,
)
from models.agent_result import AgentResult
from models.node import WorkflowNode
from services.gemini_client import GeminiClient, GeminiRateLimitError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt — Domain Research Specialist
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """\
ROLE
You are AetherMesh's Domain Research Specialist. You receive a task and a prior \
execution plan, then systematically surface what is known, assumed, unknown, \
contradicted, and missing — scoped strictly to the given domain.

INPUTS
- task: the user-supplied task description
- domain: the domain classification from the planner
- prior_plan: structured output from PlannerAgent (may be empty)

RESPONSIBILITIES
1. Summarise the most relevant factual knowledge for accomplishing the task in this domain.
2. Distinguish verified facts from unverifiable assumptions.
3. Identify concrete unknowns that cannot be resolved without additional information.
4. Surface any conflicting evidence or contradictory domain knowledge.
5. Flag information that is missing but required to complete the task confidently.
6. Estimate how many authoritative sources support the findings.
7. Return a confidence score reflecting overall research certainty, not task difficulty.

BOUNDARIES
- Do NOT produce code, plans, or implementation artifacts.
- Do NOT repeat the prior plan verbatim — reference it, don't copy it.
- Do NOT fabricate numbers, statistics, or citations.
- Unknowns must be genuinely unknown, not just difficult to answer.
- Conflicting evidence must describe a real tension, not a minor disagreement.

EXPECTED OUTPUT FORMAT — return exactly this, nothing else:
SUMMARY: <concise 2-3 sentence research summary>
FACTS:
- <verified fact 1>
- <verified fact 2>
ASSUMPTIONS:
- <assumption 1 — label why it is an assumption>
UNKNOWNS:
- <unknown 1 — what information is missing and why it matters>
CONFLICTING_EVIDENCE:
- <conflict 1 — describe the tension> (or "- None" if absent)
MISSING_INFORMATION:
- <what additional data would improve confidence>
SOURCES: <integer — estimated number of authoritative sources>
CONTRADICTION_SCORE: <float 0.0-1.0 — 0 means no contradictions>
CONFIDENCE: <float 0.0-1.0>

WHAT NOT TO DO
- Do not produce bullet lists for SUMMARY — it must be prose.
- Do not fabricate specific URLs, author names, or paper titles.
- Do not produce more than 6 bullets per section.
- Do not restate the task as a finding.
"""


class ResearcherAgent(BaseAgent):
    """Domain research specialist: surfaces facts, assumptions, unknowns, conflicts."""

    def __init__(self, gemini_client: Optional[GeminiClient] = None) -> None:
        super().__init__("researcher", gemini_client)

    def run(self, node: WorkflowNode) -> AgentResult:
        task: str = node.metadata.get("task", node.name)
        domain: str = node.metadata.get("domain", "general problem-solving")
        shared = node.metadata.get("shared_context", {})
        prior_plan = excerpt(shared.get("planner", ""), max_chars=800)

        if self.gemini is None or not getattr(self.gemini, "has_api_key", True):
            return _local_research(task, domain, node.id, rate_limited=False)

        prompt = (
            f"{_SYSTEM_PROMPT}\n\n"
            f"task: {task}\n"
            f"domain: {domain}\n"
            f"prior_plan:\n{prior_plan or '(not available)'}\n"
        )

        try:
            raw = self.gemini.generate(prompt, temperature=0.25)
        except GeminiRateLimitError as exc:
            logger.warning("ResearcherAgent rate limited: %s", exc)
            return _local_research(task, domain, node.id, rate_limited=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("ResearcherAgent Gemini call failed: %s", exc)
            return _local_research(task, domain, node.id, rate_limited=True)

        confidence = parse_float(raw, "CONFIDENCE", default=0.80)
        sources = parse_int(raw, "SOURCES", default=3)
        contradiction = parse_float(raw, "CONTRADICTION_SCORE", default=0.1)

        return AgentResult(
            answer=raw,
            confidence=confidence,
            metadata={
                "node_id": node.id,
                "domain": domain,
                "sources": sources,
                "contradiction_score": contradiction,
                "facts": parse_list_field(raw, "FACTS"),
                "assumptions": parse_list_field(raw, "ASSUMPTIONS"),
                "unknowns": parse_list_field(raw, "UNKNOWNS"),
                "conflicting_evidence": parse_list_field(raw, "CONFLICTING_EVIDENCE"),
                "missing_information": parse_list_field(raw, "MISSING_INFORMATION"),
            },
        )


# ---------------------------------------------------------------------------
# Local deterministic fallback
# ---------------------------------------------------------------------------

def _local_research(
    task: str,
    domain: str,
    node_id: str,
    *,
    rate_limited: bool,
) -> AgentResult:
    note = " Rate-limited — using task description and domain context only." if rate_limited else ""
    raw = (
        f"SUMMARY: Research conducted for {domain} task: {task}.{note} "
        "Findings are based on domain knowledge without live source retrieval.\n"
        "FACTS:\n"
        f"- The task pertains to the {domain} domain.\n"
        "- Structured multi-agent workflows improve output quality through specialisation.\n"
        "ASSUMPTIONS:\n"
        "- Assumed the task description is complete and unambiguous.\n"
        "- Assumed no access restrictions on domain-specific knowledge.\n"
        "UNKNOWNS:\n"
        "- Specific constraints or edge cases not stated in the task description.\n"
        "- Availability of domain-specific datasets or tools.\n"
        "CONFLICTING_EVIDENCE:\n"
        "- None\n"
        "MISSING_INFORMATION:\n"
        "- Detailed requirements, acceptance criteria, and target audience.\n"
        "SOURCES: 1\n"
        "CONTRADICTION_SCORE: 0.0\n"
        "CONFIDENCE: 0.58"
    )
    return AgentResult(
        answer=raw,
        confidence=0.58,
        metadata={
            "node_id": node_id,
            "domain": domain,
            "sources": 1,
            "contradiction_score": 0.0,
            "facts": [f"The task pertains to the {domain} domain."],
            "assumptions": ["Task description is complete and unambiguous."],
            "unknowns": ["Specific constraints or edge cases not stated."],
            "conflicting_evidence": [],
            "missing_information": ["Detailed requirements and acceptance criteria."],
            "rate_limited": rate_limited,
            "local_fallback": True,
        },
    )
