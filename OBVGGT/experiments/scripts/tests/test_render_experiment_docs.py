import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPT_PATH = REPO_ROOT / "OBVGGT" / "experiments" / "scripts" / "render_experiment_docs.py"
REFRESH_SCRIPT_PATH = REPO_ROOT / "OBVGGT" / "experiments" / "scripts" / "refresh_docs_from_amd_server.ps1"
# Keep test scratch space out of the repo so interrupted runs don't leave
# misleading temp directories next to the real experiment artifacts.
TMP_ROOT = Path(tempfile.gettempdir()) / "obvggt_render_experiment_docs_tests"
TMP_ROOT.mkdir(exist_ok=True)


class RenderExperimentDocsTests(unittest.TestCase):
    def test_sparse_local_runs_preserve_existing_history_sections(self) -> None:
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmpdir:
            experiments_root = Path(tmpdir)
            runs_dir = experiments_root / "runs" / "20260326_001223_baseline_video_depth"
            runs_dir.mkdir(parents=True, exist_ok=True)
            (runs_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "run_id": "20260326_001223_baseline_video_depth",
                        "variant": "baseline",
                        "task": "video_depth",
                        "status": "FAILED",
                        "timestamps": {"start": "2026-03-26T00:12:23+08:00", "end": "2026-03-26T00:13:00+08:00"},
                    }
                ),
                encoding="utf-8",
            )
            (runs_dir / "artifacts.json").write_text(json.dumps({"artifacts": []}), encoding="utf-8")
            (runs_dir / "record.md").write_text("# record", encoding="utf-8")

            (experiments_root / "EXPERIMENTS.md").write_text(
                textwrap.dedent(
                    """\
                    # OBVGGT 实验追踪表

                    > 本文件由 `experiments/scripts/render_experiment_docs.py` 自动生成。
                    > 单次运行的权威来源是 `experiments/runs/<run_id>/manifest.json`、`artifacts.json` 与 `record.md`。

                    ## 实验概览

                    说明：
                    - 优先用 repo 名称表达变体：`StreamVGGT / OBVGGT / XStreamVGGT / InfiniteVGGT`。

                    | Run ID | Variant | Task | Date | Status | Run Record | 关键指标 |
                    |--------|---------|------|------|--------|------------|----------|
                    | `20260319_145529_baseline_video_depth` | `StreamVGGT` | `video_depth` | `2026-03-19` | `DONE` | `experiments/runs/20260319_145529_baseline_video_depth/record.md` | result=3/3, system=3/3 |

                    ## 评测口径说明
                    """
                ),
                encoding="utf-8",
            )

            analysis_dir = experiments_root / "analysis"
            analysis_dir.mkdir(parents=True, exist_ok=True)
            (analysis_dir / "SUMMARY.md").write_text(
                textwrap.dedent(
                    """\
                    # 已完成实验报告汇总

                    > 本文件由 `experiments/scripts/render_experiment_docs.py` 自动生成。

                    ## 1. video_depth (StreamVGGT) - 2026-03-19

                    **Run ID**: `20260319_145529_baseline_video_depth`
                    **状态**: `DONE`
                    """
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--experiments-root", str(experiments_root)],
                check=True,
                cwd=REPO_ROOT,
            )

            experiments_text = (experiments_root / "EXPERIMENTS.md").read_text(encoding="utf-8")
            summary_text = (analysis_dir / "SUMMARY.md").read_text(encoding="utf-8")
            self.assertIn("20260326_001223_baseline_video_depth", experiments_text)
            self.assertIn("20260319_145529_baseline_video_depth", experiments_text)
            self.assertIn("20260326_001223_baseline_video_depth", summary_text)
            self.assertIn("20260319_145529_baseline_video_depth", summary_text)

    def test_all_results_unifies_ledger_and_summary_sources(self) -> None:
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmpdir:
            experiments_root = Path(tmpdir)
            analysis_dir = experiments_root / "analysis"
            analysis_tables = analysis_dir / "tables"
            analysis_tables.mkdir(parents=True, exist_ok=True)

            (experiments_root / "EXPERIMENTS.md").write_text(
                textwrap.dedent(
                    """\
                    # OBVGGT 实验追踪表

                    > 本文件由 `experiments/scripts/render_experiment_docs.py` 自动生成。
                    > 单次运行的权威来源是 `experiments/runs/<run_id>/manifest.json`、`artifacts.json` 与 `record.md`。

                    ## 实验概览

                    说明：
                    - 优先用 repo 名称表达变体：`StreamVGGT / OBVGGT / XStreamVGGT / InfiniteVGGT`。

                    | Run ID | Variant | Task | Date | Status | Run Record | 关键指标 |
                    |--------|---------|------|------|--------|------------|----------|
                    | `20260319_145529_baseline_video_depth` | `StreamVGGT` | `video_depth` | `2026-03-19` | `DONE` | `experiments/runs/20260319_145529_baseline_video_depth/record.md` | result=3/3, system=3/3 |

                    ## 评测口径说明

                    - `video_depth`：当前主时序 KV benchmark。

                    ## 维护规范

                    1. `EXPERIMENTS.md` 与 `analysis/SUMMARY.md` 一律由生成器重建，不手工编辑。
                    """
                ),
                encoding="utf-8",
            )
            (analysis_dir / "SUMMARY.md").write_text(
                textwrap.dedent(
                    """\
                    # 已完成实验报告汇总

                    > 本文件由 `experiments/scripts/render_experiment_docs.py` 自动生成。

                    ## 1. video_depth (StreamVGGT) - 2026-03-19

                    **Run ID**: `20260319_145529_baseline_video_depth`
                    **状态**: `DONE`
                    """
                ),
                encoding="utf-8",
            )
            (analysis_tables / "ablation_video_depth_20260324.csv").write_text(
                textwrap.dedent(
                    """\
                    variant,config_tag,method,p,use_vnorm,num_sink,num_recent,num_heavy,probe_mode,num_probes,sintel_absrel,sintel_rmse,sintel_d125,bonn_absrel,bonn_rmse,bonn_d125,kitti_absrel,kitti_rmse,kitti_d125,sintel_fps,bonn_fps,kitti_fps
                    obcache_p1,obcache_p1_joint_s1r2h4,obcvk,1,True,1,2,4,True,8,0.3269,3.8077,0.6544,0.0543,0.2552,0.9723,0.1268,4.1054,0.8470,5.98,5.51,5.82
                    """
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--experiments-root", str(experiments_root)],
                check=True,
                cwd=REPO_ROOT,
            )

            all_results_text = (analysis_dir / "ALL_RESULTS.md").read_text(encoding="utf-8")
            self.assertIn("# 论文式结果总表", all_results_text)
            self.assertIn("## 主结果：video_depth", all_results_text)
            self.assertIn("| StreamVGGT |", all_results_text)
            self.assertIn("## 消融：video_depth", all_results_text)
            self.assertIn("obcache_p1", all_results_text)

    def test_summary_includes_ablation_section_when_csv_exists(self) -> None:
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmpdir:
            experiments_root = Path(tmpdir)
            analysis_tables = experiments_root / "analysis" / "tables"
            analysis_tables.mkdir(parents=True, exist_ok=True)

            (analysis_tables / "ablation_video_depth_20260324.csv").write_text(
                textwrap.dedent(
                    """\
                    variant,config_tag,method,p,use_vnorm,num_sink,num_recent,num_heavy,probe_mode,num_probes,sintel_absrel,sintel_rmse,sintel_d125,bonn_absrel,bonn_rmse,bonn_d125,kitti_absrel,kitti_rmse,kitti_d125,sintel_fps,bonn_fps,kitti_fps
                    baseline,baseline,disabled,,,,,,,,0.3242,3.8179,0.6528,0.0585,0.2602,0.9721,0.1725,4.9677,0.7217,,,
                    obcache_p1,obcache_p1_joint_s1r2h4,obcvk,1,True,1,2,4,True,8,0.3269,3.8077,0.6544,0.0543,0.2552,0.9723,0.1268,4.1054,0.8470,5.98,5.51,5.82
                    """
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--experiments-root", str(experiments_root)],
                check=True,
                cwd=REPO_ROOT,
            )

            summary_path = experiments_root / "analysis" / "SUMMARY.md"
            self.assertTrue(summary_path.exists())
            summary_text = summary_path.read_text(encoding="utf-8")
            self.assertIn("ablation_video_depth_20260324.csv", summary_text)
            self.assertIn("obcache_p1", summary_text)

    def test_summary_preserves_existing_run_sections_when_runs_dir_is_sparse(self) -> None:
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmpdir:
            experiments_root = Path(tmpdir)
            analysis_dir = experiments_root / "analysis"
            analysis_tables = analysis_dir / "tables"
            analysis_tables.mkdir(parents=True, exist_ok=True)

            (analysis_dir / "SUMMARY.md").write_text(
                textwrap.dedent(
                    """\
                    # 已完成实验报告汇总

                    > 本文件由 `experiments/scripts/render_experiment_docs.py` 自动生成。

                    ## 1. video_depth (StreamVGGT) - 2026-03-19

                    **Run ID**: `20260319_145529_baseline_video_depth`
                    **状态**: `DONE`
                    """
                ),
                encoding="utf-8",
            )
            (analysis_tables / "ablation_video_depth_20260324.csv").write_text(
                textwrap.dedent(
                    """\
                    variant,config_tag,method,p,use_vnorm,num_sink,num_recent,num_heavy,probe_mode,num_probes,sintel_absrel,sintel_rmse,sintel_d125,bonn_absrel,bonn_rmse,bonn_d125,kitti_absrel,kitti_rmse,kitti_d125,sintel_fps,bonn_fps,kitti_fps
                    obcache_p1,obcache_p1_joint_s1r2h4,obcvk,1,True,1,2,4,True,8,0.3269,3.8077,0.6544,0.0543,0.2552,0.9723,0.1268,4.1054,0.8470,5.98,5.51,5.82
                    """
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--experiments-root", str(experiments_root)],
                check=True,
                cwd=REPO_ROOT,
            )

            summary_text = (analysis_dir / "SUMMARY.md").read_text(encoding="utf-8")
            self.assertIn("20260319_145529_baseline_video_depth", summary_text)
            self.assertIn("ablation_video_depth_20260324.csv", summary_text)

    def test_experiments_preserves_existing_rows_when_runs_dir_is_sparse(self) -> None:
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmpdir:
            experiments_root = Path(tmpdir)
            experiments_root.mkdir(parents=True, exist_ok=True)
            (experiments_root / "EXPERIMENTS.md").write_text(
                textwrap.dedent(
                    """\
                    # OBVGGT 实验追踪表

                    > 本文件由 `experiments/scripts/render_experiment_docs.py` 自动生成。
                    > 单次运行的权威来源是 `experiments/runs/<run_id>/manifest.json`、`artifacts.json` 与 `record.md`。

                    ## 实验概览

                    说明：
                    - 优先用 repo 名称表达变体：`StreamVGGT / OBVGGT / XStreamVGGT / InfiniteVGGT`。
                    - 历史脚本参数仍可能出现 `baseline / obcache`；其中 `obcache = OBVGGT`。
                    - `monodepth` 是 regression-only，不作为 KV 主 benchmark 结论来源。

                    | Run ID | Variant | Task | Date | Status | Run Record | 关键指标 |
                    |--------|---------|------|------|--------|------------|----------|
                    | `20260319_145529_baseline_video_depth` | `StreamVGGT` | `video_depth` | `2026-03-19` | `DONE` | `experiments/runs/20260319_145529_baseline_video_depth/record.md` | result=3/3, system=3/3 |

                    ## 评测口径说明
                    """
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--experiments-root", str(experiments_root)],
                check=True,
                cwd=REPO_ROOT,
            )

            experiments_text = (experiments_root / "EXPERIMENTS.md").read_text(encoding="utf-8")
            self.assertIn("20260319_145529_baseline_video_depth", experiments_text)
            self.assertNotIn("当前本地 experiments/runs 无记录", experiments_text)

    def test_refresh_script_is_deprecated_for_remote_state_sync(self) -> None:
        script_text = REFRESH_SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertIn("deprecated", script_text.lower())
        self.assertIn("跳板机", script_text)
        self.assertIn("不要用脚本获取", script_text)
        self.assertNotIn("scp ", script_text)


if __name__ == "__main__":
    unittest.main()
