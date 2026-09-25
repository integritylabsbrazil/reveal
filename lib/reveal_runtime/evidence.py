"""Evidence chain enforcement for completed Reveal tasks."""
from .git import git_info


def collect(root, provider_result, validation=None, *, source_commit=""):
    repo = git_info(root)
    return {
        "source_commit": source_commit,
        "commit": repo.get("commit", ""),
        "branch": repo.get("branch", ""),
        "dirty": repo.get("dirty", False),
        "changed_files": repo.get("changed_files", []),
        "tests": (validation or {}).get("checks", []),
        "validation": (validation or {}).get("status", "not_run"),
        "provider_evidence": provider_result.get("evidence", []),
    }


def can_complete(evidence):
    return (
        bool(evidence.get("commit"))
        and evidence.get("validation") in {"passed", "not_configured"}
        and bool(evidence.get("commit") != evidence.get("source_commit") or evidence.get("changed_files"))
    )
