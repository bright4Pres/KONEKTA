@echo off
set "DATA_DIR=%LOCALAPPDATA%\KONEKTA"
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
start "" "%DATA_DIR%"
