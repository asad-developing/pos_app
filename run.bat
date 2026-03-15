@echo off
title POS System
cd /d "%~dp0"

:start
echo ============================================
echo  POS System Starting...
echo  Open browser at: http://localhost:5000
echo  Press Ctrl+C to stop.
echo ============================================
echo.

python app.py

echo.
echo  POS System stopped. Restarting in 3 seconds...
echo  (Close this window to exit completely)
timeout /t 3 /nobreak >nul
goto start
