#!/bin/bash
# AradVision 一键安装脚本 (Linux/Mac)
# 用法: chmod +x install.sh && ./install.sh

set -e

echo "============================================"
echo "AradVision 依赖安装脚本"
echo "============================================"
echo ""

# 检查 Python
echo "[1/5] 检查 Python..."
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 python3，请先安装 Python 3.10+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "找到 $PYTHON_VERSION"

# 检查/创建虚拟环境
echo ""
echo "[2/5] 检查虚拟环境..."
if [ -d ".venv" ]; then
    echo "[提示] 虚拟环境已存在"
    read -p "是否重新创建? (y/N): " recreate
    if [ "$recreate" = "y" ] || [ "$recreate" = "Y" ]; then
        echo "[删除] 删除旧虚拟环境..."
        rm -rf .venv
        python3 -m venv .venv
        echo "[完成] 虚拟环境已重建"
    fi
else
    echo "[创建] 虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
echo ""
echo "[3/5] 激活虚拟环境..."
source .venv/bin/activate

# 升级 pip
echo ""
echo "[4/5] 升级 pip..."
pip install --upgrade pip --quiet

# 安装依赖
echo ""
echo "[5/5] 安装依赖包..."
echo "这可能需要几分钟，请耐心等待..."

# 基础依赖
pip install numpy PyYAML loguru pytest pytest-cov --quiet

# PyQt5
pip install PyQt5 --quiet

# 屏幕捕获
pip install mss --quiet

# 图像处理
pip install opencv-python --quiet

# YOLO 依赖（可选）
echo ""
read -p "是否安装 YOLO 检测依赖 (torch/ultralytics)? 需要较长时间 (y/N): " install_yolo
if [ "$install_yolo" = "y" ] || [ "$install_yolo" = "Y" ]; then
    echo "[安装] YOLO 依赖..."
    pip install ultralytics torch torchvision --quiet
    echo "[完成] YOLO 依赖已安装"
else
    echo "[跳过] YOLO 依赖已跳过，可稍后运行: pip install ultralytics torch torchvision"
fi

# 注意：Linux 下不需要 pydirectinput/pywin32/keyboard
echo ""
echo "[提示] Linux 跳过了 Windows 相关依赖 (pydirectinput, pywin32, keyboard)"

# 完成
echo ""
echo "============================================"
echo "安装完成！"
echo "============================================"
echo ""
echo "启动方式:"
echo "  1. 激活虚拟环境: source .venv/bin/activate"
echo "  2. 运行 UI 模式: python main.py --ui"
echo "  3. 运行控制台模式: python main.py"
echo ""
