from __future__ import annotations

"""
Composition root for the AetherMesh agent runtime.

This module constructs the shared :class:`~services.gemini_client.GeminiClient`,
injects it into Gemini-backed agents only (planner, researcher), registers them
all in an :class:`~agents.registry.AgentRegistry`, and exposes a pre-built
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


from runtime.event_logger import EventLogger


def build_registry(gemini_client: GeminiClient) -> AgentRegistry:
    """
    Construct an :class:`AgentRegistry` with Gemini wired only to planner
    and researcher. Coder, reviewer, and evaluator run locally.
    """
    reg = AgentRegistry()
    reg.register("planner",    PlannerAgent(gemini_client))
    reg.register("researcher", ResearcherAgent(gemini_client))
    reg.register("coder",      CoderAgent())
    reg.register("reviewer",   ReviewerAgent())
    reg.register("evaluator",  EvaluatorAgent())
    return reg


# ---------------------------------------------------------------------------
# Module-level singletons — import these directly from consuming code.
# ---------------------------------------------------------------------------

#: Shared Gemini SDK client.
gemini_client: GeminiClient = GeminiClient()

#: Shared EventLogger instance for logging and replay.
event_logger: EventLogger = EventLogger()

#: Agent registry — only planner/researcher use Gemini.
registry: AgentRegistry = build_registry(gemini_client)

#: Workflow generator backed by the shared Gemini client (1 call per task).
workflow_generator: WorkflowGenerator = WorkflowGenerator(gemini_client)
