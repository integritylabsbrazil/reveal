"""Persistent Reveal workspace state loader."""
from pathlib import Path
import yaml


def load_state(root):
    root = Path(root)
    path = root / ".reveal" / "current.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Reveal state not found: {path}")
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data, path


def load_config(root):
    path = Path(root) / ".reveal" / "config.yaml"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}
