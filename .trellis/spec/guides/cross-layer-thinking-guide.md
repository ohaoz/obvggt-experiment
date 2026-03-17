# Cross-Layer Thinking Guide

> Think through the full experiment contract before changing one layer.

---

## The Real Layer Map In This Repo

```text
variant config
  -> quick_run.sh
  -> adapter dry-run payload
  -> repo-local command(s)
  -> eval artifact files
  -> run_record finalize
  -> compare_variants
  -> README / EXPERIMENTS / SUMMARY / PROJECT_BRIEF
```

Most high-cost bugs happen when one hop changes and the next hop does not.

---

## Boundaries To Check

| Boundary | Questions to ask |
|----------|------------------|
| `configs/*.json` -> `quick_run.sh` | Did you add/remove a field that shell parsing depends on? |
| `quick_run.sh` -> adapter payload | Did the dry-run JSON schema change? |
| adapter -> repo-local command | Do the forwarded args still match the target repo's CLI? |
| shared task coverage -> repo-local evaluators | If the controller says a variant supports a dataset/task, does the repo-local eval code actually implement every dataset branch and filename convention needed for that matrix? |
| repo-local command -> artifact files | Did filenames, directory layout, or dataset coverage change? |
| artifacts -> `run_record.py` | Will discovery still find the right files and status? |
| run state -> `compare_variants.py` | Will aggregators still read the schema correctly? |
| machine outputs -> Markdown docs | Do the human summaries still match actual coverage and conclusions? |

---

## Checklist

Before implementation:

- [ ] mapped every reader/writer for the changed field or file
- [ ] decided final status semantics
- [ ] listed required artifacts and coverage
- [ ] checked repo-local dataset branches and file naming against the shared controller matrix
- [ ] identified human docs that must move with the contract

After implementation:

- [ ] ran dry-run or static verification on the changed path
- [ ] verified missing artifacts downgrade status when appropriate
- [ ] checked docs and controller behavior tell the same story
