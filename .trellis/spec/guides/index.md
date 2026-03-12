# Thinking Guides

> Guides for changes that affect contracts, artifacts, or multiple repos.

---

## Why These Guides Matter Here

In this workspace, most costly mistakes are contract bugs:

- docs say one dataset set, adapters run another
- artifact names change in one place but not in discovery
- controller logic drifts away from repo-local commands
- a summary doc claims coverage the artifacts do not support

---

## Available Guides

| Guide | Purpose | Use It When |
|-------|---------|-------------|
| [Code Reuse Thinking Guide](./code-reuse-thinking-guide.md) | Keep shared constants / naming / file contracts centralized | You are touching more than one adapter, config, or artifact name |
| [Cross-Layer Thinking Guide](./cross-layer-thinking-guide.md) | Track data flow from config to run artifacts to human docs | You are changing task wiring, status logic, artifact schemas, or doc conclusions |

---

## Pre-Modification Rule

Before changing any constant, filename, or label, search for every existing consumer.

Preferred command:

```bash
rg "value_to_change" .
```

Fallback if `rg` is unavailable:

```bash
grep -R "value_to_change" .
```

---

## Core Principle

In this repo, 10 minutes of contract thinking often prevents a ruined overnight run.
