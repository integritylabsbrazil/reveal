"""Coordinate state-driven Reveal execution without owning provider logic."""
from datetime import datetime, timezone
import json
from pathlib import Path

from .context import assemble_context
from .dispatcher import resolve_next_action
from .guards import evaluate
from .state import load_config, load_state


def _event(root, event, **payload):
    path = Path(root) / ".reveal" / "history.jsonl"
    record = {"event": event, "version": 1, "timestamp": datetime.now(timezone.utc).isoformat(), **payload}
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\\n")


def run(root, action_override=None):
    state, _ = load_state(root)
    config = load_config(root)
    context = assemble_context(root)
    action = action_override or resolve_next_action(state, config)
    guard = evaluate(action, state, context)
    _event(root, "RESUME_STARTED", action=action.type)

    if guard["result"] == "block":
        _event(root, "RESUME_BLOCKED", action=action.type, reason=guard["reason"])
        return {"status": "blocked", "action": action, "guard": guard, "context": context}

    result = {
        "status": "ready",
        "action": action,
        "guard": guard,
        "context": context,
        "dispatch": {
            "agent": action.agent,
            "provider": action.provider,
            "action": action.type,
        },
    }
    if guard["result"] == "require_review":
        result["status"] = "review_required"
        _event(root, "RESUME_REQUIRES_REVIEW", action=action.type, reason=guard["reason"])
    else:
        _event(root, "ACTION_DISPATCHED", action=action.type, agent=action.agent, provider=action.provider)
    return result
