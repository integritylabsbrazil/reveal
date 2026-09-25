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
    changed = [line[3:] for line in status.splitlines() if len(line) >= 4]
    return {"commit": commit, "branch": branch, "dirty": bool(status), "changed_files": changed}
