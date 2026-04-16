@echo off
set "DB_PATH=%LOCALAPPDATA%\KONEKTA\konekta.db"
echo This will reset KONEKTA local data for this Windows account.
echo Database path: %DB_PATH%
choice /M "Continue"
if errorlevel 2 goto :eof

if exist "%DB_PATH%" (
  del /f /q "%DB_PATH%"
  echo Database removed.
) else (
  echo Database file not found.
)

echo Done.
pause
