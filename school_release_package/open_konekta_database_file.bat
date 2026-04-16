@echo off
setlocal
set "DB_PATH=%LOCALAPPDATA%\KONEKTA\konekta.db"

if not exist "%DB_PATH%" (
  echo Database not found: %DB_PATH%
  echo Start the game once first, then try again.
  pause
  exit /b 1
)

start "" "%DB_PATH%"
