# Journal - zyh (Part 1)

> AI development session journal
> Started: 2026-03-12

---



## Session 1: Trellis preflight and remote eval recovery

**Date**: 2026-03-13
**Task**: Trellis preflight and remote eval recovery

### Summary

Added Trellis experiment preflight, synchronized remote bugfixes back to local code, committed OBVGGT changes, and recorded the server-side evaluation recovery work.

### Main Changes

| Area | Description |
|------|-------------|
| Trellis | Added experiment preflight config, startup context output, and backend ops guide. |
| Server 2 | Fixed `data/checkpoints/eval_results` links, restored `Sintel`, and aligned repo paths for `StreamVGGT` and `OBVGGT`. |
| Harness | Synced and repaired `quick_run.sh`, configs, and adapter scripts so remote runs use the current controller contract. |
| Eval Fixes | Fixed `mv_recon` launcher compatibility, monodepth `scannet` handling, KV flag passing, and Python compatibility in `swanlab_utils.py`. |
| Runs | Launched baseline/obcache sweeps on server 2; `video_depth`, `monodepth`, and `mv_recon` reruns were started and partially repaired. |

**Updated Repos**:
- `OBVGGT` subrepo committed as `cced750`
- Top-level Trellis workflow and task state updated

**Current Runtime Note**:
- Some server-side reruns were still in progress / mid-debug at the time of recording.


### Git Commits

| Hash | Message |
|------|---------|
| `cced750` | (see git log) |

### Testing

- Verified local/remote code sync for key files via SHA-256 comparison.
- Verified Trellis preflight output locally.
- Verified server-side reruns were launched and observed active progress in logs.

### Status

[OK] **Recorded - server reruns still in progress**

### Next Steps

- Continue monitoring the server 2 reruns for `video_depth`, `monodepth`, and `mv_recon`.
- Sync final run outcomes back into docs once the active evaluations settle.


## Session 2: Re-run all OBVGGT experiments + fix XStreamVGGT scannet

**Date**: 2026-03-14
**Task**: Re-run all OBVGGT experiments + fix XStreamVGGT scannet

### Summary

(Add summary)

### Main Changes

## Summary
Connected to amd_server (2号机), synced local code, and re-ran all OBVGGT variant experiments (baseline/obcache/xstreamvggt/infinitevggt) across monodepth/video_depth/mv_recon tasks on GPU 0 and GPU 2 in parallel.

Fixed XStreamVGGT monodepth scannet eval_metrics.py: replaced strict count check with (scene, frame) key-based pairing to handle color/depth count mismatch (1260 color vs 1170 depth GT).

## Experiment Results (2026-03-14)

| Variant | monodepth | video_depth | mv_recon |
|---------|-----------|-------------|----------|
| baseline | 4/5 (scannet: NotImplementedError in StreamVGGT) | FAILED (OOM 24G) | OK |
| obcache | **5/5 全通** | FAILED (OOM 24G) | OK |
| xstreamvggt | **5/5 全通** (scannet fix applied) | **3/3 全通** | OK |
| infinitevggt | N/A | FAILED (hardcoded paths) | FAILED (hardcoded paths) |

## XStreamVGGT Scannet Fix
- **Root cause**: scannet color_90/ has 1260 images but depth_90/ has only 1170 GT maps
- **Fix**: `eval_metrics.py` — build `(scene, frame)` lookup dict from predictions, match against GT files, only evaluate 1170 matched pairs
- **Result**: Abs Rel = 0.0241, δ<1.25 = 99.10% (matches obcache)

## Remaining Issues
1. **video_depth OOM**: 24G 4090D insufficient for baseline/obcache video_depth (needs 48G cards, currently occupied by PreDiff)
2. **baseline scannet**: StreamVGGT original code lacks scannet support in eval_metrics.py
3. **InfiniteVGGT**: hardcoded Huawei Cloud paths (`/home/ma-user/work/...`), needs path adaptation

## Key Files Changed
- `XStreamVGGT/src/eval/monodepth/eval_metrics.py` — scannet (scene,frame) pairing fix
- `XStreamVGGT/src/eval/monodepth/launch.py` — .jpg/.png stem fix (from earlier)
- `XStreamVGGT/src/eval/monodepth/run.sh` — added scannet to dataset list
- Server batch scripts: `20260314_rerun_all_gpu0.sh`, `20260314_rerun_all_gpu2.sh`


### Git Commits

| Hash | Message |
|------|---------|
| `d4cb926` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 3: Failure analysis, SSH fix, smart poll, and catch-up runs

**Date**: 2026-03-16 ~ 2026-03-17
**Task**: Diagnose all failed experiments, fix SSH, deploy smart GPU polling, run catch-up experiments

### Summary

Analyzed all experiment failure logs on amd_server, fixed SSH keys for all 7 lab servers, deployed a smart GPU polling script, and completed most catch-up runs. Found and fixed a new scannet eval_metrics.py glob bug.

### Failure Root Causes Identified (03-16)

| # | Variant | Task | Root Cause |
|---|---------|------|------------|
| 1 | baseline | monodepth (scannet) | `NotImplementedError` — StreamVGGT lacked scannet support |
| 2 | baseline | video_depth | OOM on 24G card |
| 3 | obcache | video_depth | `--kv_cache_enable` arg parsing bug (expected value, got flag) |
| 4 | xstreamvggt | monodepth (scannet) | pred/gt count mismatch (1260 vs 1170), 90 extra preds from scene0720_00 |
| 5 | infinitevggt | video_depth | Hardcoded Huawei Cloud paths (fixed in 03-15 rerun) |
| 6 | infinitevggt | mv_recon | OOM on 24G + hardcoded paths |

### Actions Taken

| Action | Detail |
|--------|--------|
| SSH key deployment | Added keys to all 7 servers (msi, msi2, x99, x99_2, x99_3) via pexpect from amd_server |
| scannet glob fix | `eval_metrics.py` glob `*/*depth.npy` → `*/*.npy` + frame extraction fix for `.jpg.npy` files. Applied to StreamVGGT_github, OBVGGT, XStreamVGGT |
| baseline monodepth | Ran on GPU0 (shared with hyau.py, ~18G free). 4/5 done, scannet eval_metrics manually re-run after glob fix → 5/5 |
| smart_poll.sh | Wrote and deployed new polling script: checks free VRAM (not used < 500), configurable task queue, state persistence. Replaced old watchers |
| Killed old watchers | `obvggt_fix_watch_streaming` and `obvggt_fix_watch_baseline_monodepth` removed |

### smart_poll.sh Auto-Completed (03-17 morning)

voxdet released GPU1 (48G) overnight. smart_poll.sh automatically:
- 09:21 baseline video_depth → **DONE**
- 09:39 obcache video_depth → **DONE**
- 09:57 infinitevggt mv_recon → started (still running)

### Manual Runs (03-17)

- xstreamvggt monodepth on GPU2 — verifying codex's scene0720_00 fix

### Current Experiment Matrix (03-17 noon)

| Variant | monodepth | video_depth | mv_recon |
|---------|-----------|-------------|----------|
| baseline | **5/5 DONE** | **DONE** | **DONE** |
| OBVGGT | **5/5 DONE** | **DONE** | **DONE** |
| xstreamvggt | **RERUNNING** (GPU2) | **DONE** | **DONE** |
| infinitevggt | N/A | **DONE** | **RUNNING** (GPU1) |

### Key Files Created/Modified

- `OBVGGT/experiments/scripts/smart_poll.sh` — new GPU polling script
- `StreamVGGT_github/src/eval/monodepth/eval_metrics.py` — scannet glob fix
- `OBVGGT/src/eval/monodepth/eval_metrics.py` — scannet glob fix
- `XStreamVGGT/src/eval/monodepth/eval_metrics.py` — scannet glob fix

### Status

[IN PROGRESS] **Waiting for 2 running experiments to finish**

### Next Steps

- Wait for xstreamvggt monodepth and infinitevggt mv_recon to complete
- Update baseline monodepth manifest PARTIAL_DONE → DONE
- Sync EXPERIMENTS.md and SUMMARY.md once all results are in
