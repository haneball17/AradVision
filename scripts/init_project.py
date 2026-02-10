"""
项目初始化脚本 - 创建项目目录结构

使用方法:
    python scripts/init_project.py

Author: Dev B
Date: Day 1 上午
"""

import os
from pathlib import Path

def create_project_structure():
    """创建项目目录结构"""

    # 项目根目录
    root = Path(".")

    # 定义目录结构
    directories = [
        # 核心代码
        "core",
        "logic",
        "vision",
        "input",

        # 测试
        "tests/unit",
        "tests/integration",
        "tests/fixtures",

        # 资源文件
        "assets/images/raw",
        "assets/images/train",
        "assets/images/val",
        "assets/weights",
        "assets/templates",

        # 配置文件
        "configs",

        # 日志
        "logs",

        # 文档
        "docs",
    ]

    # 创建目录
    print("📁 创建项目目录结构...")
    for directory in directories:
        dir_path = root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {directory}/")

    # 创建空的__init__.py文件
    print("\n📝 创建Python包文件...")
    for package_dir in ["core", "logic", "vision", "input", "tests"]:
        init_file = root / package_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""AradVision package"""\n')
            print(f"  ✓ {package_dir}/__init__.py")

    # 创建配置文件模板
    print("\n⚙️  创建配置文件模板...")
    config_template = """# AradVision Configuration File
# 配置说明: https://github.com/your-repo/docs/config.md

system:
  fps_limit: 30
  debug_window: true
  log_level: "INFO"
  emergency_stop_key: "F12"

game:
  window_title: "Dungeon & Fighter"
  resolution: [800, 600]
  class_names: ["monster", "hero", "item", "gate", "boss"]

vision:
  model_path: "./assets/weights/yolov8n_dnf.pt"
  conf_threshold: 0.65
  iou_threshold: 0.45
  device: "cuda"  # cuda or cpu

  # Y轴对齐参数
  y_align_tolerance: 15
  foot_point_offset: 0.95  # 落地点修正系数

combat:
  # 攻击距离阈值 (像素)
  attack_range_x: 120
  attack_range_y: 15

  # 目标选择策略
  target_selection: "nearest"  # nearest, weakest, strongest

  # 连招配置
  combo_sequence: ["X", "A", "S", "D"]
  combo_delay: [0.1, 0.15, 0.2, 0.3]

keys:
  # 方向键
  up: "UP"
  down: "DOWN"
  left: "LEFT"
  right: "RIGHT"

  # 战斗键
  attack: "x"
  jump: "space"
  pickup: "z"

  # 技能键
  skill_1: "a"
  skill_2: "s"
  skill_3: "d"
  skill_4: "f"

  # 消耗品
  potion_hp: "1"
  potion_mp: "2"
  buff: "space"

# 随机化参数 (反检测)
anti_detection:
  input_delay_min: 0.05  # 50ms
  input_delay_max: 0.15  # 150ms
  input_jitter_std: 0.02  # 标准差 20ms

# 路径规划
navigation:
  obstacle_threshold: 100
  stuck_detection_time: 5.0  # 5秒
  unstuck_strategy: "random_escape"
"""

    config_file = root / "configs" / "config.yaml"
    if not config_file.exists():
        config_file.write_text(config_template)
        print(f"  ✓ configs/config.yaml")

    # 创建.gitignore
    print("\n🔒 创建.gitignore...")
    gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Project
logs/*.log
*.log
assets/images/raw/*
!assets/images/raw/.gitkeep

# Model weights (大文件，用Git LFS)
*.pt
*.pth
*.onnx

# Config (个人配置)
configs/my_config.yaml

# Test coverage
.coverage
htmlcov/
.pytest_cache/

# OS
.DS_Store
Thumbs.db
"""

    gitignore_file = root / ".gitignore"
    if not gitignore_file.exists():
        gitignore_file.write_text(gitignore)
        print(f"  ✓ .gitignore")

    # 创建requirements.txt
    print("\n📦 创建requirements.txt...")
    requirements = """# Core dependencies
ultralytics>=8.0.0
opencv-python>=4.8.0
mss>=9.0.0
PyYAML>=6.0
loguru>=0.7.0

# Input control
pydirectinput>=1.0.0

# Windows specific (comment out if on Linux)
pywin32>=306; sys_platform == 'win32'

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0

# Development
black>=23.0.0
isort>=5.12.0
mypy>=1.4.0

# Data processing
numpy>=1.24.0
pillow>=10.0.0

# Optional: GPU acceleration
# torch>=2.0.0+cu118 --extra-index-url https://download.pytorch.org/whl/cu118
"""

    requirements_file = root / "requirements.txt"
    if not requirements_file.exists():
        requirements_file.write_text(requirements)
        print(f"  ✓ requirements.txt")

    # 创建README.md
    print("\n📖 创建README.md...")
    readme = """# AradVision

基于计算机视觉的DNF自动化辅助系统

## 快速开始

### 环境配置

```bash
# 创建虚拟环境
conda create -n aradvision python=3.10
conda activate aradvision

# 安装依赖
pip install -r requirements.txt
```

### 数据收集

```bash
# 启动游戏后，运行数据收集脚本
python scripts/capture_training_data.py
```

### 模型训练

```bash
# 标注数据后，训练YOLO模型
python vision/train_yolo.py
```

### 运行系统

```bash
# 启动自动化系统
python main.py
```

## 项目文档

- [开发计划与里程碑](docs/AradVision开发计划与里程碑.md)
- [模块接口契约规范](docs/AradVision模块接口契约规范.md)
- [分模块开发指南](docs/AradVision分模块开发指南.md)
- [测试策略与验收规范](docs/AradVision测试策略与验收规范.md)
- [编码规范与风格指南](docs/AradVision编码规范与风格指南.md)

## 开发者

- Dev A (AI专家): 模型训练、数据处理
- Dev B (架构专家): 系统框架、业务逻辑

## 许可证

仅供学习研究使用，请勿用于商业用途。
"""

    readme_file = root / "README.md"
    if not readme_file.exists():
        readme_file.write_text(readme)
        print(f"  ✓ README.md")

    print("\n" + "=" * 60)
    print("✅ 项目初始化完成！")
    print("=" * 60)
    print()
    print("下一步:")
    print("  1. Dev A: 运行 python scripts/capture_training_data.py")
    print("  2. Dev B: 开始实现 core/config_loader.py")
    print()

if __name__ == "__main__":
    create_project_structure()
