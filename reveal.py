#!/usr/bin/env python3
"""Reveal runtime CLI.

The user selects only a high-level operation. The runtime determines the
current step from .reveal/current.yaml and owns the transition.
"""
import argparse
import json
from pathlib import Path

from lib.reveal_runtime.context import assemble_context
from lib.reveal_runtime.runner import run
from lib.reveal_runtime.state import load_state


def find_root():
    path = Path.cwd().resolve()
    for candidate in (path, *path.parents):
        if (candidate / ".reveal" / "current.yaml").exists():
            return candidate
    raise SystemExit("Reveal workspace not found: .reveal/current.yaml")


def main():
    parser = argparse.ArgumentParser(prog="reveal")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="show current state and the next runtime action")
    sub.add_parser("resume", help="resume the current work from persistent state")
    args = parser.parse_args()

    root = find_root()

    if args.command == "status":
        state, _ = load_state(root)
        ctx = assemble_context(root)
        action = ctx["action"]
        print(f"workspace: {root}")
        print(f"state: {state.get('status', 'idle')}")
        print(f"project: {(state.get('project') or {}).get('id') or '-'}")
        print(f"ticket: {(state.get('ticket') or {}).get('key') or '-'}")
        print(f"task: {(state.get('current_task') or {}).get('key') or '-'}")
        print(f"next: {action['type']}")
        print(f"agent: {action['agent'] or '-'}")
        print(f"provider: {action['provider'] or '-'}")
        print(f"reason: {action['reason']}")
        return 0

    result = run(root)
    print(json.dumps(_json_safe(result), ensure_ascii=False, indent=2, default=str))
    return 0 if result.get("status") not in {"blocked", "failed"} else 1


def _json_safe(value):
    if hasattr(value, "__dict__"):
        return value.__dict__
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
