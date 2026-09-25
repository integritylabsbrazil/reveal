# Agent Contract

Agents are bounded workers in the Reveal runtime. An agent receives context, performs a defined responsibility, produces structured outputs, and returns control to workspace state.

## Contract

Every agent invocation has five parts:

INPUT CONTEXT -> RESPONSIBILITY -> ALLOWED ACTIONS -> OUTPUTS -> STATE TRANSITION

### Input context

An agent may receive project configuration, verified baseline knowledge, canonical ticket context, current atomic task, selected reference projects, prior decisions/findings/open questions, repository context, and previous evidence when applicable.

The agent must not assume context that was not provided or verified.

### Responsibilities

- `analyst` — understand the problem, requirements, impact and unknowns.
- `planner` — turn refined context into an executable plan and atomic tasks.
- `executor` — perform the approved task within scope and record evidence.
- `reviewer` — validate implementation, evidence, acceptance and guard compliance.

An agent must not silently take over another agent's responsibility.

### Allowed actions

Actions are constrained by active project permissions and guards. The agent contract does not grant permissions by itself.

Typical capabilities include reading project knowledge, ticket/task context and reference projects; inspecting repository state; proposing changes; executing approved tasks when permitted; and recording findings, decisions and evidence.

Writes to Jira, target repositories or Reveal knowledge require explicit permission and applicable guards.

### Outputs

Agent output must be structured and attributable. Depending on the role, outputs may include findings, requirement clarifications, impact analysis, decisions or proposals, plans, atomic tasks, changed artifacts, validation results, review findings, evidence, blockers and open questions.

No meaningful output should exist only in an agent conversation.

### State transition

After successful execution, the runtime updates `.reveal/current.yaml` and appends the corresponding event to `.reveal/history.jsonl`.

Agents do not rewrite history and do not independently redefine lifecycle state.

## Non-negotiable rules

1. Scope comes from the canonical ticket/task context.
2. Missing information becomes an explicit question or blocker.
3. Reference projects are read-only.
4. Evidence is required for completed execution.
5. Knowledge updates require their knowledge guard.
6. An agent cannot silently expand task scope.
7. Failed validation returns work to an appropriate earlier state.
8. The runtime, not the model, owns persistent state transitions.

## Agent result envelope

```yaml
agent:
  id: analyst
  invocation_id: ""

result:
  status: success
  findings: []
  decisions: []
  questions: []
  artifacts: []
  evidence: []
  blockers: []

state:
  requested_transition: ""

metadata:
  started_at: ""
  completed_at: ""
```

`requested_transition` is a proposal to the runtime. The runtime validates guards and lifecycle rules before applying it.

## Provider independence

Agent contracts are provider-independent. OpenCode, Claude, Codex or another provider may implement an agent, but the provider must honor the same input, permission, output and state-transition contract.