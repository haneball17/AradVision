# 任务 3: UI 信号连接计划

**状态**: 待实现
**预计工时**: 3h

---

## 📋 当前状态分析

### main.py 结构
- 纯控制台应用，无 UI 集成
- WorldModel 已被初始化并使用（任务 2 已确认）
- EngineThread 已创建（任务 1 已完成）但未集成

### 需要的修改

1. **导入 EngineThread**
2. **添加 --ui 参数支持**
3. **在 UI 模式下启动 EngineThread**
4. **连接信号到 UI 更新方法**

---

## 🎯 实现方案

### 方案概述

由于 main.py 目前是控制台应用，我们采用轻量级集成方案：

**A. 基础集成**（推荐）- 3h
- 添加 --ui 参数启动 UI
- 在 initialize() 中创建 EngineThread
- 连接信号（使用 lambda 绑定到当前实例方法）
- UI 模式下 EngineThread 独立运行

**B. 完整集成**（后续）- 需要时
- 重构 main.py 为 UI 应用类
- 移动控制台主循环到 EngineThread
- 添加完整的事件处理和生命周期管理

---

## 📝 详细实现步骤

### 步骤 1: 导入 EngineThread

**文件**: main.py

**修改内容**:
```python
# 在文件顶部导入区域
from ui.threads.engine_thread import EngineThread, create_engine_thread
```

---

### 步骤 2: 添加 --ui 参数支持

**文件**: main.py

**修改内容**:
```python
def parse_args():
    # ... 现有参数 ...
    parser.add_argument("--ui", action="store_true", help="启动 UI 控制面板")
    return parser.parse_args()
```

---

### 步骤 3: 在 initialize() 中创建 EngineThread

**文件**: main.py

**修改内容**:
```python
def initialize(self) -> None:
    logger.info("初始化系统模块...")

    # ... 现有代码 ...

    # ========== 新增：UI 集成 ==========
    # 检查是否启用 UI 模式
    if hasattr(self, '_ui_mode') and self._ui_mode:
        logger.info("UI 模式启动，跳过控制台主循环")

        # 创建引擎线程
        self._engine_thread = create_engine_thread(self.config)

        # 连接信号
        self._engine_thread.signals.frame_ready.connect(
            lambda frame: logger.debug(f"收到帧数据: {frame.shape if frame is not None else 'None'}")
        )

        self._engine_thread.signals.status_update.connect(
            lambda status: logger.debug(f"收到状态更新: {status}")
        )

        self._engine_thread.signals.log_message.connect(
            lambda level, msg: logger.log(level, msg)
        )

        self._engine_thread.signals.error_occurred.connect(
            lambda error: logger.error(f"引擎错误: {error}")
        )

        # 标记 UI 模式
        self._ui_mode = True

    # ... 继续其他模块初始化 ...
```

---

### 步骤 4: 修改 run() 方法

**文件**: main.py

**修改内容**:
```python
def run(self) -> None:
    """
    运行主循环

    UI 模式：启动 EngineThread，跳过控制台主循环
    控制台模式：正常运行原有主循环
    """
    if hasattr(self, '_ui_mode') and self._ui_mode:
        logger.info("UI 模式运行，EngineThread 处理主循环")

        # 启动引擎线程
        if self._engine_thread and not self._engine_thread.isRunning():
            logger.info("启动引擎线程...")
            self._engine_thread.start()
    else:
        # 控制台模式：正常运行原有逻辑
        self._main_loop()
```

---

## 🔧 代码片段准备

### 片段 1: 导入语句

```python
# 添加到导入区域（约第 18 行之后）
try:
    from ui.threads.engine_thread import EngineThread, create_engine_thread
    HAS_ENGINE_THREAD = True
except ImportError:
    logger.warning("EngineThread 不可用（缺少 PyQt5），UI 模式将禁用")
        HAS_ENGINE_THREAD = False
```

### 片段 2: 参数解析

```python
def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="AradVision - DNF 视觉辅助自动化系统")

    # 现有参数...

    # UI 参数
    parser.add_argument("--ui", action="store_true", help="启动 UI 控制面板")

    return parser.parse_args()
```

### 片段 3: EngineThread 创建

```python
# 在 initialize() 方法中（约第 260 行）
# 检查是否启用 UI 模式
if hasattr(self, '_ui_mode') and self._ui_mode:
    logger.info("UI 模式启动，创建引擎线程")

    # 创建引擎线程
    self._engine_thread = create_engine_thread(self.config)

    # 连接信号（使用 lambda 避免循环引用）
    self._engine_thread.signals.frame_ready.connect(
        lambda frame: logger.debug(f"帧数据: {frame.shape if frame is not None else 'None'}")
    )

    self._engine_thread.signals.status_update.connect(
        lambda status: logger.debug(f"状态更新: {status}")
    )

    self._engine_thread.signals.log_message.connect(
        lambda level, msg: logger.log(level, msg)
    )

    self._engine_thread.signals.error_occurred.connect(
        lambda error: logger.error(f"引擎错误: {error}")
    )
```

### 片段 4: run() 方法修改

```python
def run(self) -> None:
    """
    运行主循环

    UI 模式：启动 EngineThread，跳过控制台主循环
    控制台模式：正常运行原有主循环
    """
    if hasattr(self, '_ui_mode') and self._ui_mode:
        logger.info("UI 模式运行，EngineThread 处理主循环")

        # 启动引擎线程（如果未启动）
        if self._engine_thread and not self._engine_thread.isRunning():
            logger.info("启动引擎线程...")
            self._engine_thread.start()
    else:
            # 控制台模式：正常运行原有逻辑
            self._main_loop()
```

---

## ⚠️ 注意事项

### 1. 循环引用问题
- 信号连接时使用 lambda 避免 `self` 循环引用
- 信号槽函数中使用局部变量而非实例变量

### 2. 线程安全
- EngineThread 使用 `self._should_stop` 标志优雅退出
- 主线程通过 `engine_thread.stop()` 停止引擎

### 3. 模式检测
- 使用 `hasattr(self, '_ui_mode')` 检测 UI 模式
- 兼容控制台模式运行（无 PyQt5 时）

### 4. 依赖处理
- HAS_ENGINE_THREAD 标志处理 PyQt5 不可用的情况
- UI 模式下才创建 EngineThread

---

## 📊 测试验证

### 测试 1: UI 模式启动

```bash
# 启动 UI（需要 PyQt5）
python main.py --ui
```

**预期结果**:
- ✅ UI 控制面板正常打开
- ✅ EngineThread 独立运行
- ✅ 日志显示引擎初始化信息
- ✅ 信号正常工作（可添加 logger 输出验证）

### 测试 2: 控制台模式

```bash
# 正常运行（无 UI）
python main.py
```

**预期结果**:
- ✅ 正常主循环运行
- ✅ 所有模块正常工作

---

## 📝 文件修改汇总

| 文件 | 新增行 | 修改内容 |
|------|--------|----------|
| main.py | ~30 行 | 导入 EngineThread, 添加 --ui 参数, 创建 EngineThread, 连接信号, 修改 run() 方法 |
| 可选 | - | 其他小修改 |

---

## 🎯 下一步

执行实现后需要：
1. 运行 `python main.py --ui` 测试 UI 模式
2. 确认信号正常工作
3. 提交代码

---

**预计工时**: 3 小时

**是否开始实现？** 请确认。
