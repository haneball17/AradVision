@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo AradVision UI 模式启动（简化版）
echo ============================================================

echo 此脚本将完成以下操作：
echo   1. 切换到项目目录
echo   2. 激活虚拟环境并安装 PyQt5
echo   3. 启动 AradVision UI 模式
echo.
echo ============================================================
echo.

cd /d D:\code\AradVision || goto :error

REM 激活虚拟环境并安装 PyQt5
echo 正在激活 .venv 虚拟环境...
call .venv\Scripts\activate.bat

echo.
echo 正在虚拟环境中安装 PyQt5...
python -m pip install PyQt5 --quiet

REM 检查安装结果
if %ERRORLEVEL% NEQ 0 (
    echo    [错误] PyQt5 安装失败
    echo    错误代码: %ERRORLEVEL%
    goto :pause
)

REM 启动程序
echo.
echo 正在启动 AradVision UI 模式...
python main.py --ui

echo.
echo ============================================================
echo.
echo 如果看到 UI 窗口，说明启动成功！
echo.
echo ============================================================
echo.
echo 提示：按 Ctrl+C 可随时停止程序
echo.
pause
goto :end

:error
echo.
echo    [错误] 无法切换到项目目录！
echo    请确认项目路径：D:\code\AradVision
echo.
pause
goto :end
