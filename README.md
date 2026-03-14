# AradVision

DNF 视觉自动化研究项目。当前仓库主线聚焦于固定路线 MVP、WGC/MSS 捕获链路、可选 PyQt 控制面板，以及围绕这些能力的 Mock 优先测试体系。

## 当前主线

- 固定路线运行链路：`CaptureEngine -> FixedRoutePipeline -> InputDriver`
- 捕获后端：Windows 优先 `WGC`，失败时可按配置降级到 `MSS`
- 视觉识别：当前主流程以 `MainViewReader`、`MinimapReader`、`StateReader` 为主，检测器保留兼容入口
- UI：`main.py --ui` 启动控制面板；时间线工作台保留为独立辅助入口
- 测试策略：优先 `mock`、单元测试、集成测试，再做真实环境验证

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

默认使用配置文件 `configs/config.yaml`：

```bash
# 控制台模式
python3 main.py -c configs/config.yaml

# UI 控制面板
python3 main.py -c configs/config.yaml --ui

# 真实环境（禁用 mock）
python3 main.py -c configs/config.yaml --no-mock
```

## 项目结构

```text
AradVision/
├── core/      # 配置、日志、异常、捕获后端
├── vision/    # 读图与识别：主画面、小地图、状态、坐标映射、检测器抽象
├── logic/     # 固定路线 MVP、守护层、维护流程、兼容状态机/世界模型
├── input/     # mock/real 输入驱动与紧急停止
├── ui/        # PyQt 控制面板与辅助工作台
├── configs/   # YAML 配置
├── scripts/   # 安装、验证、辅助脚本
├── tests/     # 单元测试与集成测试
├── docs/      # 当前主线文档与专题文档
└── main.py    # 应用入口
```

## 常用命令

```bash
# 单元与集成测试
python3 -m pytest -q

# 固定路线主链路相关测试
python3 -m pytest -q \
  tests/test_config_dungeon_run.py \
  tests/test_dungeon_run_pipeline.py \
  tests/integration/test_full_flow_mock.py

# 语法快速检查
python3 -m compileall core input logic vision ui tests main.py scripts

# UI 冒烟验证
python3 scripts/test_pyqt_ui.py
```

## 文档

- [文档导航](docs/README.md)
- [架构设计文档](docs/AradVision架构设计文档.md)
- [测试运行指南](docs/测试运行指南.md)
- [UI 启动指南](docs/UI启动指南.md)
- [WGC 窗口级捕获改造](docs/WGC窗口级捕获改造/WGC窗口级捕获改造.md)
- [歼灭追击战固定路线 MVP 改造](docs/歼灭追击战固定路线MVP改造/歼灭追击战固定路线MVP改造.md)

历史规划、阶段总结和非主线专题已迁入 `docs/archive/`，不再作为主入口文档。

## 说明

- 本项目仅用于受控环境下的自动化研究。
- `F12` 为紧急停止键，真实环境验证时必须保持可用。
