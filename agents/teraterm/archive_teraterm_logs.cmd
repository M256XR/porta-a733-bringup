@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%archive_teraterm_logs.ps1" -TouchNewCurrentLog
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" (
  echo Failed with exit code %RC%.
) else (
  echo Completed.
)
pause
exit /b %RC%
