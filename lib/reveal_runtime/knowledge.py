"""Read persistent Reveal knowledge without mutating it."""
from pathlib import Path
import yaml

def load_knowledge(root, project_id=""):
    baseline_path = Path(root) / ".reveal" / "projects" / project_id / "baseline.yaml"
    if not baseline_path.exists():
        return {"target": [], "reference": [], "comparative": []}
    with baseline_path.open(encoding="utf-8") as fh:
        baseline = yaml.safe_load(fh) or {}
    project = baseline.get("project", baseline)
    return {"target": [{"source": project_id, "type": "baseline", "verified": True, "data": project}],
            "reference": [], "comparative": []}
