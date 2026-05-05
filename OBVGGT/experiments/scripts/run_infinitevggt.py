import os
from pathlib import Path

from adapter_utils import (
    accelerate_launch_parts,
    MONODEPTH_DATASETS,
    VIDEO_DEPTH_DATASETS,
    build_payload,
    checkpoint_path,
    common_parser,
    ensure_task_supported,
    metric_path_for_task,
    parse_json_arg,
    print_dry_run,
    resolve_dataset_filter,
    repo_root_from,
    run_shell_commands,
    shell_join,
)


SUPPORTED_TASKS = ["monodepth", "video_depth", "mv_recon", "pose_co3d", "long_stream"]


def mv_recon_process_count(cfg):
    raw_visible = os.getenv("CUDA_VISIBLE_DEVICES", "").strip()
    visible_count = len([item for item in raw_visible.split(",") if item.strip()]) if raw_visible else 1
    configured = cfg.get("num_processes") or os.getenv("INFINITEVGGT_MV_RECON_PROCESSES")
    if configured:
        return max(1, int(configured))
    return max(1, visible_count)


def build_commands(args):
    repo_root = repo_root_from(args.repo_path)
    ckpt = checkpoint_path(repo_root, args.checkpoint)
    output_root = Path(args.output_root)
    result_tag = args.result_tag
    extra = list(args.extra_arg)
    cfg = parse_json_arg(args.kv_cache_cfg_json)
    commands = []

    if args.task == "monodepth":
        src_root = repo_root / "src"
        for dataset in MONODEPTH_DATASETS:
            out_dir = output_root / f"{dataset}_{result_tag}"
            commands.append(
                shell_join(
                    [
                        "python",
                        "./eval/monodepth/launch.py",
                        "--weights",
                        str(ckpt),
                        "--output_dir",
                        str(out_dir),
                        "--eval_dataset",
                        dataset,
                        *extra,
                    ]
                )
            )
        for dataset in MONODEPTH_DATASETS:
            out_dir = output_root / f"{dataset}_{result_tag}"
            commands.append(
                shell_join(
                    [
                        "python",
                        "./eval/monodepth/eval_metrics.py",
                        "--output_dir",
                        str(out_dir),
                        "--eval_dataset",
                        dataset,
                    ]
                )
            )
    elif args.task == "video_depth":
        src_root = repo_root / "src"
        datasets = resolve_dataset_filter(VIDEO_DEPTH_DATASETS, args.dataset_filter)
        if args.sequence_length > 0 and "bonn_500" in (cfg.get("preferred_long_dataset") or "bonn_500"):
            datasets = [f"bonn_{args.sequence_length}"]
        for dataset in datasets:
            out_dir = output_root / f"{dataset}_{result_tag}"
            commands.append(
                shell_join(
                    [
                        *accelerate_launch_parts(
                            "--num_processes",
                            "1",
                        ),
                        "../src/eval/video_depth/launch.py",
                        "--weights",
                        str(ckpt),
                        "--output_dir",
                        str(out_dir),
                        "--eval_dataset",
                        dataset,
                        "--size",
                        "518",
                        *extra,
                    ]
                )
            )
            commands.append(
                shell_join(
                    [
                        "python",
                        "../src/eval/video_depth/eval_depth.py",
                        "--output_dir",
                        str(out_dir),
                        "--eval_dataset",
                        dataset,
                        "--align",
                        "scale",
                    ]
                )
            )
    elif args.task == "mv_recon":
        src_root = repo_root / "src"
        out_dir = output_root / result_tag
        max_frames = args.sequence_length if args.sequence_length > 0 else cfg.get("max_frames", 300)
        num_processes = mv_recon_process_count(cfg)
        commands.append(
            shell_join(
                [
                    *accelerate_launch_parts(
                        "--num_processes",
                        str(num_processes),
                        "--main_process_port",
                        "29602",
                    ),
                    "./eval/mv_recon/launch.py",
                    "--weights",
                    str(ckpt),
                    "--output_dir",
                    str(out_dir),
                    "--model_name",
                    args.model_name,
                    "--max_frames",
                    str(max_frames),
                    *extra,
                ]
            )
        )
    elif args.task == "pose_co3d":
        if not args.pose_co3d_dir or not args.pose_co3d_anno_dir:
            raise ValueError("pose_co3d requires --pose-co3d-dir and --pose-co3d-anno-dir.")
        src_root = repo_root / "src"
        out_dir = output_root / result_tag
        commands.append(
            shell_join(
                [
                    "python",
                    "./eval/pose_evaluation/test_co3d.py",
                    "--weights",
                    str(ckpt),
                    "--co3d_dir",
                    args.pose_co3d_dir,
                    "--co3d_anno_dir",
                    args.pose_co3d_anno_dir,
                    "--output_dir",
                    str(out_dir),
                    "--seed",
                    "0",
                    *extra,
                ]
            )
        )
    elif args.task == "long_stream":
        repo_cwd = repo_root
        if not args.input_dir:
            raise ValueError("long_stream requires --input-dir.")
        out_dir = output_root / result_tag
        frame_cache = args.frame_cache_dir or str(out_dir / "frame_cache")
        commands.append(
            shell_join(
                [
                    "python",
                    "run_inference.py",
                    "--input_dir",
                    args.input_dir,
                    "--frame_cache_dir",
                    frame_cache,
                    "--no_cache_results",
                    *extra,
                ]
            )
        )
        src_root = repo_cwd
    else:
        raise ValueError(args.task)

    return src_root, commands


def main():
    parser = common_parser()
    args, unknown = parser.parse_known_args()
    args.extra_arg.extend(unknown)
    ensure_task_supported(args.task, SUPPORTED_TASKS)
    repo_root = repo_root_from(args.repo_path)
    cwd, commands = build_commands(args)
    payload = build_payload(
        adapter="run_infinitevggt.py",
        repo_root=repo_root,
        env_name=args.env_name,
        supported_tasks=SUPPORTED_TASKS,
        commands=commands,
    )
    payload["expected_artifacts"] = [
        str(path)
        for path in metric_path_for_task(
            args.task,
            Path(args.output_root),
            args.result_tag,
            dataset_filter=args.dataset_filter,
        )
    ]
    if args.dry_run:
        print_dry_run(payload)
        return
    raise SystemExit(run_shell_commands(commands, cwd=cwd))


if __name__ == "__main__":
    main()
