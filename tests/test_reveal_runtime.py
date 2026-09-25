import pytest

from lib.reveal_runtime.git import has_drift
from lib.reveal_runtime.lifecycle import can_transition, validate_transition
from lib.reveal_runtime.planner import PlanningError, normalize_tasks


def test_ticket_refinement_can_skip_questions_when_complete():
    assert can_transition("understood", "refined")
    assert can_transition("understood", "questions_pending")
    assert can_transition("questions_pending", "refined")


def test_invalid_ticket_transition_is_rejected():
    with pytest.raises(ValueError):
        validate_transition("discovered", "planned")


def test_planner_rejects_duplicate_keys(tmp_path):
    with pytest.raises(PlanningError):
        normalize_tasks(
            tmp_path,
            "PROJ-1",
            [{"key": "TASK-1"}, {"key": "TASK-1"}],
        )


def test_planner_rejects_cycles(tmp_path):
    with pytest.raises(PlanningError):
        normalize_tasks(
            tmp_path,
            "PROJ-1",
            [
                {"key": "TASK-1", "dependencies": ["TASK-2"]},
                {"key": "TASK-2", "dependencies": ["TASK-1"]},
            ],
        )


def test_planner_marks_only_dependency_free_task_ready(tmp_path):
    tasks = normalize_tasks(
        tmp_path,
        "PROJ-1",
        [
            {"key": "TASK-1"},
            {"key": "TASK-2", "dependencies": ["TASK-1"]},
        ],
    )
    assert tasks[0]["status"] == "ready"
    assert tasks[1]["status"] == "planned"


def test_has_drift_is_safe_without_expected_commit(monkeypatch, tmp_path):
    assert has_drift(tmp_path, "") is False
