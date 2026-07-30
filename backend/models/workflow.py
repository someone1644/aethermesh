from __future__ import annotations

from typing import List, Optional

from uuid import uuid4

from pydantic import BaseModel, Field

from models.node import NodeStatus, WorkflowNode


class WorkflowEdge(BaseModel):
    source: str
    target: str


class Workflow(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))

    nodes: List[WorkflowNode] = Field(default_factory=list)

    edges: List[WorkflowEdge] = Field(default_factory=list)

    current_node: Optional[str] = None

    history: List[str] = Field(default_factory=list)

    def add_node(
        self,
        node: WorkflowNode,
    ):
        self.nodes.append(node)

    def add_edge(
        self,
        source: str,
        target: str,
    ):
        self.edges.append(
            WorkflowEdge(
                source=source,
                target=target,
            )
        )

    def remove_node(
        self,
        node_id: str,
    ):
        self.nodes = [
            node
            for node in self.nodes
            if node.id != node_id
        ]

        self.edges = [
            edge
            for edge in self.edges
            if edge.source != node_id
            and edge.target != node_id
        ]

        if self.current_node == node_id:
            self.current_node = None

    def replace_node(
        self,
        old_id: str,
        new_node: WorkflowNode,
    ):
        self.nodes = [
            new_node if node.id == old_id else node
            for node in self.nodes
        ]

        for edge in self.edges:

            if edge.source == old_id:
                edge.source = new_node.id

            if edge.target == old_id:
                edge.target = new_node.id

        if self.current_node == old_id:
            self.current_node = new_node.id

    def get_node(
        self,
        node_id: str,
    ) -> Optional[WorkflowNode]:

        for node in self.nodes:

            if node.id == node_id:
                return node

        return None

    def has_next(self) -> bool:

        return any(
            node.status in (
                NodeStatus.PENDING,
                NodeStatus.READY,
            )
            for node in self.nodes
        )

    def get_next_node(
        self,
    ) -> Optional[WorkflowNode]:

        for node in self.nodes:

            if node.status in (
                NodeStatus.PENDING,
                NodeStatus.READY,
            ):

                self.current_node = node.id

                return node

        return None

    def mark_running(
        self,
        node_id: str,
    ):

        node = self.get_node(node_id)

        if node:

            node.status = NodeStatus.ACTIVE

            self.current_node = node.id

    def mark_completed(
        self,
        node_id: str,
    ):

        node = self.get_node(node_id)

        if node:

            node.status = NodeStatus.COMPLETED

            self.history.append(node.id)

            self.current_node = None

    def mark_failed(
        self,
        node_id: str,
    ):

        node = self.get_node(node_id)

        if node:

            node.status = NodeStatus.FAILED

            self.current_node = None

    def mark_ready(
        self,
        node_id: str,
    ):

        node = self.get_node(node_id)

        if node:

            node.status = NodeStatus.READY

    def reset(self):

        self.current_node = None

        self.history.clear()

        for node in self.nodes:

            node.status = NodeStatus.PENDING