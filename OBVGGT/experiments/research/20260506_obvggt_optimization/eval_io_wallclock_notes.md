# Notes: `video_depth` Eval IO Wall-Clock

## Scope

This direction is allowed only as experiment-throughput work. It must not alter
formal model FPS, model outputs used by metrics, or OBCache behavior.

## Code Audit

`video_depth` formal FPS is measured around model inference in
`src/eval/video_depth/launch.py`. After that timed block, the script prepares
outputs and calls `save_depth_maps()`.

`save_depth_maps()` currently does all of the following:

- stack depth tensors;
- colorize depth maps with a colorbar;
- optionally colorize confidence maps;
- write a PNG per frame;
- reopen each PNG through PIL;
- write `frame_####.npy` per frame.

`eval_depth.py` reads `frame_*.npy` prediction files for metrics. It does not
read the colorized PNG files for metric computation.

## Safe Fast Mode Shape

If implemented later, the only safe fast-output mode is:

- keep writing `frame_####.npy`;
- skip PNG/colorbar/confidence visualization by default for metric-only runs;
- put visualization behind an explicit flag such as
  `--save_visual_depth_png true`;
- record `output_mode=metrics_only` or `output_mode=full_visualization` in
  `system_metrics.json`;
- keep formal FPS unchanged and add separate wall-clock fields for
  `prepare_output` and `save_depth_maps`.

## Validation Gate

For any future patch:

1. Run the same Bonn smoke twice, once with full visualization and once with
   metrics-only output.
2. Compare `result_scale.json`; metrics must match.
3. Compare the list and shape/dtype of `frame_*.npy` files.
4. Do not compare formal FPS as the win. Compare total wall-clock or phase
   profile save time only.

## Reporting Rule

This is not a model-speed improvement. It can reduce server turnaround time and
artifact size, but it must be reported separately from OBVGGT FPS.

