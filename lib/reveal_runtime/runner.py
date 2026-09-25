"""Coordinate state-driven Reveal execution without owning provider logic."""
from datetime import datetime, timezone
import json
from pathlib import Path

from .context import assemble_context
from .dispatcher import resolve_next_action
from .guards import evaluate
from .state import load_config, load_state
from .persistence import append_history, update_state
from .providers import ProviderInvocation, get_provider
from .validation import validate_repository, next_status
from .engines import apply_analysis, apply_refinement, apply_plan
from .tasks import load_tasks, select_next_task


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

    dispatch = {
        "agent": action.agent,
        "provider": action.provider,
        "action": action.type,
    }
    result = {
        "status": "ready",
        "action": action,
        "guard": guard,
        "context": context,
        "dispatch": dispatch,
    }
    if guard["result"] == "require_review":
        result["status"] = "review_required"
        update_state(root, state, next_action={"type": "REVIEW_REQUIRED", "description": guard["reason"]})
        append_history(root, "RESUME_REQUIRES_REVIEW", action=action.type, reason=guard["reason"])
        return result

    provider = get_provider(action.provider)
    if provider is None:
        reason = f"Provider not supported: {action.provider or '-'}"
        update_state(root, state, next_action={"type": action.type, "description": reason})
        append_history(root, "RESUME_BLOCKED", action=action.type, reason=reason)
        result["status"] = "blocked"
        result["guard"] = {"result": "block", "reason": reason, "checks": ["provider"]}
        return result

    invocation = ProviderInvocation(
        agent=action.agent or "",
        provider=action.provider or provider.name,
        action=action.type,
        context=context,
    )
    provider_result = provider.invoke(invocation, config)
    result["provider_result"] = provider_result.__dict__
    if provider_result.status != "success":
        reason = provider_result.message or "; ".join(provider_result.blockers) or provider_result.status
        update_state(root, state, next_action={"type": action.type, "description": reason})
        append_history(root, "PROVIDER_BLOCKED", action=action.type, provider=provider.name, reason=reason)
        result["status"] = "blocked"
        return result

    if provider_result.status == "success":
        if action.type == "ANALYZE_TICKET":
            ticket = apply_analysis(root, state.get("ticket") or {}, {
                "findings": provider_result.findings,
                "decisions": provider_result.decisions,
                "questions": provider_result.blockers,
            })
            state["ticket"] = {"key": ticket["key"], "status": ticket["status"]}
        elif action.type == "PLAN_TICKET":
            try:
                ticket, tasks = apply_plan(root, state.get("ticket") or {}, {
                    "tasks": provider_result.artifacts,
                })
                state["ticket"] = {"key": ticket["key"], "status": ticket["status"]}
            except ValueError:
                result["status"] = "blocked"
                result["provider_result"]["blockers"] = ["Planning requires a refined ticket."]
                return result

    result["evidence"] = provider_result.evidence
    result["artifacts"] = provider_result.artifacts
    result["findings"] = provider_result.findings
    result["decisions"] = provider_result.decisions
    state["last_evidence"] = provider_result.evidence

    validation = None
    if action.type == "EXECUTE_TASK":
        validation = validate_repository(root, config)
        result["validation"] = validation
        if validation["status"] == "failed":
            update_state(root, state, status="implementing",
                         next_action={"type": "VALIDATE_TASK", "description": "Validation failed; implementation needs correction."})
            append_history(root, "VALIDATION_FAILED", action=action.type, output=validation["output"])
            result["status"] = "failed"
            return result

    transition = next_status(action.type, provider_result.status,
                             validation["status"] if validation else None)
    if transition:
        update_state(root, state, status=transition,
                     next_action={"type": "", "description": ""})
        if transition == "completed" and state.get("ticket", {}).get("key"):
            tasks = load_tasks(root, state["ticket"]["key"])
            nxt = select_next_task(tasks)
            if nxt:
                state["current_task"] = {"key": nxt["key"], "status": nxt.get("status", "ready")}
                update_state(root, state, status="implementing",
                             next_action={"type": "EXECUTE_TASK", "description": f"Next atomic task: {nxt['key']}"})
    else:
        update_state(root, state, next_action={"type": "", "description": ""})
    append_history(
        root,
        "ACTION_COMPLETED",
        action=action.type,
        provider=provider.name,
        evidence=provider_result.evidence,
        artifacts=provider_result.artifacts,
    )
    return result
