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

from agents.analyst_agent import AnalystAgent
from agents.coder_agent import CoderAgent
from agents.summarizer_agent import SummarizerAgent
from agents.debugger_agent import DebuggerAgent
from agents.evaluator_agent import EvaluatorAgent
from agents.optimizer_agent import OptimizerAgent
from agents.planner_agent import PlannerAgent
from agents.registry import AgentRegistry
from agents.researcher_agent import ResearcherAgent
from agents.reviewer_agent import ReviewerAgent
from agents.sandbox_runner import SandboxRunnerAgent
from agents.security_agent import SecurityAuditorAgent
from services.gemini_client import GeminiClient
from services.workflow_generator import WorkflowGenerator


from runtime.event_logger import EventLogger


def build_registry(gemini_client: GeminiClient) -> AgentRegistry:
    """
    Construct an :class:`AgentRegistry` with Gemini wired only to planner
    and researcher. Coder, reviewer, and evaluator run locally.
    """
    reg = AgentRegistry()
    reg.register("planner",          PlannerAgent(gemini_client))
    reg.register("researcher",       ResearcherAgent(gemini_client))
    reg.register("coder",            CoderAgent())
    reg.register("reviewer",         ReviewerAgent())
    reg.register("evaluator",        EvaluatorAgent())
    reg.register("debugger",         DebuggerAgent())
    reg.register("security_auditor", SecurityAuditorAgent())
    reg.register("optimizer",        OptimizerAgent())
    reg.register("sandbox_runner",   SandboxRunnerAgent())
    reg.register("summarizer",        SummarizerAgent())
    reg.register("analyst",           AnalystAgent())
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
