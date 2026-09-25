"""Coordinate state-driven Reveal execution without owning provider logic."""
from .context import assemble_context
from .dispatcher import resolve_next_action
from .guards import evaluate
from .state import load_config, load_state
from .persistence import append_history, update_state
from .providers import ProviderInvocation, get_provider
from .validation import validate_repository, next_status
from .engines import apply_analysis, apply_refinement, apply_plan
from .tasks import load_tasks, select_next_task
from .evidence import collect
from .review import evaluate as evaluate_review
from .git import git_info, has_drift


def _expected_commit(state):
    evidence = state.get("last_evidence") or []
    if evidence and isinstance(evidence[0], dict):
        return evidence[0].get("commit", "")
    return (state.get("last_update") or {}).get("commit", "")


def run(root, action_override=None):
    state, _ = load_state(root)
    config = load_config(root)
    context = assemble_context(root)
    action = action_override or resolve_next_action(state, config)
    guard = evaluate(action, state, context)
    append_history(root, "RESUME_STARTED", action=action.type)

    # A task must not continue against a repository state different from the
    # state for which its previous evidence/context was produced.
    if action.type in {"EXECUTE_TASK", "VALIDATE_TASK", "REVIEW_TASK"}:
        expected = _expected_commit(state)
        if expected and has_drift(root, expected):
            reason = f"Repository drift detected: expected {expected}, current {git_info(root).get('commit', '')}."
            update_state(root, state, next_action={"type": "RECONCILE", "description": reason})
            append_history(root, "REPOSITORY_DRIFT", action=action.type, reason=reason)
            return {"status": "blocked", "action": action, "guard": guard, "context": context, "reason": reason}

    if guard["result"] == "block":
        append_history(root, "RESUME_BLOCKED", action=action.type, reason=guard["reason"])
        return {"status": "blocked", "action": action, "guard": guard, "context": context}
    result = {"status": "ready", "action": action, "guard": guard, "context": context,
              "dispatch": {"agent": action.agent, "provider": action.provider, "action": action.type}}
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
        return result

    source_commit = git_info(root).get("commit", "")
    provider_result = provider.invoke(
        ProviderInvocation(agent=action.agent or "", provider=action.provider or provider.name,
                           action=action.type, context=context), config)
    result["provider_result"] = provider_result.__dict__
    if provider_result.status != "success":
        reason = provider_result.message or "; ".join(provider_result.blockers) or provider_result.status
        update_state(root, state, next_action={"type": action.type, "description": reason})
        append_history(root, "PROVIDER_BLOCKED", action=action.type, provider=provider.name, reason=reason)
        result["status"] = "blocked"
        return result

    if action.type == "ANALYZE_TICKET":
        ticket = apply_analysis(root, state.get("ticket") or {}, {
            "findings": provider_result.findings, "decisions": provider_result.decisions,
            "questions": provider_result.blockers})
        state["ticket"] = {"key": ticket["key"], "status": ticket["status"]}
    elif action.type == "ANSWER_QUESTIONS":
        ticket = apply_refinement(root, state.get("ticket") or {}, {
            "requirements": provider_result.findings, "acceptance_criteria": provider_result.artifacts,
            "decisions": provider_result.decisions, "questions": provider_result.blockers})
        state["ticket"] = {"key": ticket["key"], "status": ticket["status"]}
    elif action.type == "PLAN_TICKET":
        try:
            ticket, _ = apply_plan(root, state.get("ticket") or {}, {"tasks": provider_result.artifacts})
            state["ticket"] = {"key": ticket["key"], "status": ticket["status"]}
        except ValueError:
            result["status"] = "blocked"
            result["provider_result"]["blockers"] = ["Planning requires a refined ticket."]
            return result

    validation = None
    if action.type in {"EXECUTE_TASK", "VALIDATE_TASK"}:
        validation = validate_repository(root, config)
        result["validation"] = validation
        if validation["status"] == "failed":
            update_state(root, state, status="implementing",
                         next_action={"type": "EXECUTE_TASK", "description": "Validation failed; implementation needs correction."})
            append_history(root, "VALIDATION_FAILED", action=action.type, output=validation["output"])
            result["status"] = "failed"
            return result

    evidence = collect(root, provider_result.__dict__, validation, source_commit=source_commit)
    result["execution_evidence"] = evidence
    result["evidence"] = provider_result.evidence
    result["artifacts"] = provider_result.artifacts
    result["findings"] = provider_result.findings
    result["decisions"] = provider_result.decisions
    state["last_evidence"] = [evidence]

    transition = next_status(action.type, provider_result.status,
                             validation["status"] if validation else None)
    if transition == "completed":
        review = evaluate_review(state.get("current_task") or {}, evidence, provider_result.__dict__)
        result["review"] = review
        if review["status"] != "approved":
            update_state(root, state, status="reviewing",
                         next_action={"type": "REVIEW_TASK", "description": "Review gate has blockers."})
            append_history(root, "REVIEW_BLOCKED", action=action.type, blockers=review["blockers"])
            result["status"] = "review_required"
            return result

    if transition:
        update_state(root, state, status=transition, next_action={"type": "", "description": ""})
        if transition == "completed" and state.get("ticket", {}).get("key"):
            tasks = load_tasks(root, state["ticket"]["key"])
            nxt = select_next_task(tasks)
            if nxt:
                state["current_task"] = {"key": nxt["key"], "status": nxt.get("status", "ready")}
                update_state(root, state, status="implementing",
                             next_action={"type": "EXECUTE_TASK", "description": f"Next atomic task: {nxt['key']}"})

    append_history(root, "ACTION_COMPLETED", action=action.type, provider=provider.name,
                   evidence=provider_result.evidence, artifacts=provider_result.artifacts)
    return result
