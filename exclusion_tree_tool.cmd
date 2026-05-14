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

if /i "%~1"=="verify" goto vnp
if /i "%~1"=="stress" goto snp
if /i "%~1"=="verify-stress" goto vstressnp
if /i "%~1"=="export-png" goto pnp

:menu
cls
echo Exclusion Tree Diagram Tool
echo ===========================
echo.
echo 1. Create new exclusion tree diagram
echo 2. Regenerate work SVG
echo 3. Export work SVG to PNG
echo 4. Verify testcases and templates
echo 5. Render stresscases
echo 6. Verify stresscases
echo 7. Exit
echo.
echo Notes:
echo - Diagram names create files under work\exclusion-tree\.
echo - Use lowercase letters, numbers, hyphen, or underscore only.
echo - Good examples: startup-checks, field_return_v1
echo - Do not enter spaces, folders, ..\, or full paths.
echo - SVG is editable. PNG is for quick sharing.
echo.
set /p "choice=Choose 1-7: "

if "%choice%"=="1" goto create
if "%choice%"=="2" goto render
if "%choice%"=="3" goto png
if "%choice%"=="4" goto verify
if "%choice%"=="5" goto stress
if "%choice%"=="6" goto vstress
if "%choice%"=="7" goto done
echo.
echo Invalid choice.
pause
goto menu

:create
echo.
set /p "name=Diagram name, for example startup-checks: "
if "%name%"=="" (
  echo Name cannot be empty.
  pause
  goto menu
)
echo.
echo Format:
echo 1. Markdown ^(recommended^)
echo 2. JSON
set /p "format_choice=Choose 1-2: "
set "format=md"
if "%format_choice%"=="2" set "format=json"
echo.
"%PY%" "%ROOT%scripts\new_exclusion_tree.py" "%name%" --format "%format%"
echo.
pause
goto menu

:render
echo.
set /p "name=Diagram name, for example startup-checks: "
if "%name%"=="" (
  echo Name cannot be empty.
  pause
  goto menu
)
echo.
"%PY%" "%ROOT%scripts\render_exclusion_tree_work.py" "%name%"
echo.
pause
goto menu

:png
echo.
set /p "name=Diagram name, for example startup-checks: "
if "%name%"=="" (
  echo Name cannot be empty.
  pause
  goto menu
)
echo.
"%PY%" "%ROOT%scripts\export_exclusion_tree_png.py" "%name%"
echo.
pause
goto menu

:pnp
if "%~2"=="" (
  echo Diagram name is required.
  exit /b 1
)
"%PY%" "%ROOT%scripts\export_exclusion_tree_png.py" "%~2"
exit /b %ERRORLEVEL%

:verify
echo.
"%PY%" "%ROOT%scripts\verify_testcases.py"
echo.
pause
goto menu

:vnp
"%PY%" "%ROOT%scripts\verify_testcases.py"
exit /b %ERRORLEVEL%

:stress
echo.
"%PY%" "%ROOT%scripts\render_stresscases.py"
echo.
pause
goto menu

:snp
"%PY%" "%ROOT%scripts\render_stresscases.py"
exit /b %ERRORLEVEL%

:vstress
echo.
"%PY%" "%ROOT%scripts\verify_stresscases.py"
echo.
pause
goto menu

:vstressnp
"%PY%" "%ROOT%scripts\verify_stresscases.py"
exit /b %ERRORLEVEL%

:done
endlocal
