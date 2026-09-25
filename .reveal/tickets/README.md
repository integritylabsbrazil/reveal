# Tickets

A ticket is the canonical work context for a change in a target project.

The ticket model connects business intent to technical execution:

```text
problem
  ↓
requirement
  ↓
impact
  ↓
decisions
  ↓
plan
  ↓
atomic tasks
  ↓
validation
  ↓
evidence
```

The ticket is not merely a copy of Jira. Jira is an external source of work information; Reveal enriches that information with technical context, impact, decisions, planning, validation and traceability.

## Lifecycle

Tickets may move through:

```text
DISCOVERED
→ UNDERSTOOD
→ QUESTIONS_PENDING
→ REFINED
→ PLANNED
→ READY
→ IMPLEMENTING
→ VALIDATING
→ REVIEWING
→ COMPLETED
```

State transitions must be supported by evidence or explicit decisions where required.

## Canonical source

The Reveal ticket model is the canonical representation of the engineering context generated for the ticket. Renderers may later produce Jira descriptions, Markdown, agent context and other views from it.

Generated views must not become independent sources of truth.
