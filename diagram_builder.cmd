@echo off
setlocal
chcp 65001 >nul

set "ROOT=%~dp0"
set "PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if not exist "%PY%" (
  echo Python runtime not found:
  echo %PY%
  echo.
  pause
  exit /b 1
)

echo Brainstorm Diagram Builder
echo ==========================
echo.
echo Stopping any previous Diagram Builder server...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>nul
echo.
echo Starting local editor at http://127.0.0.1:8765/
echo Close this window or press Ctrl+C to stop the editor.
echo.
"%PY%" "%ROOT%scripts\diagram_builder_server.py"

endlocal
