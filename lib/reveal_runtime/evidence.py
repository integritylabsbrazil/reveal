"""Evidence chain enforcement for completed Reveal tasks."""
from .git import git_info


def collect(root, provider_result, validation=None):
    repo = git_info(root)
    return {
        "commit": repo.get("commit", ""),
        "branch": repo.get("branch", ""),
        "dirty": repo.get("dirty", False),
        "changed_files": repo.get("changed_files", []),
        "tests": (validation or {}).get("checks", []),
        "validation": (validation or {}).get("status", "not_run"),
        "provider_evidence": provider_result.get("evidence", []),
    }


def can_complete(evidence):
    return bool(evidence.get("commit")) and evidence.get("validation") in {"passed", "not_configured"}
