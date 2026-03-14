# PyQt5 UI 测试指南

## 1. 目标

本指南只覆盖当前仍在维护的 UI 验证路径：

- `MainWindow` 控制面板是否可启动
- 基本交互是否可用
- `main.py --ui` 与核心引擎的联通是否正常

## 2. 前置条件

```bash
pip install -r requirements.txt
pip install PyQt5
```

## 3. 冒烟测试

```bash
python3 scripts/test_pyqt_ui.py
```

检查点：

- 窗口能正常打开
- 标签页切换无异常
- 日志面板、状态面板、参数面板能够正常渲染
- 关闭窗口时没有明显异常栈

## 4. 主程序 UI 联调

```bash
python3 main.py -c configs/config.yaml --ui
```

建议先使用 Mock 配置联调，再切换真实环境。重点观察：

- 主窗口是否成功显示
- 引擎线程是否能启动
- 日志面板是否持续收到输出
- 关闭窗口后线程是否能正常退出

## 5. 可选验证

如果需要验证辅助工作台：

```bash
python3 scripts/test_timeline_ui.py
```

该入口不属于默认主线，失败时应单独排查，不要把问题归因到固定路线主程序。
