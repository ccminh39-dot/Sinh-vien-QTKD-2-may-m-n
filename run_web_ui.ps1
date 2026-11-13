Set-Location $PSScriptRoot

Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host " KHOI DONG HUNG PHAT EXPANSION AI AGENT - GIAO DIEN WEB UI (PORT 8080)" -ForegroundColor Green
Write-Host "===============================================================================" -ForegroundColor Cyan

$pythonExe = $null

# 1. Kiem tra Virtual Environment (.venv hoac venv)
if (Test-Path "$PSScriptRoot\.venv\Scripts\python.exe") {
    $pythonExe = "$PSScriptRoot\.venv\Scripts\python.exe"
} elseif (Test-Path "$PSScriptRoot\venv\Scripts\python.exe") {
    $pythonExe = "$PSScriptRoot\venv\Scripts\python.exe"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExe = "py"
} elseif (Test-Path "C:\Program Files\MySQL\MySQL Shell 8.0\lib\Python3.13\Lib\venv\scripts\nt\python.exe") {
    $env:PYTHONHOME = "C:\Program Files\MySQL\MySQL Shell 8.0\lib\Python3.13"
    $env:PYTHONPATH = "C:\Program Files\MySQL\MySQL Shell 8.0\lib\Python3.13\Lib;$PSScriptRoot"
    $pythonExe = "C:\Program Files\MySQL\MySQL Shell 8.0\lib\Python3.13\Lib\venv\scripts\nt\python.exe"
}

if (-not $pythonExe) {
    Write-Host ""
    Write-Host "[LOI] Khong tim thay Python tren may tinh!" -ForegroundColor Red
    Write-Host "Vui long cai dat Python 3.9+ tu https://www.python.org/ (nho tich Add to PATH)." -ForegroundColor Yellow
    Write-Host ""
    Pause
    Exit
}

Write-Host "[*] Dang su dung Python: $pythonExe" -ForegroundColor Green
Write-Host "[*] Dang khoi dong Web Server tai http://localhost:8080 ..." -ForegroundColor Yellow
Start-Process "http://localhost:8080"
& $pythonExe web_server.py
