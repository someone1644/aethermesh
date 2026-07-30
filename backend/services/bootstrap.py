from __future__ import annotations

"""
Composition root for the AetherMesh agent runtime.

This module constructs the shared :class:`~services.gemini_client.GeminiClient`,
injects it into every agent, registers them all in an
:class:`~agents.registry.AgentRegistry`, and exposes a pre-built
:class:`~services.workflow_generator.WorkflowGenerator`.

Usage (e.g. from an API route or lifespan handler)::

    from services.bootstrap import registry, workflow_generator

    state = ExecutionState(task="...", workflow=workflow_generator.generate("..."))
    engine.execute(state)
"""

from agents.coder_agent import CoderAgent
from agents.evaluator_agent import EvaluatorAgent
from agents.planner_agent import PlannerAgent
from agents.registry import AgentRegistry
from agents.researcher_agent import ResearcherAgent
from agents.reviewer_agent import ReviewerAgent
from services.gemini_client import GeminiClient
from services.workflow_generator import WorkflowGenerator


def build_registry(gemini_client: GeminiClient) -> AgentRegistry:
    """
    Construct an :class:`AgentRegistry` with all agents wired to
    *gemini_client*.

    Returns
    -------
    AgentRegistry
        Registry keyed by ``agent_type`` string as used in
        :class:`~models.node.WorkflowNode`.
    """
    reg = AgentRegistry()
    reg.register("planner",    PlannerAgent(gemini_client))
    reg.register("researcher", ResearcherAgent(gemini_client))
    reg.register("coder",      CoderAgent(gemini_client))
    reg.register("reviewer",   ReviewerAgent(gemini_client))
    reg.register("evaluator",  EvaluatorAgent(gemini_client))
    return reg


# ---------------------------------------------------------------------------
# Module-level singletons — import these directly from consuming code.
# ---------------------------------------------------------------------------

#: Shared Gemini SDK client.
gemini_client: GeminiClient = GeminiClient()

#: Agent registry pre-loaded with all Gemini-powered agents.
registry: AgentRegistry = build_registry(gemini_client)

#: Workflow generator backed by the shared Gemini client.
workflow_generator: WorkflowGenerator = WorkflowGenerator(gemini_client)
