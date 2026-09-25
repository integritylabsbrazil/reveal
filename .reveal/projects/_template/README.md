# Project Knowledge

This directory contains the persistent engineering knowledge for a single target project.

The baseline represents stable facts that agents should receive as context without rediscovering them on every task.

Knowledge updates are guarded. Agents must not silently rewrite the baseline after a ticket analysis.

Project-specific configuration lives in the sibling `config.yaml`. The global `.reveal/config.yaml` provides Reveal-wide defaults.
