@echo off
REM One-click start: launches the ForzaHorizon5 process spoof + the bridge.
REM Double-click this file to begin a session. Ctrl+C in this window stops
REM the bridge; run stop_all.bat afterwards to also clean up the spoof.

cd /d "%~dp0"

echo === FH6 -> MOZA Pit House bridge ===
echo.
echo Starting ForzaHorizon5.exe process spoof...
powershell -ExecutionPolicy Bypass -NoProfile -File "spoof\start_spoof.ps1"
echo.

if exist "dist\fh6-moza-bridge.exe" (
    echo Launching bridge from dist\fh6-moza-bridge.exe ...
    echo.
    "dist\fh6-moza-bridge.exe" --inspect
) else (
    echo Bridge exe not built. Falling back to python...
    echo.
    python fh6_moza_bridge.py --inspect
)

echo.
echo Bridge stopped. The ForzaHorizon5 spoof is still running.
echo Run stop_all.bat to shut it down before quitting.
pause
