"""Build the normalized execution context without executing provider work."""
from .state import load_config, load_state


def assemble_context(root):
    state, _ = load_state(root)
    config = load_config(root)
    action = __import__("lib.reveal_runtime.dispatcher", fromlist=["resolve_next_action"]).resolve_next_action(state, config)
    return {
        "workspace": {"status": state.get("status", "idle")},
        "project": state.get("project") or {},
        "ticket": state.get("ticket") or {},
        "task": state.get("current_task") or {},
        "references": state.get("references") or [],
        "decisions": state.get("decisions") or [],
        "open_questions": state.get("open_questions") or [],
        "findings": state.get("findings") or [],
        "last_evidence": state.get("last_evidence") or [],
        "action": {
            "type": action.type,
            "agent": action.agent,
            "provider": action.provider,
            "reason": action.reason,
            "command_hint": action.command_hint,
        },
    }
