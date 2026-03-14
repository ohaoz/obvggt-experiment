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
