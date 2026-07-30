from __future__ import annotations

from typing import Any, Dict, List, Optional

import networkx as nx

from models.node import NodeStatus, WorkflowNode
from models.workflow import Workflow


def build_graph(workflow: Workflow) -> "nx.DiGraph":
    """
    Build a networkx DiGraph mirroring the current Workflow structure.

    Nodes are keyed by WorkflowNode.id; edges follow Workflow.edges
    (source -> target). This is a derived, throwaway structure — the
    Pydantic Workflow model remains the source of truth — rebuilt fresh
    from it whenever needed rather than maintained incrementally.
    """
    graph: "nx.DiGraph" = nx.DiGraph()

    for node in workflow.nodes:
        graph.add_node(
            node.id,
            name=node.name,
            agent_type=node.agent_type,
            status=node.status.value,
        )

    for edge in workflow.edges:
        graph.add_edge(edge.source, edge.target)

    return graph


def is_valid_dag(workflow: Workflow) -> bool:
    """Whether the workflow's current graph is a valid DAG (no cycles)."""
    return nx.is_directed_acyclic_graph(build_graph(workflow))


def topological_order(workflow: Workflow) -> List[str]:
    """
    Node ids in topological order.

    Raises networkx.NetworkXUnfeasible if the graph contains a cycle —
    callers that may be working with a not-yet-validated mutation should
    check is_valid_dag() first.
    """
    return list(nx.topological_sort(build_graph(workflow)))


def next_ready_node(workflow: Workflow) -> Optional[WorkflowNode]:
    """
    The first PENDING or READY node in topological order.

    This is the graph-aware replacement for Workflow.get_next_node()'s
    plain list-order scan: it respects actual node dependencies (edges)
    rather than insertion order, so it still executes today's linear
    workflows in the same order while correctly generalizing to branching
    or reordered graphs.
    """
    by_id = {node.id: node for node in workflow.nodes}

    for node_id in topological_order(workflow):
        node = by_id.get(node_id)
        if node is not None and node.status in (NodeStatus.PENDING, NodeStatus.READY):
            return node

    return None


def to_node_link_data(workflow: Workflow) -> Dict[str, Any]:
    """JSON-friendly node-link representation of the workflow graph, for
    visualization consumers that want the same structure the runtime
    itself executes against rather than a separately-maintained copy."""
    return nx.node_link_data(build_graph(workflow), edges="edges")
