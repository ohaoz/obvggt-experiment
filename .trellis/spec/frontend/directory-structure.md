# Directory Structure

> There is no frontend tree in the current workspace.

---

## Current State

Today, no directory under this workspace acts as a maintained frontend application.

That means:

- no `app/`, `pages/`, or `components/` tree exists as a source of truth
- no UI build system is part of the current experiment harness
- Markdown, JSON, CSV, and shell/Python tooling are the primary interfaces

---

## If A UI Is Added Later

Keep it isolated from the controller layer.

Acceptable options:

- a dedicated sibling repo
- a dedicated subdirectory such as `OBVGGT/experiments/web/`

Do **not** scatter HTML/JS/CSS files across:

- `.trellis/`
- `OBVGGT/experiments/scripts/`
- repo roots
