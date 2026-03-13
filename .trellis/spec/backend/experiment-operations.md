# Experiment Operations

> Trellis-owned safety and preflight rules for running experiments on shared servers.

---

## Why This Guide Exists

The operational rules in this workspace are not optional context. They are part of the experiment contract:

- wrong server choice wastes GPU time
- wrong disk target can fill the system disk
- wrong path wiring can make data look "missing" even when it exists
- wrong status handling creates false conclusions in docs

Trellis should surface these rules directly instead of relying on tribal memory.

---

## Default Server Context

- Default execution server: `amd_server`
- Endpoint: `192.168.166.137:2222`
- Preferred remote root: `/mnt/data5/OBVGGT`
- Preferred repo path: `/mnt/data5/OBVGGT/code/OBVGGT`
- Preferred data root: `/mnt/data5/OBVGGT/data`
- Preferred runs root: `/mnt/data5/OBVGGT/runs`
- Historical / migration server: `msi_server` at `192.168.166.9:2222`

Credentials are intentionally excluded from Trellis. They must stay outside tracked files and generated logs.

---

## Mandatory Preflight Before Heavy Runs

Before launching training or evaluation on a shared server:

1. Activate the server-side conda environment first.
2. Export `STREAMVGGT_CODE`, `STREAMVGGT_DATA`, `STREAMVGGT_RUNS`, `SWANLAB_LOG_DIR`, and `SWANLAB_CACHE_DIR`.
3. Run `nvidia-smi` and confirm the target GPU is available.
4. Run `df -h` and confirm the chosen disk has enough free space.
5. Verify `data`, `checkpoints`, and `eval_results` resolve to big-disk targets, not dead links or system-disk paths.
6. Create or update the Markdown run record before starting the heavy command.

If a preflight check fails, stop there and fix the environment before running the experiment.

---

## Forbidden Operations

- Never use `sudo` on shared experiment servers.
- Never write datasets, eval outputs, or SwanLab / W&B caches to the system disk.
- Never commit or print passwords, API keys, or other secrets to tracked files or logs.
- Never use destructive commands such as `rm -rf`, `mkfs`, `dd`, or `chmod -R` on shared mounts unless the human explicitly asks for that exact action and the target is fully verified.

---

## Run-State Rules

- `video_depth` and `mv_recon` are the KV-sensitive benchmark pair.
- `monodepth` is regression-only unless the benchmark stance is intentionally changed everywhere.
- A run is not `DONE` unless required artifacts for the task are present.
- Missing required outputs means `PARTIAL_DONE` or `FAILED`, never silent success.

---

## Documentation Sync Contract

After any run that changes status, coverage, or conclusions, check and update:

- `PROJECT_BRIEF.md`
- `agents.md`
- `OBVGGT/experiments/README.md`
- `OBVGGT/experiments/EXPERIMENTS.md`
- `OBVGGT/experiments/analysis/SUMMARY.md`

If no update is needed, the run record should still say that the docs were checked and why no change was required.

---

## Source Of Truth Rule

When operational rules change, keep these Trellis layers aligned:

- `.trellis/config.yaml`
- this file
- `.trellis/workflow.md`
- the relevant backend index entry

If Trellis says one thing and `agents.md` says another, treat that as a contract bug and reconcile it before the next run.
