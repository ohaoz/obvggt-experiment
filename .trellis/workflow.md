# Development Workflow

> Based on [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

---

## What This Workflow Is For

This workspace is a **multi-repo experiment harness**, not a fullstack product app.

Use Trellis here to:

- keep controller/tooling conventions explicit
- track task context across sessions
- record agent work in a repeatable way
- reduce drift between run artifacts and human docs

---

## Quick Start

### Step 0: Initialize Developer Identity

```bash
python3 ./.trellis/scripts/get_developer.py
python3 ./.trellis/scripts/init_developer.py <your-name>
```

### Step 1: Read Project Context

Read these in order:

1. `PROJECT_BRIEF.md`
2. `agents.md`
3. `OBVGGT/experiments/README.md`
4. `OBVGGT/experiments/EXPERIMENTS.md`
5. `.trellis/spec/backend/index.md`

If you are changing contracts, also read:

- `.trellis/spec/guides/index.md`
- `.trellis/spec/guides/cross-layer-thinking-guide.md`

### Step 2: Inspect Current Task State

```bash
python3 ./.trellis/scripts/get_context.py
python3 ./.trellis/scripts/task.py list
git status
```

### Step 3: Create Or Select A Task

```bash
python3 ./.trellis/scripts/task.py create "<title>" --slug <task-name>
```

---

## Must-Read Guides By Task Type

| Task Type | Must-read Documents |
|-----------|---------------------|
| Experiment harness / adapters / scripts | `PROJECT_BRIEF.md`, `agents.md`, `.trellis/spec/backend/index.md` |
| Artifact / status / doc contract change | all of the above + `.trellis/spec/guides/cross-layer-thinking-guide.md` |
| Repeated constants / helper cleanup | `.trellis/spec/guides/code-reuse-thinking-guide.md` |
| Explicit UI work | `.trellis/spec/frontend/index.md` first, then define the UI boundary before coding |

---

## Development Process

### 1. Read Before Write

Before touching code, identify:

- which repo actually owns the behavior
- which controller files orchestrate it
- which artifacts and docs will move with the change

### 2. Keep Layer Ownership Clear

- repo-local model/eval logic belongs in `*/src/`
- controller glue belongs in `OBVGGT/experiments/`
- human summaries belong in Markdown docs
- machine-readable run state belongs in JSON / CSV

### 3. Validate Locally

For controller/tooling changes:

- activate `.venv` before local Python checks
- run syntax checks such as `python -m py_compile` or `python -m compileall`
- use adapter `--dry-run` where possible
- re-read impacted docs after editing them

### 4. Record What Happened

Use Trellis workspace journals for session continuity, especially when:

- a contract changed
- a bug was diagnosed
- a run-status rule was clarified
- documentation was updated to match reality

AI should not create commits automatically, but it should leave the repo in a state where a human can review and commit confidently.

---

## Session End Checklist

- [ ] Relevant Trellis docs still match the repo
- [ ] No new second source of truth was introduced
- [ ] Run / artifact / doc contract was verified
- [ ] Validation steps were run or explicitly noted as skipped

---

## Core Principle

In this repo, the most valuable Trellis behavior is not "more context". It is **less drift** between controller code, run artifacts, and documented conclusions.
