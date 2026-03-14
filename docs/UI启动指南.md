# UI 启动指南

## 1. 入口说明

AradVision 当前存在两个 PyQt 入口：

- 主入口：`ui.main_window.MainWindow`
  - 用途：控制面板，配合 `main.py --ui` 运行主程序。
- 辅助入口：`ui.timeline_window.TimelineWorkbenchWindow`
  - 用途：时间线工作台，作为独立工具使用，不是默认主线。

## 2. 安装依赖

```bash
pip install -r requirements.txt
pip install PyQt5
```

## 3. 启动方式

### 主程序 UI 模式

```bash
python3 main.py -c configs/config.yaml --ui
```

### 控制面板冒烟脚本

```bash
python3 scripts/test_pyqt_ui.py
```

### 时间线工作台

```bash
python3 scripts/test_timeline_ui.py
```

## 4. 使用建议

- 需要联通主程序、引擎线程和日志面板时，用 `main.py --ui`。
- 只做 PyQt 组件加载与基础交互验证时，用 `scripts/test_pyqt_ui.py`。
- 处理采集/筛选/预标注类辅助流程时，再单独打开时间线工作台。

## 5. 常见问题

### 无法导入 PyQt5

```bash
pip install PyQt5
```

### UI 能启动，但主流程没有动作

- 检查配置文件中的 `capture.use_mock`、`input.type`、`dungeon_run.enabled`。
- 如果只是做界面验证，优先使用 Mock 配置，避免把问题混入真实环境。

### 时间线工作台和主程序 UI 不一致

这是预期行为。两者服务的目标不同，当前仓库默认主线仍是控制面板加固定路线 MVP。
