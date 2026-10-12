<#
.SYNOPSIS
    Convenience orchestrator for the Micro-Zone Disaster Prediction System.
.DESCRIPTION
    Run tests, train the LSTM model, or launch development servers.
.EXAMPLE
    .\scripts\run_system.ps1 -Test
    .\scripts\run_system.ps1 -Train
    .\scripts\run_system.ps1 -Backend
    .\scripts\run_system.ps1 -Frontend
#>

param (
    [switch]$Test,
    [switch]$Train,
    [switch]$AlertTest,
    [switch]$EmailTest,
    [switch]$LiveSync,
    [switch]$Backend,
    [switch]$Frontend,
    [switch]$All
)

$RootDir = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $RootDir "venv\Scripts\python.exe"
$PytestExe = Join-Path $RootDir "venv\Scripts\pytest.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Virtual environment python not found at $PythonExe. Please run: python -m venv venv"
    exit 1
}

if ($Test) {
    Write-Host "Running Backend Automated Test Suite..." -ForegroundColor Cyan
    Set-Location (Join-Path $RootDir "backend")
    & $PytestExe -v
    Set-Location $RootDir
    exit $LASTEXITCODE
}

if ($Train) {
    Write-Host "Executing Stacked LSTM Model Training Pipeline..." -ForegroundColor Cyan
    & $PythonExe (Join-Path $RootDir "scripts\train_model.py")
    exit $LASTEXITCODE
}

if ($AlertTest) {
    Write-Host "Verifying Prediction & Authority Dispatch Pipeline..." -ForegroundColor Cyan
    & $PythonExe (Join-Path $RootDir "scripts\test_high_risk_alert.py")
    exit $LASTEXITCODE
}

if ($EmailTest) {
    Write-Host "Verifying Human Behavior Aware Email Alert Dispatch..." -ForegroundColor Cyan
    & $PythonExe (Join-Path $RootDir "scripts\test_email_alert.py")
    exit $LASTEXITCODE
}

if ($LiveSync) {
    Write-Host "Synchronizing Live Internet Weather & Running AI Prediction..." -ForegroundColor Cyan
    & $PythonExe (Join-Path $RootDir "scripts\test_live_weather.py")
    exit $LASTEXITCODE
}

if ($Backend) {
    Write-Host "Starting Flask Backend Server (Port 5000)..." -ForegroundColor Green
    Set-Location (Join-Path $RootDir "backend")
    & $PythonExe run.py
    exit $LASTEXITCODE
}

if ($Frontend) {
    Write-Host "Starting React Vite Frontend Server (Port 5173)..." -ForegroundColor Green
    Set-Location (Join-Path $RootDir "frontend")
    npm run dev
    exit $LASTEXITCODE
}

if ($All) {
    Write-Host "Opening separate terminal windows for Backend and Frontend..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$RootDir\backend'; & '$PythonExe' run.py"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$RootDir\frontend'; npm run dev"
    exit 0
}

Write-Host "Usage: .\scripts\run_system.ps1 [-Test | -Train | -Backend | -Frontend | -All]" -ForegroundColor Yellow
