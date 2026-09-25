# Current Work / Resume Model

The Reveal workspace keeps one persistent current-work state instead of creating a directory for every session.

## Files

- `.reveal/current.yaml` — current resumable state.
- `.reveal/history.jsonl` — append-only history of workspace events.

## Current state

`current.yaml` answers which project, ticket and atomic task are active; which reference projects are in context; what was completed and what remains; decisions, open questions and findings; the next action; latest evidence; and the commit associated with the last update.

The file is a snapshot, not an event log. It contains only the state required to resume work safely.

## Resume semantics

A resume operation should:

1. load `.reveal/current.yaml`;
2. verify the referenced project, ticket and task still exist;
3. verify repository and branch context when execution is involved;
4. check whether the tracked commit has changed;
5. surface pending questions, findings and next action;
6. restore the same engineering context without recreating discovery work.

If the state is stale or inconsistent, Reveal should stop and request reconciliation rather than silently rebuilding context.

## History

`history.jsonl` is append-only. Meaningful state transitions add events instead of rewriting previous history.

Typical events include:

- `WORKSPACE_INITIALIZED`
- `PROJECT_SELECTED`
- `TICKET_SELECTED`
- `TASK_SELECTED`
- `STATE_UPDATED`
- `TASK_COMPLETED`
- `EVIDENCE_RECORDED`
- `RESUME_STARTED`
- `RESUME_BLOCKED`
- `WORK_COMPLETED`

History is the audit trail; `current.yaml` is the resumable snapshot.

## Design rule

There are no per-session folders. Stopping and continuing work must preserve context through the current snapshot plus append-only history.
