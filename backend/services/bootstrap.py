from __future__ import annotations

"""
Composition root for the AetherMesh agent runtime.

Constructs the shared GeminiClient and injects it into all agents.
All agents implement Gemini-backed prompts with deterministic local fallbacks.

CriticAgent is registered here but NOT yet integrated into the RuntimeEngine
workflow — it is prepared and available for future runtime activation.

Usage::

    from services.bootstrap import registry, workflow_generator

    state = ExecutionState(task="...", workflow=workflow_generator.generate("..."))
    engine.execute(state)
"""

from agents.analyst_agent import AnalystAgent
from agents.coder_agent import CoderAgent
from agents.critic_agent import CriticAgent
from agents.debugger_agent import DebuggerAgent
from agents.evaluator_agent import EvaluatorAgent
from agents.optimizer_agent import OptimizerAgent
from agents.planner_agent import PlannerAgent
from agents.registry import AgentRegistry
from agents.researcher_agent import ResearcherAgent
from agents.reviewer_agent import ReviewerAgent
from agents.sandbox_runner import SandboxRunnerAgent
from agents.security_agent import SecurityAuditorAgent
from agents.summarizer_agent import SummarizerAgent
from services.gemini_client import GeminiClient
from services.workflow_generator import WorkflowGenerator

from runtime.event_logger import EventLogger


def build_registry(gemini_client: GeminiClient) -> AgentRegistry:
    """
    Construct an AgentRegistry with the shared GeminiClient injected into
    all agents. Each agent decides at runtime whether to call Gemini
    (when has_api_key is True) or fall back to its local implementation.

    CriticAgent is registered but not yet activated in the runtime workflow.
    """
    reg = AgentRegistry()

    # Core pipeline agents
    reg.register("planner",          PlannerAgent(gemini_client))
    reg.register("researcher",       ResearcherAgent(gemini_client))
    reg.register("coder",            CoderAgent(gemini_client))
    reg.register("reviewer",         ReviewerAgent(gemini_client))
    reg.register("evaluator",        EvaluatorAgent(gemini_client))

    # Specialized domain agents
    reg.register("debugger",         DebuggerAgent(gemini_client))
    reg.register("security_auditor", SecurityAuditorAgent(gemini_client))
    reg.register("optimizer",        OptimizerAgent(gemini_client))
    reg.register("sandbox_runner",   SandboxRunnerAgent(gemini_client))

    # Synthesis agents
    reg.register("summarizer",       SummarizerAgent(gemini_client))
    reg.register("analyst",          AnalystAgent(gemini_client))

    # Adversarial quality agent — registered, NOT yet in runtime workflow
    reg.register("critic",           CriticAgent(gemini_client))

    return reg


# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

#: Shared Gemini SDK client — lazy init, reused across all agents.
gemini_client: GeminiClient = GeminiClient()

#: Shared EventLogger instance for logging and replay.
event_logger: EventLogger = EventLogger()

#: Agent registry — all agents receive the shared Gemini client.
registry: AgentRegistry = build_registry(gemini_client)

#: Workflow generator backed by the shared Gemini client (1 call per task).
workflow_generator: WorkflowGenerator = WorkflowGenerator(gemini_client)
