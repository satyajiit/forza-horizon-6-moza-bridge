@echo off
REM Build a single-file Windows exe so users don't need Python installed.
REM Run from this folder: build.bat

python -m PyInstaller --version >nul 2>nul
if errorlevel 1 (
    echo Installing PyInstaller for current user...
    python -m pip install --user pyinstaller || goto :fail
)

python -m PyInstaller ^
    --onefile ^
    --console ^
    --name fh6-moza-bridge ^
    --noconfirm ^
    fh6_moza_bridge.py || goto :fail

echo.
echo Done. Executable: dist\fh6-moza-bridge.exe
exit /b 0

:fail
echo Build failed.
exit /b 1
