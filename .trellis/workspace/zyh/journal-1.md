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
