@echo off
REM AradVision 一键安装脚本 (中文版)
REM 用法: 双击运行

echo ============================================
echo  AradVision 依赖安装脚本
echo ============================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

echo [1/4] 检查虚拟环境...
if exist ".venv" (
    echo [提示] 虚拟环境已存在
    set /p RECREATE="是否重新创建? (y/N): "
    if /i "!RECREATE!"=="y" (
        echo [删除] 删除旧虚拟环境...
        rmdir /s /q .venv
        python -m venv .venv
    )
) else (
    echo [创建] 虚拟环境...
    python -m venv .venv
)

echo.
echo [2/4] 激活虚拟环境...
call .venv\Scripts\activate.bat

echo.
echo [3/4] 升级 pip...
python -m pip install --upgrade pip --quiet

echo.
echo [4/4] 安装依赖包...
echo 这可能需要几分钟，请耐心等待...
echo.

REM 安装基础依赖
pip install numpy PyYAML loguru pytest pytest-cov --quiet

REM 安装 PyQt5
pip install PyQt5 --quiet

REM 安装屏幕捕获
pip install mss --quiet

REM 安装图像处理
pip install opencv-python --quiet

REM 安装 Windows 输入控制
pip install pydirectinput pywin32 --quiet

REM 安装键盘监听
pip install keyboard --quiet

REM 安装 YOLO（可选，需要较长时间）
echo.
set /p INSTALL_YOLO="是否安装 YOLO 检测依赖 (torch/ultralytics)? 这需要较长时间 (y/N): "
if /i "!INSTALL_YOLO!"=="y" (
    echo [安装] YOLO 依赖...
    pip install ultralytics torch torchvision --quiet
) else (
    echo [跳过] YOLO 依赖已跳过，可稍后手动安装
)

echo.
echo ============================================
echo 安装完成！
echo ============================================
echo.
echo 启动方式:
echo   1. 激活虚拟环境: .venv\Scripts\activate
echo   2. 运行 UI 模式: python main.py --ui
echo   3. 运行控制台模式: python main.py
echo.
pause
