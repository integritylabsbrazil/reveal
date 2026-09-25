# Analysis and Comparison Engine

The Analysis Engine turns normalized execution context into structured engineering findings. The Comparison Engine evaluates the target project against explicitly selected reference projects without treating the reference as a source of truth.

## Engine responsibilities

### Analysis

The analysis engine should identify:

- problem and requirement understanding;
- affected modules, components and integrations;
- technical dependencies;
- risks and unknowns;
- relevant project conventions;
- candidate decisions;
- questions that must be resolved before planning;
- evidence needed to validate the analysis.

Analysis must distinguish verified facts, inferred findings and unresolved questions.

### Comparison

The comparison engine should identify:

- target/reference similarities;
- target/reference differences;
- relevant architectural or implementation patterns;
- migration implications;
- conventions that differ;
- testing and validation differences;
- risks of copying a reference pattern without adaptation.

Comparison is descriptive. It does not automatically declare the reference to be correct or superior.

## Inputs

Both engines consume the normalized Execution Context.

Additional comparison input must include one or more explicitly selected reference projects. References are read-only and their findings remain attributable to the source.

## Outputs

The engines produce structured findings that can be persisted into ticket context, current work state, or knowledge only through the appropriate guards.

```text
ANALYSIS
  -> findings
  -> impact
  -> questions
  -> decisions
  -> risks

COMPARISON
  -> similarities
  -> differences
  -> patterns
  -> migration_implications
  -> validation_implications
```

## Confidence and provenance

Every finding should identify its source and confidence:

- `verified` — directly supported by project/repository evidence;
- `inferred` — derived from available evidence;
- `unknown` — requires confirmation.

Reference-derived findings must identify the reference project. Comparative findings must identify both target and reference sources.

## Refinement gate

Analysis feeds the ticket lifecycle. Planning should not generate executable tasks while required questions or critical unknowns remain unresolved.

```text
DISCOVERED
   ↓
UNDERSTOOD
   ↓
QUESTIONS_PENDING ──┐
   ↓                │
REFINED <───────────┘
   ↓
PLANNED
```

The engine may identify that refinement is incomplete, but the runtime owns the lifecycle transition.

## Knowledge boundary

The analysis engine may propose knowledge updates, but it must not silently mutate persistent knowledge. Knowledge changes pass through the knowledge guard and retain provenance.

## Provider independence

Analysis and comparison are engine contracts, not provider contracts. OpenCode or another provider may implement the reasoning step, while the engine owns input/output normalization and provenance rules.