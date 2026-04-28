#!/usr/bin/env python3
"""Extract seed experiment metrics from eval_results on remote server.
Run on the server: python3 extract_seed_metrics.py
"""
import json, os

runs = {
    "default_s1": "20260401_033005_obcache_default_s1_joint_s1r2h4_video_depth",
    "default_s2": "20260401_034820_obcache_default_s2_joint_s1r2h4_video_depth",
    "default_s3": "20260401_040642_obcache_default_s3_joint_s1r2h4_video_depth",
    "p1small_s1": "20260401_042501_obcache_p1_small_s1_joint_s1r1h3_video_depth",
    "p1small_s2": "20260401_044324_obcache_p1_small_s2_joint_s1r1h3_video_depth",
    "p1small_s3": "20260401_050147_obcache_p1_small_s3_joint_s1r1h3_video_depth",
    "default_fps": "20260401_030803_obcache_joint_s1r2h4_video_depth",
    "baseline_new": "20260401_051955_baseline_video_depth",
}
base = "/mnt/data5/OBVGGT/runs/eval_results/by_run"
header = f"{'Label':<15} {'Dataset':<8} {'AbsRel':>8} {'d1.25':>8} {'FPS':>8} {'PeakMB':>8}"
print(header)
print("-" * len(header))
for label, run in runs.items():
    rdir = os.path.join(base, run, "video_depth")
    if not os.path.isdir(rdir):
        print(f"{label:<15} NO OUTPUT")
        continue
    for vd in sorted(os.listdir(rdir)):
        vpath = os.path.join(rdir, vd)
        if not os.path.isdir(vpath):
            continue
        for ds_dir in sorted(os.listdir(vpath)):
            dpath = os.path.join(vpath, ds_dir)
            if not os.path.isdir(dpath):
                continue
            ds = ds_dir.split("_")[0]
            abs_rel = delta = fps = peak = "?"
            rs = os.path.join(dpath, "result_scale.json")
            if os.path.isfile(rs):
                with open(rs) as f:
                    d = json.load(f)
                    ar = d.get("Abs Rel", d.get("abs_rel"))
                    if isinstance(ar, float):
                        abs_rel = f"{ar:.4f}"
                    dt = d.get("\u03b4 < 1.25", d.get("delta_1.25"))
                    if isinstance(dt, float):
                        delta = f"{dt:.4f}"
            sy = os.path.join(dpath, "system_metrics.json")
            if os.path.isfile(sy):
                with open(sy) as f:
                    d = json.load(f)
                    s = d.get("summary", d)
                    fp = s.get("overall_fps")
                    if isinstance(fp, float):
                        fps = f"{fp:.2f}"
                    pk = s.get("max_peak_allocated_mb")
                    if isinstance(pk, float):
                        peak = f"{pk:.0f}"
            print(f"{label:<15} {ds:<8} {abs_rel:>8} {delta:>8} {fps:>8} {peak:>8}")
