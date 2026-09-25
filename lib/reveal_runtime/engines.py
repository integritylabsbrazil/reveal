"""Deterministic runtime engines that turn agent output into canonical artifacts."""
from .tickets import materialize_ticket, materialize_tasks
from .lifecycle import validate_transition


def apply_analysis(root, ticket, result):
    data = dict(ticket)
    data["status"] = "understood"
    data["findings"] = result.get("findings", [])
    data["decisions"] = result.get("decisions", [])
    data["open_questions"] = result.get("questions", [])
    materialize_ticket(root, data)
    return data


def apply_refinement(root, ticket, result):
    data = dict(ticket)
    questions = result.get("questions", [])
    if questions:
        data["status"] = "questions_pending"
        data["open_questions"] = questions
    else:
        data["status"] = "refined"
        data["requirements"] = result.get("requirements", data.get("requirements", []))
        data["acceptance_criteria"] = result.get("acceptance_criteria", data.get("acceptance_criteria", []))
        data["decisions"] = result.get("decisions", data.get("decisions", []))
    materialize_ticket(root, data)
    return data


def apply_plan(root, ticket, result):
    validate_transition(ticket.get("status", ""), "planned")
    data = dict(ticket)
    data["status"] = "planned"
    tasks = result.get("tasks", [])
    materialize_ticket(root, data)
    materialize_tasks(root, ticket["key"], tasks)
    return data, tasks
