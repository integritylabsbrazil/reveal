# Projects

A Reveal workspace can contain multiple target projects.

Each project has its own identity, repository, technology context, permissions, guards and persistent engineering knowledge.

Project-specific knowledge must remain isolated. For example, BPM and BFF can have different architectures, technologies, conventions and access policies.

## Project model

Each project is represented by:

- `config.yaml` — project-specific operational configuration
- `project.yaml` — project identity and technical profile
- `baseline.yaml` — persistent verified knowledge
- optional architecture, domain, module and decision artifacts

The global `.reveal/config.yaml` provides Reveal-wide defaults. Project configuration may override defaults where explicitly allowed.

## References

Projects may declare other projects as references. References are read-only and are used as sources for comparison, patterns, architecture, migration and testing strategies.
