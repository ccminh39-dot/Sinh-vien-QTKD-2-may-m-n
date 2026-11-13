@echo off
echo ===============================================================================
echo  KHOI DONG HUNG PHAT EXPANSION AI AGENT - GIAO DIEN WEB UI (PORT 8080)
echo ===============================================================================

set "PYTHONHOME=C:\Program Files\MySQL\MySQL Shell 8.0\lib\Python3.13"
set "PYTHONPATH=C:\Program Files\MySQL\MySQL Shell 8.0\lib\Python3.13\Lib;%~dp0"
set "PYTHON_EXE=C:\Program Files\MySQL\MySQL Shell 8.0\lib\Python3.13\Lib\venv\scripts\nt\python.exe"

cd /d "%~dp0"

echo [*] Dang khoi dong Web Server tai http://localhost:8080 ...
start http://localhost:8080
"%PYTHON_EXE%" web_server.py
pause

