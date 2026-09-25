#!/usr/bin/env python3
"""Reveal runtime CLI.

The user chooses a high-level operation; the runtime determines the current
step from .reveal/current.yaml instead of requiring manual pipeline commands.
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
        state, path = load_state(root)
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

    ctx = assemble_context(root)
    print(json.dumps(ctx, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
