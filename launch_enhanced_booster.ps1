# =============================================
# Signal Booster Enhanced Launcher
# Launches Signal Booster with optimized settings for >85% signal strength
# =============================================

Write-Host "
=============================================
   Signal Booster - Enhanced Edition
   Targeting >85% Signal Strength
=============================================
" -ForegroundColor Cyan

# Check for administrative privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "This script must be run as an Administrator to apply network optimizations." -ForegroundColor Red
    Write-Host "Please run PowerShell as an Administrator and try again." -ForegroundColor Yellow
    
    # Prompt to restart as admin
    $restart = Read-Host "Would you like to restart this script as Administrator? (y/n)"
    if ($restart -eq "y") {
        Start-Process PowerShell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    }
    exit
}

# Ensure we're in the correct directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Verify Python virtual environment exists
if (-not (Test-Path ".\venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    
    if (-not $?) {
        Write-Host "Failed to create virtual environment. Please ensure Python is installed correctly." -ForegroundColor Red
        exit 1
    }
}

# Activate the virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install or update the package
Write-Host "Installing Signal Booster package..." -ForegroundColor Yellow
pip install -e . --quiet

# Launch Signal Booster with enhanced settings
Write-Host "Launching Signal Booster with enhanced signal optimization settings..." -ForegroundColor Green
Write-Host "Target: > 85% Signal Strength with Professional Visualizations" -ForegroundColor Cyan
Write-Host ""

# Start Signal Booster with aggressive mode and monitoring for maximum performance
signal-booster start --aggressive --monitor

# Keep the window open
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 