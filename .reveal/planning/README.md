# Planning Engine

The Planning Engine transforms a refined requirement into an executable technical plan and a dependency-aware set of atomic tasks. Planning is allowed only when refinement is `READY`.

## Preconditions

Planning requires:

- a canonical ticket;
- a normalized requirement;
- refinement state `READY`;
- defined acceptance criteria;
- known or explicitly recorded dependencies;
- a validation strategy;
- applicable project permissions and guards.

If any required precondition is missing, planning stops and the missing information is returned as a blocker or question.

## Responsibilities

The planner determines:

- implementation strategy;
- affected components and files when known;
- dependencies and execution order;
- expected artifacts;
- validation steps;
- branch strategy;
- task boundaries;
- task risk and complexity;
- where review is required.

Planning must not execute repository changes or silently expand scope.

## Atomic task generation

Each generated task must be independently understandable and verifiable.

Task boundaries should follow coherent objectives rather than arbitrary file counts. Dependencies must be explicit so the runtime can determine a safe execution order.

```text
REQUIREMENT
    ↓
TECHNICAL PLAN
    ↓
DEPENDENCY GRAPH
    ↓
ATOMIC TASKS
    ↓
READY
```

## Dependency graph

Tasks may depend on other tasks. The planner must detect cycles before marking the plan ready.

```yaml
dependencies:
  - task: TASK-0002
    depends_on:
      - TASK-0001
```

A task with unresolved dependencies cannot enter `READY`.

## Task sizing

Task sizing uses:

- `complexity` — implementation difficulty;
- `risk` — probability/impact of failure or unintended change;
- `autonomy` — how independently execution may proceed;
- `requires_review` — whether explicit review is required.

These attributes describe the work, not developer seniority.

## Planning output

The planner produces:

- plan summary;
- implementation approach;
- dependencies;
- atomic tasks;
- execution order;
- validation strategy;
- risks;
- branch strategy;
- unresolved blockers, if any.

Only a complete plan whose tasks have explicit scope and validation should transition to `READY`.

## Traceability

Every task must retain a direct link to the requirement and ticket. The plan must make it possible to trace:

```text
Requirement -> Plan -> Task -> Artifact -> Validation -> Evidence
```

## Provider independence

Planning is an engine contract. Providers may perform reasoning, but task structure, dependency rules, scope boundaries and traceability are controlled by Reveal.