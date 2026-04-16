@echo off
setlocal
set "DATA_DIR=%LOCALAPPDATA%\KONEKTA"
set "TARGET_DB=%DATA_DIR%\konekta.db"
set "TEMPLATE_DB=%~dp0konekta_template.db"

if not exist "%TEMPLATE_DB%" (
  echo Template database not found:
  echo %TEMPLATE_DB%
  pause
  exit /b 1
)

if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"

if exist "%TARGET_DB%" (
  for /f %%i in ('powershell -NoProfile -Command "(Get-Date).ToString('yyyyMMdd_HHmmss')"') do set "TS=%%i"
  set "OLD_BACKUP=%DATA_DIR%\konekta_before_template_%TS%.db"
  copy /Y "%TARGET_DB%" "%OLD_BACKUP%" >nul
  echo Existing database backed up.
)

copy /Y "%TEMPLATE_DB%" "%TARGET_DB%" >nul
echo Template database installed to:
echo %TARGET_DB%
pause
