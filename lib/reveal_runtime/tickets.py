"""Canonical ticket and task persistence for Reveal."""
from pathlib import Path
import yaml


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)


def materialize_ticket(root, ticket):
    key = ticket["key"]
    data = {
        "version": 1, "key": key, "status": ticket.get("status", "discovered"),
        "title": ticket.get("title", ""), "description": ticket.get("description", ""),
        "requirements": ticket.get("requirements", []),
        "acceptance_criteria": ticket.get("acceptance_criteria", []),
        "impact": ticket.get("impact", {}), "decisions": ticket.get("decisions", []),
        "findings": ticket.get("findings", []), "open_questions": ticket.get("open_questions", []),
        "references": ticket.get("references", []),
    }
    _write(Path(root) / ".reveal" / "tickets" / f"{key}.yaml", data)
    return data


def materialize_tasks(root, ticket_key, tasks):
    base = Path(root) / ".reveal" / "tasks"
    base.mkdir(parents=True, exist_ok=True)
    for task in tasks:
        key = task["key"]
        data = {"version": 1, "ticket": ticket_key, **task}
        _write(base / f"{key}.yaml", data)
    return tasks
