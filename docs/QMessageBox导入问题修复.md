# QMessageBox 导入问题修复

**日期**: 2026-02-11
**版本**: v0.1.3
**问题**: NameError 运行时错误

---

## 问题描述

用户运行 `python .\scripts\verify_ui.py` 时出现以下错误：

```
Traceback (most recent call last):
  File "D:\code\AradVision\ui\main_window.py", line 293, in start_system
    QMessageBox.information(
    ^^^^^^^^^^^
NameError: name 'QMessageBox' is not defined
```

---

## 根本原因

在之前添加启动系统弹窗提示时，在 `start_system()` 方法中使用了 `QMessageBox.information()`，但**忘记在导入列表中添加 `QMessageBox`**。

**错误代码位置**:
```python
# ui/main_window.py 第 15-18 行
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QStatusBar, QMenuBar, QToolBar,
    QPushButton, QAction, QStyle
)  # ❌ 缺少 QMessageBox

# ui/main_window.py 第 293 行
def start_system(self):
    """启动系统"""
    logger.info("启动系统")
    self.status_label.setText("系统运行中...")
    self.system_state_label.setText("状态: RUNNING")

    # 显示提示信息
    QMessageBox.information(  # ❌ QMessageBox 未导入
        self,
        "系统启动",
        "系统已启动！\n\n当前为 UI 框架阶段，核心引擎线程尚未实现。\n实际功能将在 EngineThread 完成后可用。"
    )
```

---

## 修复方案

### 修改文件

`ui/main_window.py`

### 具体改动

在导入列表中添加 `QMessageBox`：

```python
# 修复前
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QStatusBar, QMenuBar, QToolBar,
    QPushButton, QAction, QStyle
)

# 修复后
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QStatusB ar, QMenuBar, QToolBar,
    QPushButton, QAction, QStyle, QMessageBox,  # ← 添加 QMessageBox
)
```

---

## 验证

### 测试步骤

1. 运行 `python .\scripts\verify_ui.py`
2. 检查窗口是否正常打开
3. 点击"启动系统"按钮或按 F5
4. 检查是否弹出提示对话框（不崩溃）

### 预期结果

- ✅ 程序正常启动，无 NameError
- ✅ 点击"启动系统"时弹出提示对话框
- ✅ 对话框显示正确的说明文字

---

## 其他发现的问题

从日志中还发现了一个**待调查的问题**：

### 快速控制按钮重复触发

**日志显示**:
```
23:14:06.473 | INFO | ui.widgets.status_panel:on_start_clicked:232 - 快速控制: 启动系统
23:14:07.301 | INFO | ui.widgets.status_panel:on_start_clicked:232 - 快速控制: 启动系统
23:14:07.767 | INFO | ui.widgets.status_panel:on_start_clicked:232 - 快速控制: 启动系统
23:14:13.738 | INFO | ui.widgets.status_panel:on_start_clicked:232 - 快速控制: 启动系统
```

**分析**:
- 在 0.4 秒内，`on_start_clicked` 被调用了 4 次
- 但 `MainWindow.start_system()` 只被调用了 1 次（23:14:31.721）
- 说明信号连接可能有问题，或者事件被重复触发

**可能原因**:
1. 菜单和工具栏的信号连接冲突
2. 某些操作导致连锁反应
3. StatusPanel 的按钮连接了多次

**状态**: **待进一步调查和修复**

---

## Git 提交

**提交哈希**: `4ef6e18`
**分支**: `dev`
**提交信息**:
```
fix: 添加 QMessageBox 导入

修复运行时 NameError: name 'QMessageBox' is not defined 错误。

在 PyQt5.QtWidgets 导入列表中添加 QMessageBox。

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**推送**: 已推送到 `origin/dev`

---

## 后续工作

### 短期（本次版本）

1. **修复菜单信号重复问题**:
   - 彻底调查 status_panel 按钮重复触发的原因
   - 统一菜单和工具栏的信号连接方式
   - 添加信号连接防抖机制

2. **减少日志噪音**:
   - 为快速控制按钮添加防抖逻辑
   - 避免在短时间内重复触发相同操作

### 长期（v0.2.0+）

1. **完善信号-槽架构**:
   - 使用 Qt 信号系统进行组件间通信
   - 避免直接方法调用导致的耦合

2. **事件处理优化**:
   - 添加事件过滤器
   - 实现更精确的事件响应控制

---

## 参考文档

- [PyQt5 QMessageBox 官方文档](https://doc.qt.io/qt-5/qmessagebox.html)
- 项目 UI 设计文档: `docs/PyQt控制面板UI设计文档.md`
- 项目测试指南: `docs/PyQt5-UI测试指南.md`

---

**文档版本**: v1.0
**最后更新**: 2026-02-11
**状态**: QMessageBox 导入问题已修复，重复触发问题待调查
