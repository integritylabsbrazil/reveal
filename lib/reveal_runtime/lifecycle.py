"""Validate Reveal lifecycle transitions at runtime."""

TICKET_ORDER = [
    "discovered", "understood", "questions_pending", "refined", "planned",
    "ready", "implementing", "validating", "reviewing", "completed",
]

TASK_TRANSITIONS = {
    "planned": {"ready", "blocked"},
    "ready": {"in_progress", "blocked"},
    "in_progress": {"validating", "blocked"},
    "validating": {"reviewing", "in_progress", "blocked"},
    "reviewing": {"completed", "in_progress", "blocked"},
    "blocked": {"planned", "ready", "in_progress", "validating", "reviewing"},
    "completed": set(),
}


def normalize(value):
    return str(value or "").strip().lower().replace("-", "_")


def can_transition(current, requested, kind="ticket"):
    current, requested = normalize(current), normalize(requested)
    if current == requested:
        return True
    if kind == "task":
        return requested in TASK_TRANSITIONS.get(current, set())

    # Refinement is the gate between understanding and a stable requirement.
    if current == "understood" and requested in {"questions_pending", "refined"}:
        return True
    if current == "questions_pending" and requested == "refined":
        return True

    try:
        return TICKET_ORDER.index(requested) == TICKET_ORDER.index(current) + 1
    except ValueError:
        return False


def validate_transition(current, requested, kind="ticket"):
    if not can_transition(current, requested, kind):
        raise ValueError(f"Invalid {kind} transition: {current!r} -> {requested!r}")
    return True
