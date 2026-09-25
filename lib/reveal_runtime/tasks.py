"""Task graph and automatic next-task selection."""
from pathlib import Path
import yaml


def load_tasks(root, ticket_key):
    base = Path(root) / ".reveal" / "tasks"
    if not base.exists():
        return []
    tasks = []
    for path in sorted(base.glob("*.yaml")):
        with path.open(encoding="utf-8") as fh:
            task = yaml.safe_load(fh) or {}
        if task.get("ticket") == ticket_key:
            tasks.append(task)
    return tasks


def dependencies_satisfied(task, tasks):
    by_key = {t.get("key"): t for t in tasks}
    return all(
        str(by_key.get(dep, {}).get("status", "")).lower() == "completed"
        for dep in task.get("dependencies", [])
    )


def select_next_task(tasks):
    for task in sorted(tasks, key=lambda x: x.get("key", "")):
        status = str(task.get("status", "")).lower()
        if status in {"planned", "ready"} and dependencies_satisfied(task, tasks):
            return task
    return None


def materialize_ready_task(root, task):
    path = Path(root) / ".reveal" / "tasks" / f"{task['key']}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    task = dict(task)
    task["status"] = "ready"
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(task, fh, sort_keys=False, allow_unicode=True)
    return task
