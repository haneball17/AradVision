# AradVision

AradVision 当前主线聚焦于 DNF 自动化运行链路：屏幕捕获、目标检测、世界模型、状态机决策和输入执行。

## 当前方向

- 主线目标是自动化运行链路，而不是训练数据工作台。
- “训练数据资产管理工作台”已暂停，相关实现已归档到 `docs/workbench-v2-refactor` 分支，并在本地打上 `archive/workbench-v2-freeze-2026-03` 标签。
- 训练资产获取改为“外部工具录制游戏视频流 + 仓库内仅维护导入规范”的方式。

## 当前能力

- 多后端捕获：`auto / wgc / mss`
- Mock 检测链路与控制台主循环
- `WorldModel + BotFSM + CombatLogic` 决策链
- 真实输入驱动、窗口前台管理、`F12` 紧急停止
- 经典 `PyQt5` 控制面板（监控/参数/日志），仍定位为实验性辅助界面

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如需 UI、截图与图像处理相关依赖：

```bash
pip install -r requirements-full.txt
```

运行主程序：

```bash
# 控制台模式（当前推荐）
python main.py -c configs/config.yaml

# 经典 UI 模式（实验性）
python main.py --ui -c configs/config.yaml
```

## Git 分支约定

- `main`: 稳定线
- `dev`: 主开发集成线
- `feat/*`: 主题开发分支
- `docs/workbench-v2-refactor`: 已冻结的工作台归档线，不再合并回主线

## 外部资产流程

1. 使用你熟悉的外部录屏工具录制游戏视频流。
2. 原始视频默认保存在仓库外；如果临时放在仓库内，请只使用被忽略的本地目录。
3. 在仓库外完成拆帧、筛选或标注前处理。
4. 按导入规范把筛选后的结果和最小元数据引入训练流程。

详细规则见：

- `docs/自动化主线收敛与外部资产导入/自动化主线收敛与外部资产导入.md`
- `docs/自动化主线收敛与外部资产导入/工作台归档说明.md`

## 核心目录

```text
AradVision/
├── core/       核心基础设施（配置、日志、捕获）
├── vision/     检测接口、Mock 检测器、坐标映射
├── logic/      世界模型、状态机、战斗与路径逻辑
├── input/      Mock/Real 输入驱动与 KillSwitch
├── ui/         经典 PyQt5 控制面板
├── configs/    YAML 配置
├── scripts/    安装、验证与辅助脚本
├── tests/      单元测试与集成测试
└── docs/       设计、规范与阶段文档
```

## 文档索引

- [自动化主线收敛与外部资产导入](docs/自动化主线收敛与外部资产导入/自动化主线收敛与外部资产导入.md)
- [开发计划与里程碑](docs/AradVision开发计划与里程碑.md)
- [项目现状分析与下一步计划](docs/项目现状分析与下一步计划.md)
- [YOLO 训练专项指南](docs/AradVision_YOLO训练专项指南.md)
- [经典 UI 启动指南](docs/UI启动指南.md)

## 安全声明

本项目仅供受控环境下的自动化研究与学习使用。请自行评估风险，并遵守相关平台规则。
