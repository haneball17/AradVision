# ArVision Installation Script (PowerShell)
# Usage: .\install.ps1

# UTF-8 with BOM encoding for Windows PowerShell compatibility

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " AradVision Dependency Installer" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "[1/6] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Please install Python 3.10+" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check/Create virtual environment
Write-Host ""
Write-Host "[2/6] Checking virtual environment..." -ForegroundColor Yellow
if (Test-Path ".\.venv") {
    Write-Host "[INFO] Virtual environment exists" -ForegroundColor Yellow
    $recreate = Read-Host "Recreate? (y/N)"
    if ($recreate -eq "y" -or $recreate -eq "Y") {
        Write-Host "[DELETE] Removing old virtual environment..." -ForegroundColor Red
        Remove-Item -Recurse -Force .\.venv
        python -m venv .\.venv
        Write-Host "[DONE] Virtual environment recreated" -ForegroundColor Green
    }
} else {
    Write-Host "[CREATE] Creating virtual environment..." -ForegroundColor Green
    python -m venv .\.venv
}

# Activate virtual environment
Write-Host ""
Write-Host "[3/6] Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host ""
Write-Host "[4/6] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

# Install dependencies
Write-Host ""
Write-Host "[5/6] Installing dependencies..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray

$packages = @(
    "numpy>=1.24.0",
    "PyYAML>=6.0",
    "loguru>=0.7.0",
    "PyQt5>=5.15.0",
    "mss>=9.0.0",
    "opencv-python>=4.8.0",
    "pydirectinput>=1.0.4",
    "pywin32>=305",
    "keyboard>=0.13.5",
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0"
)

foreach ($pkg in $packages) {
    Write-Host "Installing $pkg..." -ForegroundColor Gray
    pip install $pkg --quiet
}

# YOLO dependencies (optional)
Write-Host ""
Write-Host "[6/6] YOLO Detection..." -ForegroundColor Yellow
$installYOLO = Read-Host "Install YOLO dependencies (torch/ultralytics)? Takes time (y/N)"
if ($installYOLO -eq "y" -or $installYOLO -eq "Y") {
    Write-Host "Installing torch..." -ForegroundColor Gray
    pip install torch --quiet
    Write-Host "Installing torchvision..." -ForegroundColor Gray
    pip install torchvision --quiet
    Write-Host "Installing ultralytics..." -ForegroundColor Gray
    pip install ultralytics --quiet
    Write-Host "[DONE] YOLO dependencies installed" -ForegroundColor Green
} else {
    Write-Host "[SKIP] YOLO skipped. Install later: pip install ultralytics torch torchvision" -ForegroundColor Yellow
}

# Done
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start AradVision:" -ForegroundColor White
Write-Host "  1. Activate: .venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "  2. UI mode: python main.py --ui" -ForegroundColor Gray
Write-Host "  3. Console mode: python main.py" -ForegroundColor Gray
Write-Host ""
Read-Host "Press Enter to exit"
