# Scope Audit: No Core OBCache Algorithm Changes

## User Constraint

OBVGGT is based on OBCache. This branch must not change the core OBCache
algorithm.

## Audit Result

This branch does not modify the OBVGGT core OBCache scoring, eviction, cache
budget, attention-cache, or aggregator semantics.

Not modified:

- `OBVGGT/src/streamvggt/utils/obcache_kv.py`
- `OBVGGT/src/streamvggt/layers/attention.py`
- `OBVGGT/src/streamvggt/models/aggregator.py`
- OBVGGT cache budget config semantics
- OBVGGT retained-token decision logic

OBVGGT source change in this branch:

- `OBVGGT/src/streamvggt/utils/runtime_diagnostics.py`
  - instrumentation-only fix for backend diagnostic reporting;
  - covered by `test_runtime_diagnostics`;
  - no cache or model-output semantics changed.

## Why `streamvggt.py` Appears In Diff

The changed `streamvggt.py` files are sibling baseline implementations:

- `StreamVGGT/src/streamvggt/models/streamvggt.py`
- `XStreamVGGT/src/streamvggt/models/streamvggt.py`
- `InfiniteVGGT/src/streamvggt/models/streamvggt.py`

Those changes add opt-in `output_keys` head gating for `video_depth
--head_mode depth_only`. Default `output_keys=None` preserves full-head
behavior. The aggregator/cache path still runs before the gated heads and is
not modified.

## Rejected Runtime Candidates

The branch records two rejected same-budget directions:

- `prealloc_kv`: already rejected before this branch because it was slower and
  used more memory.
- current `probe4/probe6`: rejected by the 2026-05-06 clean Bonn 40-frame
  smoke; both kept cache/seq budget but did not improve FPS.

## Accepted Work Type

The remaining work is non-algorithmic:

- runtime/backend diagnostics;
- read-only paired gate checking;
- experiment records and local artifact sync;
- fair `video_depth` depth-only task-contract preparation;
- prefix-eval support for short smoke runs;
- scoring microbench planning with exact `keep_topk_idx` equivalence as the
  promotion gate.

