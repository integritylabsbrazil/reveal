"""Repository inspection helpers used by the runtime."""
from pathlib import Path
import subprocess


def git_info(root):
    root = Path(root)
    def run(*args):
        p = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
        return p.stdout.strip() if p.returncode == 0 else ""
    return {"commit": run("rev-parse", "HEAD"), "branch": run("branch", "--show-current"),
            "dirty": bool(run("status", "--porcelain"))}
