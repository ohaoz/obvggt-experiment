# Frontend Guidelines

> Current status: there is no first-class frontend application in this workspace.

---

## Overview

This repository is **CLI / experiment / evaluation first**. Do not assume:

- React
- TypeScript
- component libraries
- API routes
- browser build tooling

unless a task explicitly introduces a UI surface.

The purpose of this directory is to define the **boundary**:

- today: frontend guidance is mostly `N/A`
- future: if a dashboard/viewer/web app is added, these docs must be rewritten before substantial UI code is generated

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Where a future UI could live without polluting the harness | Filled |
| [Component Guidelines](./component-guidelines.md) | Explicitly not applicable until a UI exists | Filled |
| [Hook Guidelines](./hook-guidelines.md) | Explicitly not applicable until a React-like UI exists | Filled |
| [State Management](./state-management.md) | How future UI should treat run artifacts as read-only source data | Filled |
| [Quality Guidelines](./quality-guidelines.md) | Requirements that must be added before UI code is merged | Filled |
| [Type Safety](./type-safety.md) | Boundary rules for future TS/JS code | Filled |

---

## Rule For Agents

If the user asks for harness, evaluation, or server work, stay in the controller/tooling layer. Do **not** invent a web dashboard as a "helpful" side effect.
