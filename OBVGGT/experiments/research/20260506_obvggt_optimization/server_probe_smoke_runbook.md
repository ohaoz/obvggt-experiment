# Server Runbook: Probe Smoke Gate

## Scope

This runbook is for the first server-side follow-up experiment from the
non-algorithm optimization research pass. It tests only existing OBCache configs:

- ctrl: `obcache_p1_no_recent_ctrl_backend_probe`
- candidate A: `obcache_p1_no_recent_probe6`
- candidate B: `obcache_p1_no_recent_probe4`

It must not change OBCache scoring, eviction, budgets, or model code.

## Preflight

Run on `amd_server` with conda. Do not use sudo.

```bash
ssh amd_server
conda activate obvggt

export STREAMVGGT_CODE=/mnt/data5/OBVGGT/code/OBVGGT
export STREAMVGGT_DATA=/mnt/data5/OBVGGT/data
export STREAMVGGT_RUNS=/mnt/data5/OBVGGT/runs
export SWANLAB_LOG_DIR=$STREAMVGGT_RUNS/swanlab
export SWANLAB_CACHE_DIR=$STREAMVGGT_RUNS/swanlab_cache
export SWANLAB_PROJECT=OBVGGT

nvidia-smi
df -h | sed -n '1,160p'
du -sh "$STREAMVGGT_RUNS" 2>/dev/null || true
cd "$STREAMVGGT_CODE"
git status --short --branch
git rev-parse HEAD
```

Stop if the target GPU is occupied, the branch is wrong, or the target disk is
near full.

Observed 2026-05-06 preflight:

- Direct SSH required bypassing local SSH config:
  `ssh -F NUL -o ProxyCommand=none -p 2222 szw@192.168.166.137`.
- GPU 0 and 2 were idle, but GPU 1 and 3 were busy.
- `/mnt/data5` was `97%` used with about `149G` available.
- `/mnt/data5/OBVGGT/code/OBVGGT` was dirty `main`, not a clean research
  branch.

Decision from that preflight: do not run smoke there until a clean server
checkout/worktree is prepared on a disk with enough headroom.

## Commands

Use one GPU and keep the same Bonn sequence/prefix for all three runs.

```bash
cd "$STREAMVGGT_CODE/experiments"

bash quick_run.sh obcache_p1_no_recent_ctrl_backend_probe video_depth \
  --dataset-filter bonn \
  --seq_list balloon2 \
  --max_frames 40

bash quick_run.sh obcache_p1_no_recent_probe6 video_depth \
  --dataset-filter bonn \
  --seq_list balloon2 \
  --max_frames 40

bash quick_run.sh obcache_p1_no_recent_probe4 video_depth \
  --dataset-filter bonn \
  --seq_list balloon2 \
  --max_frames 40
```

Each run should produce:

- `experiments/runs/<run_id>/manifest.json`
- `experiments/runs/<run_id>/artifacts.json`
- `experiments/runs/<run_id>/record.md`
- `.../result_scale.json`
- `.../system_metrics.json`

Local dry-run validation:

- All three variants expand to `../src/eval/video_depth/launch.py`.
- All three pass `--eval_dataset bonn --seq_list balloon2 --max_frames 40`.
- All three run `../src/eval/video_depth/eval_depth.py --eval_dataset bonn --align scale`.
- The only intended config difference is `num_patch_probes`: ctrl `8`,
  probe6 `6`, probe4 `4`.

## Promotion Gate

For each candidate, compare against the ctrl with:

```bash
python "$STREAMVGGT_CODE/experiments/scripts/check_video_depth_gate.py" \
  --ctrl-system <ctrl_output>/system_metrics.json \
  --cand-system <candidate_output>/system_metrics.json \
  --ctrl-result <ctrl_output>/result_scale.json \
  --cand-result <candidate_output>/result_scale.json \
  --min-fps-gain-pct 3 \
  --metric-abs-tol 1e-9 \
  --cache-abs-tol 0
```

Accept only if:

- `GATE: PASS`
- `formal_fps_valid=true`
- `cache_max`, `seq_max`, evict calls, and hit rate match ctrl
- depth metrics match within tolerance

If both candidates pass, prefer `probe6` unless `probe4` has a clearly larger
gain and no quality/cache drift. If neither passes, do not run Bonn full.

## Local Sync

After remote finalize, sync at minimum:

```bash
rsync -av amd_server:/mnt/data5/OBVGGT/code/OBVGGT/experiments/runs/<run_id>/manifest.json \
  OBVGGT/experiments/runs/<run_id>/manifest.json
rsync -av amd_server:/mnt/data5/OBVGGT/code/OBVGGT/experiments/runs/<run_id>/artifacts.json \
  OBVGGT/experiments/runs/<run_id>/artifacts.json
rsync -av amd_server:/mnt/data5/OBVGGT/code/OBVGGT/experiments/runs/<run_id>/record.md \
  OBVGGT/experiments/runs/<run_id>/record.md
```

Also sync the candidate/control `system_metrics.json` and `result_scale.json`
into an analysis artifact folder, for example:

`OBVGGT/experiments/analysis/artifacts/20260506_probe_smoke/{ctrl,probe6,probe4}/`

Then rebuild local docs:

```bash
cd OBVGGT
python experiments/scripts/render_experiment_docs.py
```

## Documentation Update Rule

Update `OBVGGT/experiments/EXPERIMENTS.md`,
`OBVGGT/experiments/analysis/SUMMARY.md`, and
`OBVGGT/experiments/analysis/ALL_RESULTS.md` via the renderer after sync.

If the smoke does not affect project-level status, record that
`AGENTS.md`, `PROJECT_BRIEF.md`, and `OBVGGT/experiments/README.md` were checked
and no update was required because the run did not pass promotion gates.

## Expected Decision

- `probe6` or `probe4` passing smoke only authorizes Bonn full.
- Bonn full passing authorizes full `sintel/bonn/kitti`.
- Smoke passing does not by itself authorize a paper/report conclusion.
