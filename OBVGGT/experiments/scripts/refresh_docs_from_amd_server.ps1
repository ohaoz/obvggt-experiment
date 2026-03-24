$ErrorActionPreference = "Stop"

$root = "C:\Users\zgg20\Documents\trae_projects\vggt"
$localExperiments = Join-Path $root "OBVGGT\experiments"
$remoteHost = "szw@192.168.166.137"
$remoteExperiments = "/mnt/data5/OBVGGT/code/OBVGGT/experiments"

Write-Host "[refresh-docs] rendering docs on amd_server..."
ssh -p 2222 $remoteHost "python $remoteExperiments/scripts/render_experiment_docs.py --experiments-root $remoteExperiments"

Write-Host "[refresh-docs] pulling EXPERIMENTS.md..."
scp -P 2222 "${remoteHost}:${remoteExperiments}/EXPERIMENTS.md" "$localExperiments/EXPERIMENTS.md"

Write-Host "[refresh-docs] pulling analysis/SUMMARY.md..."
scp -P 2222 "${remoteHost}:${remoteExperiments}/analysis/SUMMARY.md" "$localExperiments/analysis/SUMMARY.md"

Write-Host "[refresh-docs] done."
