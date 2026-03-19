$ErrorActionPreference = "Stop"

$root = "C:\Users\zgg20\Documents\trae_projects\vggt"
$logDir = Join-Path $root "transfer_logs"
$logFile = Join-Path $logDir "continuous_watch_transfer.log"
New-Item -ItemType Directory -Force $logDir | Out-Null

function Write-Log {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    $line | Tee-Object -FilePath $logFile -Append
}

while ($true) {
    Write-Log "===== heartbeat ====="

    $procs = Get-CimInstance Win32_Process |
        Where-Object {
            ($_.Name -match 'scp.exe|pwsh.exe') -and
            ($_.CommandLine -match 'co3d|tar -C /mnt/data2 -cf - co3d_raw_data')
        } |
        Select-Object ProcessId, Name, CommandLine

    if ($procs) {
        $procs | Out-String | Tee-Object -FilePath $logFile -Append | Out-Null
    } else {
        Write-Log "no local co3d transfer process found"
    }

    foreach ($name in @("co3d_copy.err", "co3d_copy.out", "co3d_tar_copy.err", "co3d_tar_copy.out")) {
        $path = Join-Path $logDir $name
        if (Test-Path $path) {
            Write-Log "--- tail $name"
            Get-Content $path -Tail 10 | Tee-Object -FilePath $logFile -Append | Out-Null
        }
    }

    Write-Log "--- remote co3d status"
    ssh -p 2222 szw@192.168.166.137 "du -sh /mnt/data5/OBVGGT/data/eval/co3d_raw_data 2>/dev/null || true; find /mnt/data5/OBVGGT/data/eval/co3d_raw_data -maxdepth 2 -name frame_annotations.jgz 2>/dev/null | wc -l" |
        Tee-Object -FilePath $logFile -Append | Out-Null

    Start-Sleep -Seconds 60
}
