from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field
from models.node import WorkflowNode
class WorkflowEdge(BaseModel):
    source: str
    target: str
class Workflow(BaseModel):
    nodes: List[WorkflowNode] = Field(default_factory=list)
    edges: List[WorkflowEdge] = Field(default_factory=list)
    current_node: Optional[str] = None
    history: List[str] = Field(default_factory=list)
    def add_node(self, node: WorkflowNode):
        self.nodes.append(node)
    def add_edge(self, source: str, target: str):
        self.edges.append(
            WorkflowEdge(source=source, target=target)
        )
    def remove_node(self, node_id: str):
        self.nodes = [n for n in self.nodes if n.id != node_id]
        self.edges = [
            edge
            for edge in self.edges
            if edge.source != node_id and edge.target != node_id
        ]
    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    def replace_node(self, old_id: str, new_node: WorkflowNode):
        self.nodes = [
            new_node if n.id == old_id else n
            for n in self.nodes
        ]
        for edge in self.edges:
            if edge.source == old_id:
                edge.source = new_node.id
            if edge.target == old_id:
                edge.target = new_node.id