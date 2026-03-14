## Goal

Fix the `XStreamVGGT` monodepth evaluation path so the unified `OBVGGT/experiments/quick_run.sh xstreamvggt monodepth` contract can complete the full 5-dataset regression set without failing on `scannet`.

## Requirements

- Preserve the current unified monodepth dataset set: `sintel`, `bonn`, `kitti`, `nyu`, `scannet`.
- Add `scannet` metric evaluation support to `XStreamVGGT/src/eval/monodepth/eval_metrics.py`.
- Keep the fix scoped to the existing evaluation contract; do not change benchmark stance or remove datasets from the controller.
- Validate locally with Python syntax checks and an adapter dry-run.

## Non-Goals

- No remote rerun in this change.
- No changes to experiment conclusions.
- No broader refactor of the monodepth pipeline.
