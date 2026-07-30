from models.execution import ExecutionState
from models.node import NodeStatus, WorkflowNode
from models.runtime_decision import DecisionAction, RuntimeDecision
from models.workflow import Workflow
from runtime.mutation_engine import MutationEngine
from runtime.state_manager import StateManager
from runtime.workflow_graph import is_valid_dag, next_ready_node, to_node_link_data


def _linear_workflow() -> Workflow:
    """A -> B -> C, mirroring the shape of a real planner/researcher/coder chain."""
    a = WorkflowNode(name="A", agent_type="planner", status=NodeStatus.COMPLETED)
    b = WorkflowNode(name="B", agent_type="researcher", status=NodeStatus.PENDING)
    c = WorkflowNode(name="C", agent_type="coder", status=NodeStatus.PENDING)

    wf = Workflow()
    wf.add_node(a)
    wf.add_node(b)
    wf.add_node(c)
    wf.add_edge(a.id, b.id)
    wf.add_edge(b.id, c.id)
    wf.current_node = b.id

    return wf, a, b, c


def test_next_ready_node_follows_topological_order():
    wf, a, b, c = _linear_workflow()

    # A is already completed; B is the only node whose dependencies are
    # satisfied and is itself pending, so it must be picked next.
    assert next_ready_node(wf).id == b.id

    b.status = NodeStatus.COMPLETED
    assert next_ready_node(wf).id == c.id

    c.status = NodeStatus.COMPLETED
    assert next_ready_node(wf) is None


def test_mutation_engine_applies_valid_add():
    wf, a, b, c = _linear_workflow()
    state = ExecutionState(task="t", workflow=wf)
    manager = StateManager(state)

    new_node = WorkflowNode(name="Extra research", agent_type="researcher")
    decision = RuntimeDecision(
        action=DecisionAction.ADD,
        new_node=new_node,
        policy_name="TestPolicy",
    )

    applied = MutationEngine().apply(manager, decision)

    assert applied is True
    assert state.metrics.mutations == 1
    assert wf.get_node(new_node.id) is not None
    # Wired in after the currently-active node (B), not left disconnected.
    assert any(e.source == b.id and e.target == new_node.id for e in wf.edges)
    assert is_valid_dag(wf)


def test_mutation_engine_rejects_mutation_that_introduces_a_cycle():
    wf, a, b, c = _linear_workflow()
    state = ExecutionState(task="t", workflow=wf)
    manager = StateManager(state)

    original_edges = [(e.source, e.target) for e in wf.edges]
    original_node_ids = {n.id for n in wf.nodes}

    # Replacing C with a node that reuses A's id rewires the B->C edge
    # into B->A. Combined with the existing A->B edge, that's a 2-cycle
    # (A -> B -> A) — this must be rejected, not silently committed.
    cyclic_new_node = WorkflowNode(id=a.id, name="A again", agent_type="planner")
    decision = RuntimeDecision(
        action=DecisionAction.REPLACE,
        target_node=c.id,
        new_node=cyclic_new_node,
        policy_name="TestPolicy",
    )

    applied = MutationEngine().apply(manager, decision)

    assert applied is False
    assert state.metrics.mutations == 0
    # Workflow must be left untouched — no partial/broken mutation.
    assert {n.id for n in wf.nodes} == original_node_ids
    assert [(e.source, e.target) for e in wf.edges] == original_edges
    assert is_valid_dag(wf)


def test_to_node_link_data_reflects_current_graph():
    wf, a, b, c = _linear_workflow()

    data = to_node_link_data(wf)

    node_ids = {n["id"] for n in data["nodes"]}
    assert node_ids == {a.id, b.id, c.id}
    assert len(data["edges"]) == 2
