# Requirement and Refinement Engine

The Requirement Engine converts analyzed ticket context into a precise engineering requirement. The Refinement Engine determines whether that requirement is sufficiently understood to allow planning and atomic task generation.

## Responsibilities

### Requirement

Produce a normalized requirement from:

- original problem;
- business context;
- expected outcome;
- functional requirements;
- non-functional requirements;
- acceptance criteria;
- technical impact;
- verified findings;
- explicit decisions.

The requirement must preserve the distinction between business intent and technical implementation.

### Refinement

Evaluate whether the available context is sufficient for planning.

The refinement engine should identify:

- unresolved requirements;
- ambiguous acceptance criteria;
- missing technical information;
- missing dependencies;
- unresolved architectural decisions;
- missing validation strategy;
- scope risks.

## Refinement gate

The engine produces one of three normalized states:

- `READY` — sufficient context exists to plan;
- `QUESTIONS_PENDING` — clarification is required;
- `BLOCKED` — a critical dependency or decision prevents safe planning.

The runtime owns the actual ticket lifecycle transition.

```text
ANALYSIS
   ↓
REQUIREMENT
   ↓
REFINEMENT
   ├── QUESTIONS_PENDING
   ├── BLOCKED
   └── READY
          ↓
       PLANNING
```

## Question model

Every refinement question should explain why it matters and what decision it unlocks.

```yaml
question:
  id: ""
  category: requirement
  question: ""
  reason: ""
  blocking: true
  resolved: false
```

Questions should be closed with an explicit answer or decision. The engine must not invent answers to remove a blocker.

## Acceptance criteria

Acceptance criteria must be testable and traceable to the requirement. Criteria that cannot be validated should remain unresolved rather than being treated as complete.

## Scope

Refinement may clarify or narrow scope, but it must not silently expand the requested work. Material scope changes require an explicit decision and should be reflected in the canonical ticket context.

## Output

The engine produces a refinement result containing:

- normalized requirement;
- acceptance criteria;
- resolved decisions;
- remaining questions;
- scope boundaries;
- validation strategy;
- readiness state;
- blockers;
- provenance.

Only a `READY` result should unlock executable planning and atomic task generation.