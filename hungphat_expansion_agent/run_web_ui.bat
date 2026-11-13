@echo off
setlocal enabledelayedexpansion
title Hung Phat Expansion AI Agent - Web UI
echo ===============================================================================
echo   KHOI DONG HUNG PHAT EXPANSION AI AGENT - GIAO DIEN WEB UI (PORT 8080)
echo ===============================================================================

cd /d "%~dp0"

:: 1. Kiem tra Virtual Environment (.venv hoac venv)
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
    goto :FOUND_PYTHON
)
if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=venv\Scripts\python.exe"
    goto :FOUND_PYTHON
)

:: 2. Kiem tra lenh python trong PATH he thong
where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python"
    goto :FOUND_PYTHON
)

:: 3. Kiem tra lenh py (Python Launcher tren Windows)
where py >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=py"
    goto :FOUND_PYTHON
)

:: 4. Fallback: Kiem tra duong dan Python MySQL Shell tren may lab phong thi
if exist "C:\Program Files\MySQL\MySQL Shell 8.0\lib\Python3.13\Lib\venv\scripts\nt\python.exe" (
    set "PYTHONHOME=C:\Program Files\MySQL\MySQL Shell 8.0\lib\Python3.13"
    set "PYTHONPATH=C:\Program Files\MySQL\MySQL Shell 8.0\lib\Python3.13\Lib;%~dp0"
    set "PYTHON_EXE=C:\Program Files\MySQL\MySQL Shell 8.0\lib\Python3.13\Lib\venv\scripts\nt\python.exe"
    goto :FOUND_PYTHON
)

:: Neu khong tim thay Python
echo.
echo [LOI] Khong tim thay Python tren may tinh cua ban!
echo Vui long cai dat Python 3.9+ tai: https://www.python.org/downloads/
echo LUU Y: Khi cai dat, nho tich chon "Add python.exe to PATH".
echo.
pause
exit /b 1

:FOUND_PYTHON
echo [*] Dang su dung Python: !PYTHON_EXE!
echo [*] Dang khoi dong Web Server tai http://localhost:8080 ...
start http://localhost:8080
"!PYTHON_EXE!" web_server.py
if %errorlevel% neq 0 (
    echo.
    echo [LOI] Co van de xay ra khi chay web_server.py.
    pause
)
