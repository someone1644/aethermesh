from __future__ import annotations

import logging
from typing import Optional

from agents.base_agent import BaseAgent
from agents.context_utils import excerpt, parse_field, parse_float, parse_list_field
from models.agent_result import AgentResult
from models.node import WorkflowNode
from services.gemini_client import GeminiClient, GeminiRateLimitError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt — Assumption Challenger & Hallucination Detector
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """\
ROLE
You are AetherMesh's Critic — an adversarial quality agent whose sole purpose is to challenge \
every output produced by the prior agents. You are not helpful, encouraging, or constructive \
by default. You are skeptical, precise, and evidence-driven.

INPUTS
- task: the original task description
- domain: the domain classification
- planner_output: the orchestration plan to question
- researcher_output: the research findings to challenge
- coder_output: the artifact to probe for correctness
- reviewer_verdict: the approval decision to re-examine
- evaluator_scores: the quality scores to scrutinise

RESPONSIBILITIES
1. PLANNER CHALLENGE: Are the required_agents list, complexity, and task_type justified? \
   Flag if the planner overcommitted or undercommitted agents.
2. RESEARCHER CHALLENGE: Which claims in FACTS are actually unverified assumptions? \
   Which ASSUMPTIONS could have been stated as facts? Are unknowns real or just lazy admissions?
3. CODER CHALLENGE: Does the artifact actually fulfil the task? Are there logical gaps, \
   contradictions with the plan, or domain-incorrect patterns?
4. REVIEWER CHALLENGE: Was APPROVE issued without sufficient evidence? \
   Were any issues dismissed without justification?
5. EVALUATOR CHALLENGE: Are the scores internally consistent? Does HALLUCINATION_RISK \
   reflect actual unsupported claims in the artifact?
6. Produce a RISK_LEVEL: critical | high | medium | low.
7. Compute HALLUCINATION_PROBABILITY: the probability that key claims are unsupported.

BOUNDARIES
- Do NOT produce a full re-review — produce targeted challenges only.
- Do NOT challenge outputs that were not provided — mark them as "not available".
- Do NOT fabricate hallucinations — only flag claims that are verifiably unsupported.
- RECOMMENDED_ACTIONS must be specific enough to act on.
- Maximum 3 unsupported assumptions and 3 recommended actions.

EXPECTED OUTPUT FORMAT — return exactly this, nothing else:
ARTIFACT_TYPE: critic_report
RISK_LEVEL: <critical|high|medium|low>
HALLUCINATION_PROBABILITY: <float 0.0-1.0>
UNSUPPORTED_ASSUMPTIONS:
- <specific claim from prior outputs that lacks evidence> (or "- None identified")
PLANNER_CHALLENGES:
- <specific challenge to planner decision> (or "- None")
RESEARCHER_CHALLENGES:
- <specific challenge to researcher claim> (or "- None")
CODER_CHALLENGES:
- <specific challenge to artifact correctness> (or "- None")
REVIEWER_CHALLENGES:
- <specific challenge to reviewer verdict> (or "- None")
RECOMMENDED_ACTIONS:
- <specific corrective action 1>
CONFIDENCE: <float 0.0-1.0>

WHAT NOT TO DO
- Do not fabricate claims that are not present in the provided inputs.
- Do not challenge things not in scope (e.g. criticise performance when evaluating a business doc).
- Do not give a LOW risk level if any UNSUPPORTED_ASSUMPTIONS were found.
- Do not repeat the same challenge under multiple headers.
- Do not produce a confidence score above 0.90 — perfect critic certainty is not warranted.
"""


class CriticAgent(BaseAgent):
    """
    Adversarial quality agent: challenges assumptions, detects hallucinations,
    and questions decisions made by all prior agents.

    NOTE: Registered in the agent registry but NOT yet integrated into the
    RuntimeEngine workflow. Prepared for future runtime integration.
    """

    def __init__(self, gemini_client: Optional[GeminiClient] = None) -> None:
        super().__init__("critic", gemini_client)

    def run(self, node: WorkflowNode) -> AgentResult:
        task: str = node.metadata.get("task", node.name)
        domain: str = node.metadata.get("domain", "general problem-solving")
        shared = node.metadata.get("shared_context", {})

        planner_out = excerpt(shared.get("planner", ""), max_chars=600)
        researcher_out = excerpt(shared.get("researcher", ""), max_chars=600)
        coder_out = excerpt(shared.get("coder", ""), max_chars=600)
        reviewer_out = excerpt(shared.get("reviewer", ""), max_chars=400)
        evaluator_out = excerpt(shared.get("evaluator", ""), max_chars=400)

        if self.gemini is None or not getattr(self.gemini, "has_api_key", True):
            return _local_critique(task, domain, shared, node.id, rate_limited=False)

        prompt = (
            f"{_SYSTEM_PROMPT}\n\n"
            f"task: {task}\n"
            f"domain: {domain}\n\n"
            f"planner_output:\n{planner_out or '(not available)'}\n\n"
            f"researcher_output:\n{researcher_out or '(not available)'}\n\n"
            f"coder_output:\n{coder_out or '(not available)'}\n\n"
            f"reviewer_verdict:\n{reviewer_out or '(not available)'}\n\n"
            f"evaluator_scores:\n{evaluator_out or '(not available)'}\n"
        )

        try:
            raw = self.gemini.generate(prompt, temperature=0.15)
        except GeminiRateLimitError as exc:
            logger.warning("CriticAgent rate limited: %s", exc)
            return _local_critique(task, domain, shared, node.id, rate_limited=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("CriticAgent Gemini call failed: %s", exc)
            return _local_critique(task, domain, shared, node.id, rate_limited=True)

        confidence = parse_float(raw, "CONFIDENCE", default=0.75)
        hallucination_prob = parse_float(raw, "HALLUCINATION_PROBABILITY", default=0.2)
        risk_level = parse_field(raw, "RISK_LEVEL", default="medium")

        return AgentResult(
            answer=raw,
            confidence=confidence,
            metadata={
                "agent_type": "critic",
                "node_id": node.id,
                "domain": domain,
                "risk_level": risk_level,
                "hallucination_probability": hallucination_prob,
                "unsupported_assumptions": parse_list_field(raw, "UNSUPPORTED_ASSUMPTIONS"),
                "planner_challenges": parse_list_field(raw, "PLANNER_CHALLENGES"),
                "researcher_challenges": parse_list_field(raw, "RESEARCHER_CHALLENGES"),
                "coder_challenges": parse_list_field(raw, "CODER_CHALLENGES"),
                "reviewer_challenges": parse_list_field(raw, "REVIEWER_CHALLENGES"),
                "recommended_actions": parse_list_field(raw, "RECOMMENDED_ACTIONS"),
            },
        )


# ---------------------------------------------------------------------------
# Local deterministic fallback
# ---------------------------------------------------------------------------

def _local_critique(
    task: str,
    domain: str,
    shared: dict,
    node_id: str,
    *,
    rate_limited: bool,
) -> AgentResult:
    note = " (rate-limited)" if rate_limited else " (local fallback)"

    reviewer_approved = "APPROVE" in shared.get("reviewer", "")
    researcher_present = bool(shared.get("researcher"))
    coder_present = bool(shared.get("coder"))
    has_assumptions = "ASSUMPTIONS:" in shared.get("researcher", "")

    # Heuristic challenges
    unsupported = []
    planner_ch = []
    researcher_ch = []
    coder_ch = []
    reviewer_ch = []

    if not researcher_present:
        unsupported.append("Planner proceeded without research validation — domain facts unverified")
    if has_assumptions:
        researcher_ch.append("Researcher listed assumptions without flagging their impact on confidence")
    if coder_present and "TODO" in shared.get("coder", ""):
        coder_ch.append("Coder artifact contains TODO placeholders — implementation is incomplete")
    if reviewer_approved and not coder_present:
        reviewer_ch.append("Reviewer issued APPROVE without a code artifact to review")
    if not shared.get("planner"):
        planner_ch.append("No planner output found — workflow proceeded without orchestration metadata")

    all_issues = unsupported + planner_ch + researcher_ch + coder_ch + reviewer_ch
    risk = "high" if len(all_issues) >= 3 else ("medium" if all_issues else "low")
    hallucination_prob = min(0.6, 0.1 + 0.1 * len(unsupported) + (0.15 if not researcher_present else 0.0))

    raw = (
        f"ARTIFACT_TYPE: critic_report\n"
        f"RISK_LEVEL: {risk}{note}\n"
        f"HALLUCINATION_PROBABILITY: {hallucination_prob:.2f}\n"
        f"UNSUPPORTED_ASSUMPTIONS:\n"
        + ("\n".join(f"- {u}" for u in unsupported) if unsupported else "- None identified") + "\n"
        f"PLANNER_CHALLENGES:\n"
        + ("\n".join(f"- {c}" for c in planner_ch) if planner_ch else "- None") + "\n"
        f"RESEARCHER_CHALLENGES:\n"
        + ("\n".join(f"- {c}" for c in researcher_ch) if researcher_ch else "- None") + "\n"
        f"CODER_CHALLENGES:\n"
        + ("\n".join(f"- {c}" for c in coder_ch) if coder_ch else "- None") + "\n"
        f"REVIEWER_CHALLENGES:\n"
        + ("\n".join(f"- {c}" for c in reviewer_ch) if reviewer_ch else "- None") + "\n"
        f"RECOMMENDED_ACTIONS:\n"
        + (
            "\n".join(f"- {a}" for a in (all_issues[:3] or ["Re-run with complete pipeline to reduce uncertainty"]))
        ) + "\n"
        "CONFIDENCE: 0.65"
    )

    return AgentResult(
        answer=raw,
        confidence=0.65,
        metadata={
            "agent_type": "critic",
            "node_id": node_id,
            "domain": domain,
            "risk_level": risk,
            "hallucination_probability": round(hallucination_prob, 2),
            "unsupported_assumptions": unsupported,
            "planner_challenges": planner_ch,
            "researcher_challenges": researcher_ch,
            "coder_challenges": coder_ch,
            "reviewer_challenges": reviewer_ch,
            "recommended_actions": all_issues[:3] or ["Re-run with complete pipeline"],
            "rate_limited": rate_limited,
            "local_fallback": True,
        },
    )
