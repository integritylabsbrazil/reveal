"""Safe persistence helpers for Reveal runtime state and history."""
from datetime import datetime, timezone
import json
from pathlib import Path
import yaml


def update_state(root, state, *, next_action=None, status=None):
    root = Path(root)
    path = root / ".reveal" / "current.yaml"
    if status is not None:
        state["status"] = status
    if next_action is not None:
        state["next_action"] = next_action
    state["last_update"] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "commit": (state.get("last_update") or {}).get("commit", ""),
    }
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(state, fh, sort_keys=False, allow_unicode=True)


def append_history(root, event, **payload):
    path = Path(root) / ".reveal" / "history.jsonl"
    record = {"event": event, "version": 1,
              "timestamp": datetime.now(timezone.utc).isoformat(), **payload}
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\\n")
