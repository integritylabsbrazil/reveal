# Execution Engine

The Execution Engine is the runtime boundary that turns an approved atomic task into controlled repository work and evidence.

## Preconditions

Execution requires:

- a valid project context;
- a canonical ticket;
- an atomic task in `READY`;
- a validated Execution Context;
- effective permissions;
- applicable guards;
- a repository commit and branch context;
- a validation strategy.

Execution must stop if required context is missing, the task scope is invalid, repository state has drifted beyond the accepted context, or a guard blocks the operation.

## Execution flow

```text
READY
  ↓
ASSEMBLE CONTEXT
  ↓
VALIDATE GUARDS
  ↓
PREPARE BRANCH
  ↓
EXECUTE
  ↓
COLLECT CHANGES
  ↓
VALIDATE
  ↓
COLLECT EVIDENCE
  ↓
REVIEW / COMPLETE
```

## Runtime responsibilities

The runtime owns:

- loading and validating the task;
- assembling Execution Context;
- evaluating guards;
- preparing the branch according to task policy;
- invoking the configured provider/agent;
- enforcing task scope;
- collecting changed artifacts;
- running declared validation;
- recording evidence;
- updating current state;
- appending history events;
- handling blocked or failed execution.

The provider performs the reasoning or implementation work. It does not own persistent state transitions.

## Scope enforcement

Before execution, the runtime resolves the task's allowed and forbidden scope. After execution, changed paths are compared against that scope.

Unexpected changes must block completion and trigger review or reconciliation.

## Repository drift

The execution context records the source commit. Before execution, the runtime compares the repository state with that commit.

```text
same commit -> continue
different commit -> revalidate context
unavailable context -> block
```

Drift must not be silently ignored.

## Validation

Validation is task-specific and comes from the task's validation section. The runtime records:

- commands/checks executed;
- exit/result status;
- relevant output or summary;
- build result when applicable;
- test result when applicable.

Validation failure prevents the task from being marked complete.

## Evidence

Execution produces evidence that connects:

```text
Task -> Commit -> Changed Files -> Validation -> Review
```

Evidence is persisted before completion and is required by the evidence guard.

## Failure and recovery

Execution may end as:

- `COMPLETED` — task and validation succeeded;
- `BLOCKED` — execution cannot safely continue;
- `FAILED` — execution ran but did not satisfy validation;
- `REVIEWING` — implementation exists but requires explicit review.

Failure must preserve current state and evidence collected so far so `resume` can continue without losing context.

## Provider independence

The engine invokes providers through the Agent Contract. OpenCode is the default provider today, but the execution lifecycle does not depend on a specific provider.