# Atomic Tasks

An atomic task is the smallest independently executable and verifiable unit of work generated from a ticket.

A task must have a clear objective, bounded scope, dependencies, acceptance criteria and validation strategy.

## Principles

- one coherent objective per task
- explicit scope and expected artifacts
- independently verifiable result
- dependencies are explicit
- branch planning is tied to the task when applicable
- execution must produce evidence
- tasks must not silently expand their scope

## Task model

```text
TASK
├── identity
├── objective
├── scope
├── dependencies
├── expected artifacts
├── acceptance
├── validation
├── risk
├── complexity
├── autonomy
├── review
├── branch
├── status
└── evidence
```

The model deliberately avoids assigning a developer seniority level. Execution should be described by complexity, risk, autonomy and review requirements instead.

## Task lifecycle

```text
PLANNED
→ READY
→ IN_PROGRESS
→ BLOCKED
→ VALIDATING
→ REVIEWING
→ COMPLETED
```

A task may return to an earlier state when validation or review identifies a problem.

## Traceability

Every task belongs to a ticket and should be traceable to:

```text
ticket
  ↓
requirement
  ↓
task
  ↓
changed artifacts
  ↓
validation
  ↓
evidence
```

This allows Reveal to determine not only what should be changed, but what was actually changed and how the result was validated.
