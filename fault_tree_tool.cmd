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

:menu
cls
echo Fault Tree Diagram Tool
echo =======================
echo.
echo 1. Create new fault tree diagram
echo 2. Regenerate work SVG
echo 3. Verify testcases and templates
echo 4. Render stresscases
echo 5. Verify stresscases
echo 6. Exit
echo.
echo Notes:
echo - Diagram names create files under work\fault-tree\.
echo - Use lowercase letters, numbers, hyphen, or underscore only.
echo - Good examples: startup-failure, safety_chain_v1
echo - Do not enter spaces, folders, ..\, or full paths.
echo - Fault tree output is SVG.
echo.
set /p "choice=Choose 1-6: "

if "%choice%"=="1" goto create
if "%choice%"=="2" goto render
if "%choice%"=="3" goto verify
if "%choice%"=="4" goto stress
if "%choice%"=="5" goto vstress
if "%choice%"=="6" goto done
echo.
echo Invalid choice.
pause
goto menu

:create
echo.
set /p "name=Diagram name, for example startup-failure: "
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
"%PY%" "%ROOT%scripts\new_fault_tree.py" "%name%" --format "%format%"
echo.
pause
goto menu

:render
echo.
set /p "name=Diagram name, for example startup-failure: "
if "%name%"=="" (
  echo Name cannot be empty.
  pause
  goto menu
)
echo.
"%PY%" "%ROOT%scripts\render_fault_tree_work.py" "%name%"
echo.
pause
goto menu

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
