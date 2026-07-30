from services.bootstrap import workflow_generator, registry, event_logger
from models.execution import ExecutionState
from runtime.engine import RuntimeEngine
from runtime.policy_engine import PolicyEngine
from runtime.replay import ReplayReader
from policies import (
    LowConfidencePolicy,
    MissingRepoPolicy,
    ContradictionPolicy,
    LowSourcesPolicy,
    ExecutionTimeoutPolicy,
)


def test_backend_execution_and_replay():
    task = "Build a secure REST API in Python"
    workflow = workflow_generator.generate(task)
    assert len(workflow.nodes) > 0
    assert workflow.id is not None

    state = ExecutionState(task=task, workflow=workflow)

    policy_engine = PolicyEngine(
        policies=[
            LowConfidencePolicy(),
            MissingRepoPolicy(),
            ContradictionPolicy(),
            LowSourcesPolicy(),
            ExecutionTimeoutPolicy(),
        ]
    )

    engine = RuntimeEngine(
        policy_engine=policy_engine,
        registry=registry,
        event_logger=event_logger,
    )

    result_state = engine.execute(state)
    assert result_state.status.value == "completed"
    assert len(result_state.events) > 0
    assert result_state.metrics.completed_agents > 0

    reader = ReplayReader(event_logger)
    replay = reader.reconstruct(workflow.id)
    assert replay.workflow_id == workflow.id
    assert len(replay.steps) == len(result_state.events)


if __name__ == "__main__":
    test_backend_execution_and_replay()
    print("test_backend_execution_and_replay PASSED!")
