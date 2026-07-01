@echo off
setlocal
chcp 65001 >nul

set "ROOT=%~dp0"
set "PY=python"
python --version >nul 2>nul
if errorlevel 1 (
  set "PY=py -3"
  py -3 --version >nul 2>nul
  if errorlevel 1 (
    echo Python was not found. Install Python 3 or add it to PATH.
    echo.
    pause
    exit /b 1
  )
)

echo Brainstorm Diagram Builder
echo ==========================
echo.
echo Starting local editor. If port 8765 is busy, the server will use the next available port.
echo Close this window or press Ctrl+C to stop the editor.
echo.
%PY% "%ROOT%scripts\diagram_builder_server.py"

endlocal
