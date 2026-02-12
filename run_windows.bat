@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo AradVision UI 模式启动脚本
echo ============================================================
echo.
echo 此脚本将：
echo   1. 激活 Python 虚拟环境
echo   2. 在虚拟环境中安装 PyQt5
echo   3. 启动 AradVision UI 模式
echo.
echo ============================================================
echo.

REM 激活虚拟环境
echo 正在激活 .venv 虚拟环境...
call .venv\Scripts\activate.bat

if %ERRORLEVEL% NEQ 0 (
    echo    [错误] 虚拟环境激活失败！
    echo    请检查 .venv 文件夹是否存在
    pause
    goto :end
)

REM 在虚拟环境中安装 PyQt5
echo 正在虚拟环境中安装 PyQt5...
python -m pip install PyQt5

if %ERRORLEVEL% NEQ 0 (
    echo    [错误] PyQt5 安装失败！
    echo    错误代码: %ERRORLEVEL%
    pause
    goto :end
)

REM 运行程序
echo ============================================================
echo 正在启动 AradVision UI 模式...
echo ============================================================
python main.py --ui

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [成功] UI 模式已启动！
    echo.
    echo ============================================================
    echo.
    echo 提示：按 Ctrl+C 可随时停止程序
    echo.
) else (
    echo.
    echo [错误] 程序运行失败！
    echo    错误代码: %ERRORLEVEL%
    pause
)

:end
echo ============================================================
echo.
pause
