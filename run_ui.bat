@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo 正在虚拟环境中安装 PyQt5 并运行 AradVision...
echo ============================================================

REM 激活虚拟环境
call .venv\Scripts\activate.bat

REM 在虚拟环境中安装 PyQt5
python -m pip install PyQt5

REM 检查安装结果
python -c "import PyQt5; print('PyQt5 安装状态:', 'OK' if PyQt5 else 'FAILED')"

REM 运行程序
echo ============================================================
echo 正在启动 AradVision UI 模式...
echo ============================================================
python main.py --ui

echo ============================================================
echo 如果看到 UI 窗口，说明启动成功！
echo ============================================================

REM 暂停以查看输出
pause
