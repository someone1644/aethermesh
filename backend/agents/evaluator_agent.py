from __future__ import annotations

import logging
from typing import Optional

from agents.base_agent import BaseAgent
from agents.context_utils import excerpt, parse_field, parse_float
from models.agent_result import AgentResult
from models.node import WorkflowNode
from services.gemini_client import GeminiClient, GeminiRateLimitError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt — Multi-Dimensional Quality Evaluator
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """\
ROLE
You are AetherMesh's Multi-Dimensional Quality Evaluator. You receive the final artifact \
and all prior agent outputs, then score the artifact across six dimensions that together \
represent comprehensive output quality.

INPUTS
- artifact: the output produced by CoderAgent (primary evaluation target)
- domain: the domain classification
- artifact_type: the declared type of the artifact
- reviewer_output: the verdict and issues from ReviewerAgent
- research_context: facts and assumptions from ResearcherAgent

RESPONSIBILITIES
1. Score TECHNICAL_QUALITY: correctness, completeness, and domain-appropriate implementation.
2. Score REASONING: logical coherence, step-by-step soundness, and justification quality.
3. Score DOMAIN_CORRECTNESS: adherence to domain-specific standards, conventions, and norms.
4. Score HALLUCINATION_RISK: probability that claims, code, or facts are fabricated or unsupported.
5. Score MAINTAINABILITY: for code — readability and extensibility; for documents — structure and clarity.
6. Compute OVERALL_CONFIDENCE as a weighted average, not a simple mean.
7. Produce FEEDBACK: 2-3 specific, actionable sentences — not generic praise or criticism.

BOUNDARIES
- HALLUCINATION_RISK should be 0.0 for well-grounded outputs, not reflexively high.
- Do NOT set any score above 0.97 — perfect scores are never warranted.
- FEEDBACK must reference specific content from the artifact, not generic patterns.
- Weight TECHNICAL_QUALITY and DOMAIN_CORRECTNESS most heavily in OVERALL_CONFIDENCE.
- Penalise MAINTAINABILITY heavily if the artifact contains TODO placeholders.

EXPECTED OUTPUT FORMAT — return exactly this, nothing else:
TECHNICAL_QUALITY: <float 0.0-1.0>
REASONING: <float 0.0-1.0>
DOMAIN_CORRECTNESS: <float 0.0-1.0>
HALLUCINATION_RISK: <float 0.0-1.0>
MAINTAINABILITY: <float 0.0-1.0>
OVERALL_CONFIDENCE: <float 0.0-1.0>
FEEDBACK: <2-3 specific, actionable sentences referencing the actual artifact>

WHAT NOT TO DO
- Do not output vague feedback like "the artifact is good" or "needs improvement".
- Do not score all dimensions identically.
- Do not compute OVERALL_CONFIDENCE as a simple average of other scores.
- Do not include any text outside the format above.
- Do not reference agent names (planner, researcher, etc.) in FEEDBACK — focus on the artifact.
"""


class EvaluatorAgent(BaseAgent):
    """Multi-dimensional quality evaluator: scores artifacts across 6 dimensions."""

    def __init__(self, gemini_client: Optional[GeminiClient] = None) -> None:
        super().__init__("evaluator", gemini_client)

    def run(self, node: WorkflowNode) -> AgentResult:
        artifact: str = node.metadata.get("artifact", node.metadata.get("task", node.name))
        domain: str = node.metadata.get("domain", "general problem-solving")
        artifact_type: str = node.metadata.get("artifact_type", "output")
        shared = node.metadata.get("shared_context", {})

        reviewer_output = excerpt(shared.get("reviewer", ""), max_chars=400)
        research_context = excerpt(shared.get("researcher", ""), max_chars=400)

        if self.gemini is None or not getattr(self.gemini, "has_api_key", True):
            return _local_evaluate(artifact, domain, artifact_type, shared, node.id, rate_limited=False)

        prompt = (
            f"{_SYSTEM_PROMPT}\n\n"
            f"domain: {domain}\n"
            f"artifact_type: {artifact_type}\n\n"
            f"reviewer_output:\n{reviewer_output or '(not available)'}\n\n"
            f"research_context:\n{research_context or '(not available)'}\n\n"
            f"artifact:\n{excerpt(artifact, max_chars=2000)}\n"
        )

        try:
            raw = self.gemini.generate(prompt, temperature=0.1)
        except GeminiRateLimitError as exc:
            logger.warning("EvaluatorAgent rate limited: %s", exc)
            return _local_evaluate(artifact, domain, artifact_type, shared, node.id, rate_limited=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("EvaluatorAgent Gemini call failed: %s", exc)
            return _local_evaluate(artifact, domain, artifact_type, shared, node.id, rate_limited=True)

        overall = parse_float(raw, "OVERALL_CONFIDENCE", default=0.75)
        return AgentResult(
            answer=raw,
            confidence=overall,
            metadata={
                "node_id": node.id,
                "domain": domain,
                "artifact_type": artifact_type,
                "technical_quality": parse_float(raw, "TECHNICAL_QUALITY", default=0.75),
                "reasoning": parse_float(raw, "REASONING", default=0.75),
                "domain_correctness": parse_float(raw, "DOMAIN_CORRECTNESS", default=0.75),
                "hallucination_risk": parse_float(raw, "HALLUCINATION_RISK", default=0.2),
                "maintainability": parse_float(raw, "MAINTAINABILITY", default=0.75),
                "overall_confidence": overall,
                "feedback": parse_field(raw, "FEEDBACK"),
            },
        )


# ---------------------------------------------------------------------------
# Local deterministic fallback — heuristic multi-dimensional scoring
# Combined with repo synergy and length metrics
# ---------------------------------------------------------------------------

def _local_evaluate(
    artifact: str,
    domain: str,
    artifact_type: str,
    shared: dict,
    node_id: str,
    *,
    rate_limited: bool,
) -> AgentResult:
    text = (artifact or "").strip()

    # 1. Synergy & length metrics from repo scoring math
    char_len = len(text)
    length_score = min(1.0, max(0.40, char_len / 750.0))
    active_agents = len([k for k, v in shared.items() if v])
    synergy_score = min(1.0, 0.40 + (active_agents * 0.12))

    has_plan = bool(shared.get("planner"))
    has_research = bool(shared.get("researcher"))
    has_review = bool(shared.get("reviewer"))
    has_code = "```" in text
    has_structure = ("##" in text or "OUTPUT:" in text or "|" in text)

    # 2. Multi-dimensional score calculation integrating synergy and length metrics
    technical_quality = min(0.95, (length_score * 0.4) + (synergy_score * 0.3) + 0.25 + (0.07 if has_code else 0.0))
    reasoning = min(0.90, 0.45 + (0.25 if has_structure else 0.10) + 0.15 * int(has_plan) + 0.10 * int(has_research))
    domain_correctness = min(0.90, 0.50 + (synergy_score * 0.2) + 0.15 * int(has_research) + 0.13 * int(domain != "general problem-solving"))
    hallucination_risk = max(0.05, 0.40 - 0.15 * int(has_research) - 0.10 * int(has_plan))
    maintainability = 0.45 if ("TODO" in text or char_len < 100) else min(0.90, 0.55 + length_score * 0.30)

    overall = round(
        technical_quality * 0.30
        + reasoning * 0.20
        + domain_correctness * 0.25
        + (1.0 - hallucination_risk) * 0.10
        + maintainability * 0.15,
        3,
    )
    note = " (rate-limited)" if rate_limited else " (local)"

    raw = (
        f"TECHNICAL_QUALITY: {technical_quality:.2f}\n"
        f"REASONING: {reasoning:.2f}\n"
        f"DOMAIN_CORRECTNESS: {domain_correctness:.2f}\n"
        f"HALLUCINATION_RISK: {hallucination_risk:.2f}\n"
        f"MAINTAINABILITY: {maintainability:.2f}\n"
        f"OVERALL_CONFIDENCE: {overall:.3f}\n"
        f"FEEDBACK: Multi-dimensional evaluation for {domain} {artifact_type}{note}. "
        f"Scores weighted by artifact length ({char_len} chars), agent synergy ({active_agents} active agents), "
        f"context availability (plan={'yes' if has_plan else 'no'}, research={'yes' if has_research else 'no'}), "
        f"and structural quality markers."
    )

    return AgentResult(
        answer=raw,
        confidence=overall,
        metadata={
            "node_id": node_id,
            "domain": domain,
            "artifact_type": artifact_type,
            "technical_quality": round(technical_quality, 2),
            "reasoning": round(reasoning, 2),
            "domain_correctness": round(domain_correctness, 2),
            "hallucination_risk": round(hallucination_risk, 2),
            "maintainability": round(maintainability, 2),
            "overall_confidence": overall,
            "completeness": round(min(1.0, (length_score * 0.5) + (synergy_score * 0.5)), 2),
            "correctness": round(min(1.0, ((1.0 if has_code else 0.65) * 0.6) + (0.4 if "TODO" not in text else 0.1)), 2),
            "clarity": round(min(1.0, ((1.0 if has_structure else 0.50) * 0.7) + (0.3 if char_len > 150 else 0.1)), 2),
            "feedback": f"Multi-dimensional evaluation for {domain} {artifact_type}{note}.",
            "rate_limited": rate_limited,
            "local_fallback": True,
        },
    )
