@echo off
REM ArVision Installation Script
REM Usage: Double-click or run from command line

chcp 65001 >nul
echo ============================================
echo  AradVision Dependency Installer
echo ============================================
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

echo [1/4] Checking virtual environment...
if exist ".venv" (
    echo [INFO] Virtual environment exists
    set /p RECREATE="Recreate? (y/N): "
    if /i "!RECREATE!"=="y" (
        echo [DELETE] Removing old virtual environment...
        rmdir /s /q .venv
        python -m venv .venv
    )
) else (
    echo [CREATE] Creating virtual environment...
    python -m venv .venv
)

echo.
echo [2/4] Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo [3/4] Upgrading pip...
python -m pip install --upgrade pip --quiet

echo.
echo [4/4] Installing dependencies...
echo This may take a few minutes...
echo.

REM Install basic dependencies
pip install numpy PyYAML loguru pytest pytest-cov --quiet

REM Install PyQt5
pip install PyQt5 --quiet

REM Install screen capture
pip install mss --quiet

REM Install image processing
pip install opencv-python --quiet

REM Install Windows input control
pip install pydirectinput pywin32 --quiet

REM Install keyboard listener
pip install keyboard --quiet

REM YOLO dependencies (optional)
echo.
set /p INSTALL_YOLO="Install YOLO dependencies (torch/ultralytics)? Takes time (y/N): "
if /i "!INSTALL_YOLO!"=="y" (
    echo [INSTALL] YOLO dependencies...
    pip install ultralytics torch torchvision --quiet
) else (
    echo [SKIP] YOLO skipped. Install later with: pip install ultralytics torch torchvision
)

echo.
echo ============================================
echo Installation Complete!
echo ============================================
echo.
echo To start AradVision:
echo   1. Activate: .venv\Scripts\activate
echo   2. UI mode: python main.py --ui
echo   3. Console mode: python main.py
echo.
pause
