@echo off
setlocal enabledelayedexpansion
title Hung Phat AI Agent - Automated Test Suite
echo ===============================================================================
echo   CHAY KIEM THU TU DONG (3 KICH BAN AI301)
echo ===============================================================================

cd /d "%~dp0"

set "PYTHON_EXE=python"
if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=.venv\Scripts\python.exe"
if exist "venv\Scripts\python.exe" set "PYTHON_EXE=venv\Scripts\python.exe"
where python >nul 2>&1 || (where py >nul 2>&1 && set "PYTHON_EXE=py")
if exist "C:\Program Files\MySQL\MySQL Shell 8.0\lib\Python3.13\Lib\venv\scripts\nt\python.exe" (
    set "PYTHONHOME=C:\Program Files\MySQL\MySQL Shell 8.0\lib\Python3.13"
    set "PYTHONPATH=C:\Program Files\MySQL\MySQL Shell 8.0\lib\Python3.13\Lib;%~dp0"
    set "PYTHON_EXE=C:\Program Files\MySQL\MySQL Shell 8.0\lib\Python3.13\Lib\venv\scripts\nt\python.exe"
)

echo [*] Su dung Python: %PYTHON_EXE%
"%PYTHON_EXE%" tests\test_cases.py
echo.
echo ===============================================================================
pause

