"""Normalize planner output into dependency-aware atomic tasks."""
from .tasks import materialize_ready_task


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
        tasks.append(task)

    known = {task["key"] for task in tasks}
    for task in tasks:
        task["dependencies"] = [d for d in task["dependencies"] if d in known and d != task["key"]]

    if tasks:
        materialize_ready_task(root, tasks[0])
        tasks[0]["status"] = "ready"
    return tasks
