"""Review gate for Reveal task completion."""


def evaluate(task, evidence, provider_result):
    blockers = []
    if not task.get("key"):
        blockers.append("Task key is missing.")
    if not evidence.get("commit"):
        blockers.append("No repository commit captured.")
    if evidence.get("validation") == "failed":
        blockers.append("Validation failed.")
    if not (evidence.get("changed_files") or evidence.get("provider_evidence") or provider_result.get("artifacts")):
        blockers.append("No implementation evidence or changed artifacts returned.")
    return {
        "status": "approved" if not blockers else "changes_requested",
        "blockers": blockers,
    }
