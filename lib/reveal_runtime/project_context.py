"""Load persistent target-project context for Reveal agents."""
from pathlib import Path
import yaml

def _load(path):
    path = Path(path)
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}

def load_project_context(root, project_id=""):
    if not project_id:
        return {}
    project_dir = Path(root) / ".reveal" / "projects" / project_id
    project = _load(project_dir / "project.yaml")
    config = _load(project_dir / "config.yaml")
    baseline = _load(project_dir / "baseline.yaml")
    return {"id": project_id, "project": project.get("project", {}),
            "technology": project.get("technology", {}),
            "architecture": project.get("architecture", {}),
            "integrations": project.get("integrations", []),
            "conventions": project.get("conventions", []),
            "config": config, "baseline": baseline.get("project", baseline)}
