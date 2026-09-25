"""Normalize planner output into dependency-aware atomic tasks."""
from .tasks import materialize_ready_task


class PlanningError(ValueError):
    """Raised when planner output cannot form a safe task graph."""


def _has_cycle(tasks):
    graph = {task["key"]: set(task.get("dependencies", [])) for task in tasks}
    visiting, visited = set(), set()

    def visit(key):
        if key in visiting:
            return True
        if key in visited:
            return False
        visiting.add(key)
        if any(visit(dep) for dep in graph.get(key, ())):
            return True
        visiting.remove(key)
        visited.add(key)
        return False

    return any(visit(key) for key in graph)


def normalize_tasks(root, ticket_key, raw_tasks):
    tasks = []
    for index, raw in enumerate(raw_tasks, 1):
        task = dict(raw)
        task.setdefault("key", f"TASK-{index:04d}")
        task["ticket"] = ticket_key
        task.setdefault("status", "planned")
        task.setdefault("dependencies", [])
        task.setdefault("scope", {})
        task.setdefault("acceptance", [])
        task.setdefault("validation", {})
        task.setdefault("complexity", "medium")
        task.setdefault("risk", "medium")
        task.setdefault("autonomy", "bounded")
        task.setdefault("requires_review", True)
        tasks.append(task)

    keys = [task["key"] for task in tasks]
    if len(keys) != len(set(keys)):
        raise PlanningError("Planner produced duplicate task keys.")

    known = set(keys)
    for task in tasks:
        task["dependencies"] = [d for d in task["dependencies"] if d in known and d != task["key"]]
    if _has_cycle(tasks):
        raise PlanningError("Planner produced a cyclic task dependency graph.")

    if tasks:
        materialize_ready_task(root, tasks[0])
        tasks[0]["status"] = "ready"
    return tasks
