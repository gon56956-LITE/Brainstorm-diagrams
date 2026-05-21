@echo off
setlocal
set "ROOT=%~dp0"
call "%ROOT%fmea_table_tool.cmd" %*
exit /b %ERRORLEVEL%
