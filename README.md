# AradVision

<div align="center">

**DNF 视觉辅助自动化系统**

基于计算机视觉和 AI 决策的游戏辅助工具，采用非侵入式设计（无内存注入）。

[Python 3.10+](https://www.python.org/) | [PyQt5](https://pypi.org/project/PyQt5/) | [YOLOv8](https://github.com/ultralytics/ultralytics)

</div>

---

## 特性

- **视觉检测** - 基于 YOLOv8 的目标检测
- **AI 决策** - 智能状态机与战斗逻辑
- **2.5D 定位** - DNF Y 轴对齐算法
- **UI 控制面板** - 实时监控、参数配置、日志查看
- **紧急停止** - F12 键立即停止所有操作
- **跨平台** - Windows/Linux/macOS 支持

---

## 快速开始

### Windows 用户

```powershell
# 克隆项目
git clone https://github.com/haneball17/AradVision.git
cd AradVision

# 运行安装脚本（推荐）
.\scripts\install.ps1

# 或使用批处理脚本
.\scripts\install.bat
```

### Linux/macOS 用户

```bash
# 克隆项目
git clone https://github.com/haneball17/AradVision.git
cd AradVision

# 运行安装脚本
chmod +x scripts/install.sh
./scripts/install.sh
```

### 运行程序

```powershell
# 激活虚拟环境
.venv\Scripts\activate      # Windows
source .venv/bin/activate  # Linux/macOS

# UI 模式（推荐）
python main.py --ui

# 控制台模式
python main.py
```

---

## 项目结构

```
AradVision/
├── core/              # 核心模块（配置、日志、捕获）
├── vision/            # 视觉模块（YOLO 检测、坐标映射）
├── logic/             # 业务逻辑（状态机、战斗、路径规划）
├── input/             # 输入模块（键盘、鼠标控制）
├── ui/                # UI 界面（PyQt5 控制面板）
│   ├── widgets/       # UI 组件
│   ├── threads/       # 工作线程
│   └── themes/        # 主题配置
├── configs/           # 配置文件
├── scripts/           # 工具脚本
├── tests/             # 测试文件
└── main.py            # 程序入口
```

---

## 配置

配置文件位于 `configs/config.yaml`：

```yaml
# 截图配置
capture:
  window_title: 地下城与勇士  # 游戏窗口标题
  use_mock: false                # 是否使用 Mock 模式
  target_fps: 30                 # 目标帧率

# 检测器配置
detector:
  type: mock                     # mock 或 yolo
  confidence_threshold: 0.6        # 置信度阈值

# 输入配置
input:
  type: mock                      # mock 或 real
  delay_min: 0.05               # 最小延迟（秒）

# 战斗配置
combat:
  y_tolerance: 15                 # Y 轴对齐容差（像素）
  attack_range: 150               # 攻击距离
```

---

## 依赖说明

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 运行环境 |
| PyQt5 | 5.15+ | UI 界面 |
| mss | 9.0+ | 屏幕捕获 |
| opencv-python | 4.8+ | 图像处理 |
| pywin32 | 305+ | Windows 窗口查找 |
| pydirectinput | 1.0+ | DirectX 输入 |
| ultralytics | 8.0+ | YOLO 检测（可选） |
| torch | 2.0+ | 模型推理（可选） |

---

## 开发

```bash
# 运行测试
pytest tests/ -v

# 代码风格检查
pylint core/ --errors-only

# 类型检查
mypy core/
```

---

## 文档

- [开发计划与里程碑](docs/AradVision开发计划与里程碑.md)
- [架构设计文档](docs/AradVision架构设计文档.md)
- [模块接口契约规范](docs/AradVision模块接口契约规范.md)
- [编码规范与风格指南](docs/AradVision编码规范与风格指南.md)
- [YOLO 训练指南](docs/AradVision_YOLO训练专项指南.md)

---

## 安全声明

本项目仅供学习交流使用，请遵守游戏服务条款。使用本工具造成的任何后果由使用者自行承担。

---

## 许可证

MIT License

---

## 作者

[haneball17](https://github.com/haneball17) | [yangmq17](https://github.com/yangmq17)

---

<div align="center">

**Made with ❤️ for DNF players**

</div>
