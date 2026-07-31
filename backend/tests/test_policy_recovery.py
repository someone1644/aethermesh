"""
End-to-end tests for the four recovery policies (plus the built-in
LowSourcesPolicy, which rides along since it's always registered
alongside the other four in production — see test_backend.py).

Each policy test has two parts:
  1. A direct PolicyEngine.evaluate() / DecisionEngine.select() check —
     construct the ExecutionState right at the trigger point and assert
     the exact RuntimeDecision shape (action, target_node, policy_name,
     reason).
  2. A full RuntimeEngine.execute() run with scripted (fake, in-process)
     agents standing in for planner/researcher/evaluator/coder, asserting
     the resulting policy_triggered RuntimeEvent, the graph mutation, and
     that the workflow recovers and completes normally.

Real thresholds (not the ones from the request's scenario table, which
don't match the current implementation):
  - LowConfidencePolicy:    confidence < 0.4          (not 0.6)
  - ContradictionPolicy:    contradiction_score > 0.6  (not 0.7)
  - MissingRepoPolicy:      repository_found is False  (adds a fallback
                             "Repository search" node, action=ADD)
  - ExecutionTimeoutPolicy: cumulative execution_time > timeout_seconds
                             (action=REMOVE on the current node, not
                             replace)
None of the policies ever emit DecisionAction.REPLACE today — only ADD
and REMOVE — so target_node is only populated for the timeout policy.
"""
from __future__ import annotations

import time

import pytest

from agents.base_agent import BaseAgent
from agents.registry import AgentRegistry
from config import settings
from models.agent_result import AgentResult
from models.event import EventType
from models.execution import ExecutionState
from models.node import NodeStatus, WorkflowNode
from models.runtime_decision import DecisionAction
from models.workflow import Workflow
from policies import (
    ContradictionPolicy,
    ExecutionTimeoutPolicy,
    LowConfidencePolicy,
    LowSourcesPolicy,
    MissingRepoPolicy,
)
from policies.contradiction import CONTRADICTION_THRESHOLD
from policies.low_confidence import CONFIDENCE_THRESHOLD
from runtime.decision_engine import DecisionEngine
from runtime.engine import RuntimeEngine
from runtime.policy_engine import PolicyEngine


@pytest.fixture(autouse=True)
def _no_agent_delay(monkeypatch):
    """RuntimeEngine sleeps GEMINI_AGENT_DELAY_SECONDS (2s by default) before
    every node to pace real Gemini calls. These tests use fake, in-process
    agents, so the delay would only make them slow."""
    monkeypatch.setattr(settings, "GEMINI_AGENT_DELAY_SECONDS", 0.0)


class ScriptedAgent(BaseAgent):
    """Returns AgentResults (or AgentResult-returning callables, for
    simulating slow calls) from a fixed script, one entry per call,
    holding on the last entry once the script is exhausted."""

    def __init__(self, name: str, script: list):
        super().__init__(name)
        self._script = list(script)
        self.calls = 0

    def run(self, node: WorkflowNode) -> AgentResult:
        item = self._script[min(self.calls, len(self._script) - 1)]
        self.calls += 1
        return item(node) if callable(item) else item


def _linear_workflow(*node_specs):
    """node_specs: (name, agent_type) tuples, wired A -> B -> C -> ..."""
    wf = Workflow()
    nodes = [WorkflowNode(name=name, agent_type=agent_type) for name, agent_type in node_specs]
    for node in nodes:
        wf.add_node(node)
    for a, b in zip(nodes, nodes[1:]):
        wf.add_edge(a.id, b.id)
    return wf, nodes


def _all_policies(**timeout_kwargs) -> PolicyEngine:
    return PolicyEngine(
        policies=[
            LowConfidencePolicy(),
            ContradictionPolicy(),
            MissingRepoPolicy(),
            LowSourcesPolicy(),
            ExecutionTimeoutPolicy(**timeout_kwargs),
        ]
    )


def _policy_events(state: ExecutionState):
    return [e for e in state.events if e.event_type == EventType.POLICY_TRIGGERED]


# ---------------------------------------------------------------------------
# 1. low_confidence_policy
# ---------------------------------------------------------------------------


def test_low_confidence_policy_decision_shape():
    wf, (plan,) = _linear_workflow(("Plan", "planner"))
    state = ExecutionState(task="t", workflow=wf)
    state.metrics.completed_agents = 1
    state.confidence = 0.30
    state.sources = 5  # keep LowSourcesPolicy from also firing

    engine = _all_policies()
    decisions = engine.evaluate(state)
    assert len(decisions) == 1

    decision = DecisionEngine().select(decisions)
    assert decision.policy_name == "LowConfidencePolicy"
    assert decision.action == DecisionAction.ADD
    assert decision.target_node is None
    assert decision.new_node.agent_type == "researcher"
    assert f"{0.30:.2f}" in decision.reason
    assert f"{CONFIDENCE_THRESHOLD:.2f}" in decision.reason


def test_low_confidence_policy_end_to_end_recovers():
    task = "Diagnose the failing checkout-service CI pipeline and ship a fix"
    wf, (plan, research) = _linear_workflow(("Plan", "planner"), ("Diagnose CI failure", "researcher"))
    state = ExecutionState(task=task, workflow=wf)

    registry = AgentRegistry()
    registry.register("planner", ScriptedAgent("planner", [AgentResult(answer="plan", confidence=0.9)]))
    registry.register(
        "researcher",
        ScriptedAgent(
            "researcher",
            [
                AgentResult(
                    answer="inconclusive",
                    confidence=0.30,
                    metadata={"sources": 5, "repository_found": True, "contradiction_score": 0.0},
                ),
                AgentResult(answer="root cause: bad env var; fix pushed", confidence=0.75),
            ],
        ),
    )

    engine = RuntimeEngine(policy_engine=_all_policies(), registry=registry)
    result = engine.execute(state)

    events = _policy_events(result)
    assert len(events) == 1
    assert events[0].details["policy"] == "LowConfidencePolicy"
    assert f"{0.30:.2f}" in events[0].reason

    added = next(n for n in result.workflow.nodes if n.metadata.get("reason") == "confidence_boost")
    assert added.agent_type == "researcher"
    assert added.status == NodeStatus.COMPLETED  # got a turn and finished

    assert result.status.value == "completed"
    assert result.confidence >= 0.6
    assert all(n.status == NodeStatus.COMPLETED for n in result.workflow.nodes)


# ---------------------------------------------------------------------------
# 2. contradiction_policy
# ---------------------------------------------------------------------------


def test_contradiction_policy_decision_shape():
    wf, (plan,) = _linear_workflow(("Plan", "planner"))
    state = ExecutionState(task="t", workflow=wf)
    state.metrics.completed_agents = 1
    state.confidence = 0.9
    state.sources = 5
    state.repository_found = True
    state.contradiction_score = 0.80

    engine = _all_policies()
    decisions = engine.evaluate(state)
    assert len(decisions) == 1

    decision = DecisionEngine().select(decisions)
    assert decision.policy_name == "ContradictionPolicy"
    assert decision.action == DecisionAction.ADD
    assert decision.target_node is None
    assert decision.new_node.agent_type == "evaluator"
    assert f"{0.80:.2f}" in decision.reason
    assert f"{CONTRADICTION_THRESHOLD:.2f}" in decision.reason


def test_contradiction_policy_end_to_end_recovers():
    task = "Reconcile conflicting evidence from three sources on the outage root cause"
    wf, (plan, research) = _linear_workflow(("Plan", "planner"), ("Gather evidence", "researcher"))
    state = ExecutionState(task=task, workflow=wf)

    registry = AgentRegistry()
    registry.register("planner", ScriptedAgent("planner", [AgentResult(answer="plan", confidence=0.9)]))
    registry.register(
        "researcher",
        ScriptedAgent(
            "researcher",
            [
                AgentResult(
                    answer="Source A blames network partition; Source B blames bad deploy — directly conflicting",
                    confidence=0.9,
                    metadata={"sources": 5, "repository_found": True, "contradiction_score": 0.80},
                ),
            ],
        ),
    )
    registry.register("evaluator", ScriptedAgent("evaluator", [AgentResult(answer="reconciled", confidence=0.9)]))

    engine = RuntimeEngine(policy_engine=_all_policies(), registry=registry)
    result = engine.execute(state)

    events = _policy_events(result)
    assert len(events) == 1
    assert events[0].details["policy"] == "ContradictionPolicy"
    assert f"{0.80:.2f}" in events[0].reason

    added = next(n for n in result.workflow.nodes if n.metadata.get("reason") == "contradiction_resolution")
    assert added.agent_type == "evaluator"
    assert added.status == NodeStatus.COMPLETED

    assert result.status.value == "completed"


# ---------------------------------------------------------------------------
# 3. missing_repo_policy
# ---------------------------------------------------------------------------


def test_missing_repo_policy_decision_shape():
    wf, (plan,) = _linear_workflow(("Plan", "planner"))
    state = ExecutionState(task="t", workflow=wf)
    state.metrics.completed_agents = 1
    state.confidence = 0.9
    state.sources = 5
    state.repository_found = False
    state.contradiction_score = 0.0

    engine = _all_policies()
    decisions = engine.evaluate(state)
    assert len(decisions) == 1

    decision = DecisionEngine().select(decisions)
    assert decision.policy_name == "MissingRepoPolicy"
    assert decision.action == DecisionAction.ADD
    assert decision.target_node is None
    assert decision.new_node.agent_type == "researcher"
    assert decision.reason == "No repository was located during execution."


def test_missing_repo_policy_end_to_end_recovers():
    task = "Investigate a missing repository dependency for service X"
    wf, (plan, research) = _linear_workflow(("Plan", "planner"), ("Locate dependency", "researcher"))
    state = ExecutionState(task=task, workflow=wf)

    registry = AgentRegistry()
    registry.register("planner", ScriptedAgent("planner", [AgentResult(answer="plan", confidence=0.9)]))
    registry.register(
        "researcher",
        ScriptedAgent(
            "researcher",
            [
                AgentResult(
                    answer="Could not locate the repository for service X",
                    confidence=0.9,
                    metadata={"sources": 5, "repository_found": False, "contradiction_score": 0.0},
                ),
                AgentResult(
                    answer="Found it under the renamed org path",
                    confidence=0.9,
                    metadata={"repository_found": True},
                ),
            ],
        ),
    )

    engine = RuntimeEngine(policy_engine=_all_policies(), registry=registry)
    result = engine.execute(state)

    events = _policy_events(result)
    assert len(events) == 1
    assert events[0].details["policy"] == "MissingRepoPolicy"
    assert events[0].reason == "No repository was located during execution."

    added = next(n for n in result.workflow.nodes if n.metadata.get("reason") == "repository_search")
    assert added.agent_type == "researcher"
    assert added.status == NodeStatus.COMPLETED

    assert result.status.value == "completed"
    assert result.repository_found is True


# ---------------------------------------------------------------------------
# 4. execution_timeout_policy
# ---------------------------------------------------------------------------


def test_execution_timeout_policy_decision_shape():
    wf, (research,) = _linear_workflow(("Research", "researcher"))
    state = ExecutionState(task="t", workflow=wf)
    state.workflow.current_node = research.id
    state.metrics.completed_agents = 1
    state.metrics.execution_time = 5.0
    state.confidence = 0.9
    state.sources = 5
    state.repository_found = True
    state.contradiction_score = 0.0

    engine = _all_policies(timeout_seconds=1.0)
    decisions = engine.evaluate(state)
    assert len(decisions) == 1

    decision = DecisionEngine().select(decisions)
    assert decision.policy_name == "ExecutionTimeoutPolicy"
    assert decision.action == DecisionAction.REMOVE
    assert decision.target_node == research.id
    assert f"{5.0:.2f}s" in decision.reason
    assert f"{1.0:.2f}s" in decision.reason


def test_execution_timeout_policy_end_to_end_removes_slow_node():
    task = "Run a slow diagnostic against the payments service"
    wf, (plan, research) = _linear_workflow(("Plan", "planner"), ("Slow diagnostic", "researcher"))
    research_id = research.id
    state = ExecutionState(task=task, workflow=wf)

    def _slow_result(_node):
        time.sleep(0.2)
        return AgentResult(
            answer="done",
            confidence=0.9,
            metadata={"sources": 5, "repository_found": True, "contradiction_score": 0.0},
        )

    registry = AgentRegistry()
    registry.register("planner", ScriptedAgent("planner", [AgentResult(answer="plan", confidence=0.9)]))
    registry.register("researcher", ScriptedAgent("researcher", [_slow_result]))

    engine = RuntimeEngine(policy_engine=_all_policies(timeout_seconds=0.05), registry=registry)
    result = engine.execute(state)

    events = _policy_events(result)
    assert len(events) == 1
    assert events[0].details["policy"] == "ExecutionTimeoutPolicy"
    assert "exceeded timeout of 0.05s" in events[0].reason

    assert result.workflow.get_node(research_id) is None  # removed, not replaced in place
    assert result.metrics.mutations == 1
    assert result.status.value == "completed"


# ---------------------------------------------------------------------------
# 5. Control: happy path — no policy should fire
# ---------------------------------------------------------------------------


def test_happy_path_triggers_no_policies():
    task = "Summarize open tasks across the team board"
    wf, (plan, research, code) = _linear_workflow(
        ("Plan", "planner"), ("Gather status", "researcher"), ("Summarize", "coder")
    )
    state = ExecutionState(task=task, workflow=wf)

    good_metadata = {"sources": 5, "repository_found": True, "contradiction_score": 0.0}
    registry = AgentRegistry()
    registry.register("planner", ScriptedAgent("planner", [AgentResult(answer="plan", confidence=0.9)]))
    registry.register(
        "researcher",
        ScriptedAgent("researcher", [AgentResult(answer="status gathered", confidence=0.85, metadata=good_metadata)]),
    )
    registry.register(
        "coder", ScriptedAgent("coder", [AgentResult(answer="summary written", confidence=0.9, metadata=good_metadata)])
    )

    engine = RuntimeEngine(policy_engine=_all_policies(), registry=registry)
    result = engine.execute(state)

    assert _policy_events(result) == []
    assert result.metrics.mutations == 0
    assert result.status.value == "completed"
    assert len(result.workflow.nodes) == 3
    assert all(n.status == NodeStatus.COMPLETED for n in result.workflow.nodes)
    assert not any(n.status in (NodeStatus.FAILED, NodeStatus.SKIPPED) for n in result.workflow.nodes)
