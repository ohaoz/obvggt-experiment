# Quality Guidelines

> Frontend-specific quality gates are deferred until a real UI exists.

---

## Current Rule

Do not merge UI code that creates a hidden second architecture without first defining:

- framework
- build command
- lint command
- test command
- accessibility expectations

If those are not defined, the safer choice is to keep work in Markdown / JSON / Python tooling.

---

## Forbidden Patterns

- Dropping ad-hoc HTML/JS files into controller directories
- Creating a dashboard that writes canonical experiment state
- Introducing frontend dependencies without documenting how they are built and tested
