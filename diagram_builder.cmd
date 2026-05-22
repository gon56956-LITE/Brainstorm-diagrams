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
echo Starting local editor. If port 8765 is busy, the server will use the next available port.
echo Close this window or press Ctrl+C to stop the editor.
echo.
"%PY%" "%ROOT%scripts\diagram_builder_server.py"

endlocal
