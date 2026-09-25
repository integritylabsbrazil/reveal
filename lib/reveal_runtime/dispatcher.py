"""Determine the next Reveal action from persistent state.

This module deliberately returns an internal action, rather than asking the user
which shell script to run. Providers/agents can consume this action later.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Action:
    type: str
    agent: str | None
    provider: str | None
    reason: str
    command_hint: str | None = None


def resolve_next_action(state, config=None):
    config = config or {}
    status = str(state.get("status") or "idle").lower()
    ticket = state.get("ticket") or {}
    task = state.get("current_task") or {}
    ticket_status = str(ticket.get("status") or "").lower()
    task_status = str(task.get("status") or "").lower()
    agents = config.get("agents") or {}
    default_provider = (config.get("reveal") or {}).get("default_agent") or "opencode"

    if status in {"blocked", "failed"}:
        return Action("RECONCILE", None, None,
                       "Workspace is blocked/failed; reconcile state before continuing.")
    if task_status in {"blocked"} or ticket_status in {"questions_pending", "blocked"}:
        return Action("ANSWER_QUESTIONS", "analyst", agents.get("analysis", default_provider),
                       "Open questions or blockers must be resolved before planning/execution.")
    if task_status in {"validating"} or status == "validating":
        return Action("VALIDATE_TASK", "reviewer", agents.get("review", default_provider),
                       "Current task is ready for validation.")
    if task_status in {"reviewing"} or status == "reviewing":
        return Action("REVIEW_TASK", "reviewer", agents.get("review", default_provider),
                       "Current task is awaiting review.")
    if task_status in {"ready", "in_progress"} or status == "implementing":
        return Action("EXECUTE_TASK", "executor", agents.get("execution", default_provider),
                       "A current atomic task can be executed by the runtime.")
    if ticket_status in {"discovered", "understood", ""} and ticket.get("key"):
        return Action("ANALYZE_TICKET", "analyst", agents.get("analysis", default_provider),
                       "Ticket needs technical analysis before refinement.")
    if ticket_status == "refined" or status == "refined":
        return Action("PLAN_TICKET", "planner", agents.get("planning", default_provider),
                       "Refinement is ready; planning can generate atomic tasks.")
    if ticket_status == "planned" or status == "planned":
        return Action("PREPARE_TASKS", "planner", agents.get("planning", default_provider),
                       "Plan exists; runtime should materialize dependency-aware tasks.")
    if status == "idle":
        return Action("SELECT_WORK", None, None,
                      "No active work is selected; select or initialize a project/ticket/task.")
    if ticket_status == "completed" or status == "completed":
        return Action("WORK_COMPLETE", None, None, "Current work is complete.")
    return Action("INSPECT_STATE", None, None,
                  f"No safe transition is defined for status={status!r}, task_status={task_status!r}.")
