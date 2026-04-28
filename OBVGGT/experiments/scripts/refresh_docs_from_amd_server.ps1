$ErrorActionPreference = "Stop"

throw @"
[refresh-docs] Deprecated.

不要用脚本获取远端服务器文档，因为结果可能写入不及时。

请改用跳板机人工核对 `amd_server` 上的真实状态：
  - /mnt/data5/OBVGGT/code/OBVGGT/experiments/runs/<run_id>/manifest.json
  - /mnt/data5/OBVGGT/code/OBVGGT/experiments/runs/<run_id>/artifacts.json
  - /mnt/data5/OBVGGT/code/OBVGGT/experiments/runs/<run_id>/record.md
  - /mnt/data5/OBVGGT/code/OBVGGT/experiments/EXPERIMENTS.md
  - /mnt/data5/OBVGGT/code/OBVGGT/experiments/analysis/SUMMARY.md

如果需要同步到本地，请在确认远端 run 已 finalize 后，再通过跳板机手工复制目标文件。
"@
