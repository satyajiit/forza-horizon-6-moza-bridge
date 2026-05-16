# Stop the ForzaHorizon5.exe spoof process.

$procs = Get-Process -Name "ForzaHorizon5" -ErrorAction SilentlyContinue
if (-not $procs) {
    Write-Host "No spoof process running."
    exit 0
}
foreach ($p in $procs) {
    try {
        Stop-Process -Id $p.Id -Force
        Write-Host "Stopped spoof PID $($p.Id)."
    } catch {
        Write-Warning "Could not stop PID $($p.Id): $_"
    }
}
