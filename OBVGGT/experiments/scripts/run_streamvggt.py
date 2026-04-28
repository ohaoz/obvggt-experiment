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
    resolve_dataset_filter,
    print_dry_run,
    repo_root_from,
    run_shell_commands,
    shell_join,
)


SUPPORTED_TASKS = ["monodepth", "video_depth", "mv_recon", "pose_co3d"]

def build_commands(args):
    repo_root = repo_root_from(args.repo_path)
    ckpt = checkpoint_path(repo_root, args.checkpoint)
    output_root = Path(args.output_root)
    result_tag = args.result_tag
    extra = list(args.extra_arg)

    commands = []
    src_root = repo_root / "src"
    if args.task == "monodepth":
        datasets = resolve_dataset_filter(MONODEPTH_DATASETS, args.dataset_filter)
        for dataset in datasets:
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
        for dataset in datasets:
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
        datasets = resolve_dataset_filter(VIDEO_DEPTH_DATASETS, args.dataset_filter)
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
        out_dir = output_root / result_tag
        commands.append(
            shell_join(
                [
                    *accelerate_launch_parts(
                        "--num_processes",
                        "1",
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
                    *extra,
                ]
            )
        )
    elif args.task == "pose_co3d":
        if not args.pose_co3d_dir or not args.pose_co3d_anno_dir:
            raise ValueError("pose_co3d requires --pose-co3d-dir and --pose-co3d-anno-dir.")
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
        adapter="run_streamvggt.py",
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
