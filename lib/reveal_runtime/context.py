"""Build the normalized execution context without executing provider work."""
import hashlib
import json

from .dispatcher import resolve_next_action
from .state import load_config, load_state
from .git import git_info
from .project_context import load_project_context
from .references import load_references
from .knowledge import load_knowledge


def _fingerprint(data):
    payload = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def assemble_context(root):
    state, _ = load_state(root)
    config = load_config(root)
    action = resolve_next_action(state, config)
    project_state = state.get("project") or {}
    project_id = project_state.get("id", "")
    project = load_project_context(root, project_id)
    references = load_references(root, state.get("references") or [])
    knowledge = load_knowledge(root, project_id)
    repository = git_info(root)
    defaults = (config.get("defaults") or {}).get("permissions") or {}
    project_permissions = (project.get("config") or {}).get("permissions") or {}
    repo_permissions = project_permissions.get("repository") or defaults.get("target_repository") or {}
    context = {
        "workspace": {"status": state.get("status", "idle")},
        "project": {**project_state, **project},
        "ticket": state.get("ticket") or {},
        "task": state.get("current_task") or {},
        "references": references,
        "knowledge": knowledge,
        "decisions": state.get("decisions") or [],
        "open_questions": state.get("open_questions") or [],
        "findings": state.get("findings") or [],
        "last_evidence": state.get("last_evidence") or [],
        "permissions": {
            "jira": defaults.get("jira", {}),
            "target_repository": repo_permissions,
            "reveal_workspace": defaults.get("reveal_workspace", {}),
        },
        "guards": (config.get("defaults") or {}).get("guards") or {},
        "repository": repository,
        "action": {"type": action.type, "agent": action.agent, "provider": action.provider,
                   "reason": action.reason, "command_hint": action.command_hint},
    }
    context["context_fingerprint"] = _fingerprint(context)
    return context
