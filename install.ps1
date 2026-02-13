# AradVision 一键安装脚本 (PowerShell)
# 用法: .\install.ps1

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "AradVision 依赖安装脚本" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
Write-Host "[1/6] 检查 Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 未找到 Python，请先安装 Python 3.10+" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}
Write-Host "找到 $pythonVersion" -ForegroundColor Green

# 检查/创建虚拟环境
Write-Host ""
Write-Host "[2/6] 检查虚拟环境..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "[提示] 虚拟环境已存在" -ForegroundColor Yellow
    $recreate = Read-Host "是否重新创建? (y/N)"
    if ($recreate -eq "y" -or $recreate -eq "Y") {
        Write-Host "[删除] 删除旧虚拟环境..." -ForegroundColor Red
        Remove-Item -Recurse -Force .venv
        python -m venv .venv
        Write-Host "[完成] 虚拟环境已重建" -ForegroundColor Green
    }
} else {
    Write-Host "[创建] 虚拟环境..." -ForegroundColor Green
    python -m venv .venv
}

# 激活虚拟环境
Write-Host ""
Write-Host "[3/6] 激活虚拟环境..." -ForegroundColor Yellow
& .venv\Scripts\Activate.ps1

# 升级 pip
Write-Host ""
Write-Host "[4/6] 升级 pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

# 安装依赖
Write-Host ""
Write-Host "[5/6] 安装依赖包..." -ForegroundColor Yellow
Write-Host "这可能需要几分钟，请耐心等待..." -ForegroundColor Gray

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
    Write-Host "安装 $pkg..." -ForegroundColor Gray
    pip install $pkg --quiet
}

# YOLO 依赖（可选）
Write-Host ""
Write-Host "[6/6] YOLO 检测依赖..." -ForegroundColor Yellow
$installYOLO = Read-Host "是否安装 YOLO 依赖 (torch/ultralytics)? 需要较长时间 (y/N)"
if ($installYOLO -eq "y" -or $installYOLO -eq "Y") {
    Write-Host "安装 torch..." -ForegroundColor Gray
    pip install torch --quiet
    Write-Host "安装 torchvision..." -ForegroundColor Gray
    pip install torchvision --quiet
    Write-Host "安装 ultralytics..." -ForegroundColor Gray
    pip install ultralytics --quiet
    Write-Host "[完成] YOLO 依赖已安装" -ForegroundColor Green
} else {
    Write-Host "[跳过] YOLO 依赖已跳过，可稍后运行: pip install ultralytics torch torchvision" -ForegroundColor Yellow
}

# 完成
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "安装完成！" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "启动方式:" -ForegroundColor White
Write-Host "  1. 激活虚拟环境: .venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "  2. 运行 UI 模式: python main.py --ui" -ForegroundColor Gray
Write-Host "  3. 运行控制台模式: python main.py" -ForegroundColor Gray
Write-Host ""
Read-Host "按回车退出"
