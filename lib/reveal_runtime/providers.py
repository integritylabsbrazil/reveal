"""Provider abstraction for Reveal agents.

Providers are adapters: the runtime owns state and policy; providers only
receive an immutable invocation package and return a structured result.
"""
from dataclasses import dataclass


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

    def invoke(self, invocation):
        raise NotImplementedError


class OpenCodeProvider(Provider):
    name = "opencode"

    def invoke(self, invocation):
        return ProviderResult(
            status="provider_not_configured",
            findings=[], decisions=[], artifacts=[], evidence=[],
            blockers=["OpenCode provider adapter is not configured for execution."],
            message=(
                "The runtime prepared the OpenCode invocation, but no executable "
                "provider command is configured."
            ),
        )


def get_provider(name):
    providers = {"opencode": OpenCodeProvider()}
    return providers.get(str(name or "").lower())
