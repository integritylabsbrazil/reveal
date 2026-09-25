"""Runtime validation and execution lifecycle mapping."""
from pathlib import Path
import subprocess


def validate_repository(root, config=None):
    config = config or {}
    settings = config.get("validation") or {}
    command = settings.get("command") or ""
    if not command:
        return {"status": "not_configured", "checks": [], "output": ""}
    try:
        p = subprocess.run(
            command if isinstance(command, list) else command.split(),
            cwd=Path(root), text=True, capture_output=True,
            timeout=int(settings.get("timeout_seconds", 1800)), check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status": "failed", "checks": [], "output": str(exc)}
    return {"status": "passed" if p.returncode == 0 else "failed",
            "checks": [command], "output": (p.stdout + "\n" + p.stderr).strip()}


def next_status(action_type, provider_status, validation_status=None):
    if provider_status != "success":
        return "failed"
    if action_type == "EXECUTE_TASK":
        return "validating"
    if action_type == "VALIDATE_TASK":
        return "reviewing" if validation_status in {"passed", "not_configured"} else "implementing"
    if action_type == "REVIEW_TASK":
        return "completed"
    return None
