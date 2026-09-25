# Projects

Reveal supports multiple target projects in the same workspace.

Each project has its own configuration and persistent engineering knowledge. Project-specific settings must not be stored in the global Reveal configuration.

Recommended structure:

```text
.reveal/
├── config.yaml
├── projects/
│   ├── <project-id>/
│   │   ├── config.yaml
│   │   ├── baseline.yaml
│   │   ├── architecture.yaml
│   │   ├── domains.yaml
│   │   ├── modules.yaml
│   │   ├── technologies.yaml
│   │   ├── conventions.yaml
│   │   └── decisions/
│   └── ...
├── references/
├── tickets/
├── tasks/
├── evidence/
├── current.yaml
└── history.jsonl
```

A project configuration may define repository access, Jira permissions, technologies, references, agent overrides and project-specific guards.

The global `.reveal/config.yaml` defines Reveal-wide defaults. A project configuration may override those defaults where explicitly allowed.

Project knowledge belongs to the project. For example, BPM and BFF must have independent baselines because their architecture, modules, technologies and conventions can differ.

Reference projects remain read-only and are selected explicitly by the target project or task.
