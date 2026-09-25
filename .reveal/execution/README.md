# Execution Context

Execution Context is the normalized runtime package delivered to an agent for one operation. It makes agent execution reproducible and provider-independent.

## Purpose

The context answers:

- what project is active;
- what ticket and atomic task are being executed;
- what verified project knowledge is available;
- which reference projects are selected;
- what decisions and findings already exist;
- which permissions and guards apply;
- what repository state is relevant;
- what evidence already exists;
- what the agent is expected to produce.

Providers must consume this normalized context rather than rebuilding engineering context independently.

## Context layers

```text
Workspace
  -> Project
      -> Ticket
          -> Task
              -> References
              -> Knowledge
              -> Decisions / Findings
              -> Permissions / Guards
              -> Repository
              -> Evidence
```

### Workspace

Contains current state, lifecycle information and resume metadata.

### Project

Contains project identity, repository, technologies, architecture, conventions, permissions and verified baseline knowledge.

### Ticket

Contains the canonical engineering problem, requirements, acceptance criteria, impact, decisions, plan and traceability.

### Task

Contains the atomic execution scope, dependencies, expected artifacts, acceptance, validation strategy, risk, complexity, autonomy and review requirement.

### References

Contains explicitly selected read-only reference projects and the reason each is relevant.

### Knowledge

Contains only knowledge that is available and attributable to the target project or an explicitly selected reference.

### Permissions and guards

Contains the effective permissions and guard policies applicable to the operation. The agent receives these as constraints, not as suggestions.

### Repository

Contains the relevant repository identity, branch/commit context and allowed paths. Execution context must identify the commit used for analysis so drift can be detected.

### Evidence

Contains relevant prior evidence and defines what new evidence is expected from the operation.

## Context rules

1. Context is assembled by the runtime, not by the provider.
2. Missing required context blocks execution.
3. Unverified knowledge is not presented as verified baseline knowledge.
4. Reference information remains attributable to its source.
5. The task scope is narrower than the ticket scope.
6. Permissions never expand because a provider requests them.
7. Repository drift must be detectable from the recorded commit.
8. Context is immutable during an invocation; changes become new runtime state after the operation.
9. Sensitive or irrelevant context should not be included unnecessarily.

## Context identity

Each execution context should have a stable invocation identifier and a context fingerprint. The fingerprint lets the runtime determine whether an agent is operating on the context that was actually prepared.

## Lifecycle

```text
ASSEMBLE -> VALIDATE -> DELIVER -> EXECUTE -> COLLECT -> PERSIST
```

Before execution, the runtime assembles and validates context. After execution, outputs and evidence are collected, guards are re-evaluated where required, and persistent state is updated.