# Start ForzaHorizon5.exe spoof process.
#
# MOZA Pit House only opens its FH5 telemetry listener (UDP :30055) when
# it sees a running process named "ForzaHorizon5.exe". Since you're
# actually playing FH6, that check never trips - so we satisfy it with
# a harmless renamed copy of ping.exe pinging localhost in the background.
#
# Run from this folder:   .\start_spoof.ps1
# Stop it later with:      .\stop_spoof.ps1

$ErrorActionPreference = "Stop"

$spoofExe = Join-Path $PSScriptRoot "ForzaHorizon5.exe"

if (-not (Test-Path $spoofExe)) {
    $src = Join-Path $env:WINDIR "System32\PING.EXE"
    if (-not (Test-Path $src)) { Write-Error "Could not find ping.exe at $src"; exit 1 }
    Copy-Item -Path $src -Destination $spoofExe -Force
    Write-Host "Created spoof exe: $spoofExe"
}

$existing = Get-Process -Name "ForzaHorizon5" -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Spoof already running (PID $($existing.Id)). Nothing to do."
    exit 0
}

$proc = Start-Process -FilePath $spoofExe `
                      -ArgumentList "-t","-w","1000","127.0.0.1" `
                      -WindowStyle Hidden -PassThru
Write-Host "Spoof started, PID $($proc.Id)."
Write-Host "Pit House should now detect 'ForzaHorizon5' as running and bind UDP :30055."
