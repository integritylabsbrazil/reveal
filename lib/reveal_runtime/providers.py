"""Provider abstraction and executable command adapter for Reveal agents."""
from dataclasses import dataclass
import json
import os
import subprocess


@dataclass(frozen=True)
class ProviderInvocation:
    agent: str
    provider: str
    action: str
    context: dict


@dataclass(frozen=True)
class ProviderResult:
    status: str
    findings: list
    decisions: list
    artifacts: list
    evidence: list
    blockers: list
    message: str = ""


class Provider:
    name = ""

    def invoke(self, invocation, config=None):
        raise NotImplementedError


class OpenCodeProvider(Provider):
    name = "opencode"

    def invoke(self, invocation, config=None):
        config = config or {}
        provider_config = (config.get("providers") or {}).get("opencode") or {}
        command = provider_config.get("command") or os.environ.get("REVEAL_OPENCODE_COMMAND")

        if not command:
            return ProviderResult(
                status="provider_not_configured",
                findings=[], decisions=[], artifacts=[], evidence=[],
                blockers=["OpenCode command is not configured."],
                message=(
                    "Configure providers.opencode.command in .reveal/config.yaml "
                    "or set REVEAL_OPENCODE_COMMAND."
                ),
            )

        payload = json.dumps({
            "agent": invocation.agent,
            "provider": invocation.provider,
            "action": invocation.action,
            "context": invocation.context,
        }, ensure_ascii=False)

        try:
            completed = subprocess.run(
                command if isinstance(command, list) else command.split(),
                input=payload,
                text=True,
                capture_output=True,
                cwd=provider_config.get("cwd") or None,
                timeout=int(provider_config.get("timeout_seconds", 1800)),
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return ProviderResult(
                status="provider_failed",
                findings=[], decisions=[], artifacts=[], evidence=[],
                blockers=[str(exc)],
                message="Failed to start OpenCode provider.",
            )

        if completed.returncode != 0:
            return ProviderResult(
                status="provider_failed",
                findings=[], decisions=[], artifacts=[], evidence=[],
                blockers=[completed.stderr.strip() or f"exit code {completed.returncode}"],
                message="OpenCode provider returned a non-zero exit code.",
            )

        try:
            result = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError:
            return ProviderResult(
                status="provider_invalid_result",
                findings=[], decisions=[], artifacts=[], evidence=[],
                blockers=["Provider stdout was not valid JSON."],
                message="OpenCode must return the Reveal result envelope as JSON.",
            )

        return ProviderResult(
            status=result.get("status", "success"),
            findings=result.get("findings", []),
            decisions=result.get("decisions", []),
            artifacts=result.get("artifacts", []),
            evidence=result.get("evidence", []),
            blockers=result.get("blockers", []),
            message=result.get("message", ""),
        )


def get_provider(name):
    return {"opencode": OpenCodeProvider()}.get(str(name or "").lower())
