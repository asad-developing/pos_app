@echo off
echo ============================================
echo  POS System - Installing Dependencies
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Installing Flask...
pip install flask

echo.
echo ============================================
echo  Installation complete!
echo  Run "run.bat" to start the POS system.
echo ============================================
pause
