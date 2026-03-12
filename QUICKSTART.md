# AradVision 快速启动指南

本指南只覆盖当前主线：自动化运行链路与外部资产导入规范。

## 1. 环境准备

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果需要经典 `PyQt5` 控制面板、截图或图像处理依赖：

```bash
pip install -r requirements-full.txt
```

## 2. 启动方式

推荐先跑控制台模式：

```bash
python main.py -c configs/config.yaml
```

经典 UI 仅作为监控/调试辅助界面：

```bash
python main.py --ui -c configs/config.yaml
```

## 3. Git 工作流

当前分支约定：

```text
main  -> 稳定线
dev   -> 集成线
feat/* -> 主题开发分支
docs/workbench-v2-refactor -> 已冻结的工作台归档线
```

日常开发流程：

```bash
git checkout dev
git pull origin dev
git checkout -b feat/<topic>
```

完成后回并 `dev`，稳定后再从 `dev` 合入 `main`。不要再把工作台分支合并回主线。

## 4. 外部资产获取方式

当前不再维护仓库内训练数据工作台，推荐流程如下：

1. 用外部录屏工具采集游戏视频流。
2. 原始视频保存在仓库外；如果临时放进仓库，只能放到被忽略的本地目录。
3. 在仓库外完成抽帧、粗筛或人工筛选。
4. 按导入规范把筛选后的结果和最小元数据带入训练流程。

详细规则见：

- `docs/自动化主线收敛与外部资产导入/自动化主线收敛与外部资产导入.md`
- `docs/AradVision_YOLO训练专项指南.md`

## 5. 当前不再使用的路径

以下内容不属于当前主线：

- 时间线工作台
- 仓库内采集/筛选/预标注桌面流程
- `scripts/test_timeline_ui.py`

如需查看历史实现，请切到归档分支 `docs/workbench-v2-refactor` 或参考归档标签 `archive/workbench-v2-freeze-2026-03`。
