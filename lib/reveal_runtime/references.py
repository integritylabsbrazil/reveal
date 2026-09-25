"""Load explicitly selected, read-only reference projects."""
from pathlib import Path
import yaml

def _load(path):
    path = Path(path)
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}

def load_references(root, references):
    base = Path(root) / ".reveal" / "references"
    selected = []
    for item in references or []:
        ref_id = item.get("id") if isinstance(item, dict) else str(item)
        if not ref_id:
            continue
        data = _load(base / f"{ref_id}.yaml")
        if data:
            ref = dict(data.get("reference", data))
            ref["read_only"] = True
            selected.append(ref)
    return selected
