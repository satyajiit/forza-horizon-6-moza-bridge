@echo off
REM One-click stop: kills the bridge exe + the ForzaHorizon5 spoof.

cd /d "%~dp0"

echo Stopping bridge exe (if running)...
taskkill /IM fh6-moza-bridge.exe /F >nul 2>nul
if errorlevel 1 (echo   no bridge exe was running.) else (echo   ok.)

echo Stopping ForzaHorizon5 spoof...
powershell -ExecutionPolicy Bypass -NoProfile -File "spoof\stop_spoof.ps1"

echo Done.
pause
