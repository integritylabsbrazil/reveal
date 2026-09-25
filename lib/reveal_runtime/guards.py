"""Runtime guards for protected Reveal actions."""


def evaluate(action, state, context):
    checks = []
    task = state.get("current_task") or {}
    permissions = context.get("permissions") or {}
    repository = permissions.get("target_repository") or {}

    if action.type == "EXECUTE_TASK":
        if not task.get("key"):
            return {"result": "block", "reason": "No current task selected.", "checks": ["task_selected"]}
        if str(task.get("status", "")).lower() not in {"ready", "in_progress"}:
            return {"result": "block", "reason": "Current task is not executable.", "checks": ["task_status"]}
        if repository.get("read") is not True:
            return {"result": "block", "reason": "Target repository read permission is disabled.", "checks": ["repository_read"]}
        if repository.get("write") is not True:
            return {"result": "require_review", "reason": "Target repository write permission is disabled.", "checks": ["repository_write"]}
        checks.extend(["task_selected", "task_status", "repository_read", "repository_scope"])

    if action.type in {"PLAN_TICKET", "PREPARE_TASKS"} and not (state.get("ticket") or {}).get("key"):
        return {"result": "block", "reason": "No canonical ticket selected.", "checks": ["ticket_selected"]}

    if action.type in {"ANALYZE_TICKET", "ANSWER_QUESTIONS", "PLAN_TICKET"}:
        if (permissions.get("jira") or {}).get("read") is not True:
            return {"result": "block", "reason": "Jira read permission is disabled.", "checks": ["jira_read"]}

    return {"result": "allow", "reason": "All applicable guards passed.", "checks": checks}
