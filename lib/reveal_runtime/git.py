"""Repository inspection helpers used by the runtime."""
from pathlib import Path
import subprocess


def _run(root, *args):
    p = subprocess.run(["git", *args], cwd=Path(root), text=True, capture_output=True, check=False)
    return p.stdout.strip() if p.returncode == 0 else ""


def git_info(root):
    commit = _run(root, "rev-parse", "HEAD")
    branch = _run(root, "branch", "--show-current")
    status = _run(root, "status", "--porcelain")
    changed = []
    for line in status.splitlines():
        if len(line) < 4:
            continue
        # Porcelain v1 uses two status columns followed by a space.
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        changed.append(path)
    return {
        "commit": commit,
        "branch": branch,
        "dirty": bool(status),
        "changed_files": changed,
    }


def has_drift(root, expected_commit):
    """Return whether HEAD differs from an expected repository commit."""
    expected = str(expected_commit or "").strip()
    if not expected:
        return False
    current = git_info(root).get("commit", "")
    return bool(current and current != expected)
