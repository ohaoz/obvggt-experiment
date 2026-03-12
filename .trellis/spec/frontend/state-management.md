# State Management

> Current state is file-based, not client-state-based.

---

## Current State Categories

The canonical state in this workspace lives in files:

- variant config state -> `configs/*.json`
- per-run machine state -> `manifest.json`, `artifacts.json`
- per-run human summary -> `record.md`
- derived cross-run state -> `analysis/*.csv`

There is no browser-side global store.

---

## Rule For Future UI Work

If a UI is added later, it should treat run artifacts as:

- read-only source data
- refreshable / cacheable views
- never the canonical writer of experiment truth
