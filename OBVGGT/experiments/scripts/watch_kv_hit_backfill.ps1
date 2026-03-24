param(
    [string]$RunId = "20260319_151439_infinitevggt_rolling_memory_budget1200000_video_depth",
    [int]$PollSeconds = 60
)

$ErrorActionPreference = "Stop"

$root = "C:\Users\zgg20\Documents\trae_projects\vggt"
$localExperiments = Join-Path $root "OBVGGT\experiments"
$localTransfer = Join-Path $root "transfer_logs"
$localCompare = Join-Path $localTransfer "compare_variants"
$remoteHost = "szw@192.168.166.137"
$remoteExperiments = "/mnt/data5/OBVGGT/code/OBVGGT/experiments"
$remoteRunDir = "$remoteExperiments/runs/$RunId"
$logFile = Join-Path $localTransfer "kv_hit_watch_$RunId.log"

New-Item -ItemType Directory -Force $localTransfer | Out-Null
New-Item -ItemType Directory -Force $localCompare | Out-Null

function Write-Log {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    $line | Tee-Object -FilePath $logFile -Append | Out-Null
}

function Run-Ssh {
    param([string]$Command)
    ssh -p 2222 $remoteHost $Command
}

$refreshed = $false

Write-Log "watcher started for run: $RunId"
while ($true) {
    Write-Log "===== heartbeat ====="

    $statusBlock = Run-Ssh "bash -lc 'if [ -f ""$remoteRunDir/record.md"" ]; then grep -nE ""Status:|Start:|End:|Exit code:"" ""$remoteRunDir/record.md""; else echo ""record_missing""; fi'"
    $statusBlock | Tee-Object -FilePath $logFile -Append | Out-Null

    Write-Log "--- gpu snapshot"
    Run-Ssh "nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits" |
        Tee-Object -FilePath $logFile -Append | Out-Null

    Write-Log "--- latest system_metrics under run"
    Run-Ssh "bash -lc 'find ""/mnt/data5/OBVGGT/runs/eval_results/by_run/$RunId"" -name system_metrics.json 2>/dev/null | sort'" |
        Tee-Object -FilePath $logFile -Append | Out-Null

    $joined = ($statusBlock | Out-String)
    if (-not $refreshed -and $joined -match "Status:\s+(DONE|FAILED|PARTIAL_DONE)") {
        Write-Log "run finished, refreshing docs and tables"
        Run-Ssh "python $remoteExperiments/scripts/render_experiment_docs.py --experiments-root $remoteExperiments" |
            Tee-Object -FilePath $logFile -Append | Out-Null
        Run-Ssh "python $remoteExperiments/scripts/compare_variants.py" |
            Tee-Object -FilePath $logFile -Append | Out-Null

        scp -P 2222 "${remoteHost}:${remoteExperiments}/EXPERIMENTS.md" "$localExperiments/EXPERIMENTS.md" | Out-Null
        scp -P 2222 "${remoteHost}:${remoteExperiments}/analysis/SUMMARY.md" "$localExperiments/analysis/SUMMARY.md" | Out-Null
        scp -P 2222 "${remoteHost}:${remoteExperiments}/analysis/tables/short_sequence_metrics.csv" (Join-Path $localCompare "short_sequence_metrics.csv") | Out-Null
        scp -P 2222 "${remoteHost}:${remoteExperiments}/analysis/tables/efficiency_metrics.csv" (Join-Path $localCompare "efficiency_metrics.csv") | Out-Null
        Write-Log "docs and tables refreshed locally"
        $refreshed = $true
    }

    Start-Sleep -Seconds $PollSeconds
}
