#!/usr/bin/env python3
"""Generate missing root-level summary_metrics.json and system_metrics.json
for mv_recon ablation runs that have per-dataset results but lack root aggregation.
"""
import json, os, sys

RUNS = [
    ("20260326_001223_obcache_p1_joint_s1r2h4_mv_recon", "obcache_p1", "obcache_p1_joint_s1r2h4"),
    ("20260326_001835_obcache_random_random_s1r2h4_mv_recon", "obcache_random", "obcache_random_random_s1r2h4"),
    ("20260326_002422_obcache_sliding_window_sliding_window_s0r7h0_mv_recon", "obcache_sliding_window", "obcache_sliding_window_sliding_window_s0r7h0"),
]
EVAL_BASE = "/mnt/data5/OBVGGT/runs/eval_results/by_run"
RUN_BASE = "/mnt/data5/OBVGGT/code/OBVGGT/experiments/runs"
DATASETS = ["7scenes", "NRGBD"]

def avg_dicts(dicts):
    keys = dicts[0].keys()
    return {k: sum(d[k] for d in dicts) / len(dicts) for k in keys if isinstance(dicts[0][k], (int, float))}

for run_id, variant, result_tag in RUNS:
    variant_dir = os.path.join(EVAL_BASE, run_id, "mv_recon", variant, result_tag)
    if not os.path.isdir(variant_dir):
        print(f"SKIP {run_id}: no variant dir at {variant_dir}")
        continue

    # Collect per-dataset summaries
    ds_summaries = []
    ds_systems = []
    for ds in DATASETS:
        sm = os.path.join(variant_dir, ds, "summary_metrics.json")
        sy = os.path.join(variant_dir, ds, "system_metrics.json")
        if os.path.isfile(sm):
            with open(sm) as f:
                ds_summaries.append((ds, json.load(f)))
        if os.path.isfile(sy):
            with open(sy) as f:
                ds_systems.append((ds, json.load(f)))

    if len(ds_summaries) != len(DATASETS):
        print(f"SKIP {run_id}: only {len(ds_summaries)}/{len(DATASETS)} dataset summaries")
        continue

    # Generate root summary_metrics.json (average across datasets)
    root_summary = avg_dicts([s for _, s in ds_summaries])
    root_summary_path = os.path.join(variant_dir, "summary_metrics.json")
    with open(root_summary_path, "w") as f:
        json.dump(root_summary, f, indent=4)
    print(f"WROTE {root_summary_path}")

    # Generate root system_metrics.json
    root_system = {
        "summary": {
            "num_datasets_total": len(DATASETS),
            "num_datasets_ok": len(ds_systems),
            "num_scenes_total": sum(s.get("summary", s).get("num_scenes_total", s.get("summary", s).get("num_sequences_total", 0)) for _, s in ds_systems),
            "num_scenes_ok": sum(s.get("summary", s).get("num_scenes_ok", s.get("summary", s).get("num_sequences_ok", 0)) for _, s in ds_systems),
        },
        "per_dataset": []
    }
    for ds_name, ds_sys in ds_systems:
        entry = {"dataset": ds_name}
        # Copy per-dataset summary from its summary_metrics
        for name, sm in ds_summaries:
            if name == ds_name:
                entry.update(sm)
                break
        # Add system-level stats
        s = ds_sys.get("summary", ds_sys)
        for k in ["overall_fps", "max_peak_allocated_mb", "max_peak_reserved_mb", "total_elapsed_sec"]:
            if k in s:
                entry[k] = s[k]
        root_system["per_dataset"].append(entry)

    # Add aggregate FPS
    fps_vals = [e.get("overall_fps") for e in root_system["per_dataset"] if e.get("overall_fps")]
    if fps_vals:
        root_system["summary"]["avg_fps"] = sum(fps_vals) / len(fps_vals)
    peak_vals = [e.get("max_peak_allocated_mb") for e in root_system["per_dataset"] if e.get("max_peak_allocated_mb")]
    if peak_vals:
        root_system["summary"]["max_peak_allocated_mb"] = max(peak_vals)

    root_system_path = os.path.join(variant_dir, "system_metrics.json")
    with open(root_system_path, "w") as f:
        json.dump(root_system, f, indent=4)
    print(f"WROTE {root_system_path}")

    # Update manifest to DONE
    manifest_path = os.path.join(RUN_BASE, run_id, "manifest.json")
    if os.path.isfile(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)
        manifest["status"] = "DONE"
        manifest["result_summary"] = f"datasets={len(DATASETS)}/{len(DATASETS)}, root_summary=yes, root_system=yes"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"UPDATED manifest -> DONE: {manifest_path}")

    # Update artifacts.json
    artifacts_path = os.path.join(RUN_BASE, run_id, "artifacts.json")
    if os.path.isfile(artifacts_path):
        with open(artifacts_path) as f:
            artifacts = json.load(f)
        artifacts["status"] = "DONE"
        artifacts["missing_artifacts"] = []
        # Add the new root files
        for fpath in [root_summary_path, root_system_path]:
            artifacts["artifacts"].append({
                "path": fpath,
                "name": os.path.basename(fpath),
                "size_bytes": os.path.getsize(fpath)
            })
        with open(artifacts_path, "w") as f:
            json.dump(artifacts, f, indent=2)
        print(f"UPDATED artifacts -> DONE: {artifacts_path}")

    print(f"OK {run_id}")
    print()

print("ALL DONE")
