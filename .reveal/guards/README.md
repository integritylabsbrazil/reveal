# Guard Contract

Guards are executable policy boundaries in Reveal. They decide whether an agent or runtime action is allowed to proceed, based on explicit context and permissions.

## Contract

Every guarded action follows:

```text
ACTION -> CONTEXT -> GUARDS -> ALLOW | BLOCK | REQUIRE_REVIEW
```

A guard must be deterministic from the supplied context whenever possible. It must not rely on an agent's subjective judgment to authorize an action.

## Guard types

- `scope` — prevents work outside the approved ticket/task scope.
- `repository` — controls repository reads, writes, branches and target paths.
- `jira` — controls Jira reads/writes according to project permissions.
- `knowledge` — prevents unverified or unauthorized knowledge updates.
- `evidence` — requires sufficient execution evidence before completion.

## Guard result

Every guard evaluation should produce a normalized result:

```yaml
guard:
  id: scope
  version: 1

result: allow
reason: ""

checks: []
required_actions: []

metadata:
  evaluated_at: ""
```

Allowed results are:

- `allow` — the action may proceed.
- `block` — the action must not proceed.
- `require_review` — the action may continue only through an explicit review gate.

## Evaluation rules

1. Guards run before protected actions.
2. A `block` result always stops the action.
3. `require_review` cannot be silently downgraded to `allow` by an agent.
4. Guards receive the current project, ticket/task, permissions and relevant repository/evidence context.
5. Guard decisions are recorded when they materially affect execution.
6. Guard implementations are provider-independent.
7. Changing guard policy requires an explicit configuration change, not an agent decision.

## Scope guard

Validates that proposed files, modules, behavior and artifacts remain inside the task's allowed scope and outside its forbidden scope.

## Repository guard

Validates repository identity, branch strategy, target paths, read/write permission and protected areas before repository actions.

## Jira guard

Validates Jira access mode. The default Reveal policy permits reading Jira but does not grant write access.

## Knowledge guard

Validates provenance, verification status and authorization before changing persistent project knowledge. Auto-update is disabled by default.

## Evidence guard

Validates that required evidence exists before a task or ticket can advance to a completion state. Evidence may include changed files, executed tests, test results, build results and review results.

## Composition

Multiple guards compose conservatively: the most restrictive applicable result wins.

```text
BLOCK > REQUIRE_REVIEW > ALLOW
```

An action is therefore allowed only when every applicable guard allows it.