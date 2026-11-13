$env:PYTHONHOME = "C:\Program Files\MySQL\MySQL Shell 8.0\lib\Python3.13"
$env:PYTHONPATH = "C:\Program Files\MySQL\MySQL Shell 8.0\lib\Python3.13\Lib;$PSScriptRoot"
$pythonExe = "C:\Program Files\MySQL\MySQL Shell 8.0\lib\Python3.13\Lib\venv\scripts\nt\python.exe"

Set-Location $PSScriptRoot

Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host " KHOI DONG HUNG PHAT EXPANSION AI AGENT - GIAO DIEN WEB UI (PORT 8080)" -ForegroundColor Green
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "[*] Dang khoi dong Web Server tai http://localhost:8080 ..." -ForegroundColor Yellow

Start-Process "http://localhost:8080"
& $pythonExe web_server.py

