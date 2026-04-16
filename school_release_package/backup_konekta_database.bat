@echo off
setlocal
set "DATA_DIR=%LOCALAPPDATA%\KONEKTA"
set "DB_PATH=%DATA_DIR%\konekta.db"

if not exist "%DB_PATH%" (
  echo Database not found: %DB_PATH%
  echo Start the game once first, then try again.
  pause
  exit /b 1
)

for /f %%i in ('powershell -NoProfile -Command "(Get-Date).ToString('yyyyMMdd_HHmmss')"') do set "TS=%%i"
set "BACKUP_PATH=%DATA_DIR%\konekta_backup_%TS%.db"
copy /Y "%DB_PATH%" "%BACKUP_PATH%" >nul

echo Backup created:
echo %BACKUP_PATH%
pause
