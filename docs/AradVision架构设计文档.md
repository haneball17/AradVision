# AradVision 架构设计文档

## 1. 当前定位

AradVision 当前主线不是“通用全自动 YOLO 平台”，而是围绕《歼灭追击战》固定路线 MVP 构建的一条可测试、可扩展、可降级的运行链路：

```text
CaptureEngine
  -> MainViewReader / MinimapReader / StateReader
  -> GuardLayer / RouteRunController / MaintenanceController
  -> FixedRoutePipeline
  -> InputDriver
```

`main.py` 负责装配上述链路，并根据参数决定是否启用 UI。

## 2. 模块边界

### `core`

- `config.py`：配置数据结构与加载入口。
- `capture.py`：`Mock / MSS / WGC` 捕获后端与统一工厂。
- `logger.py`、`exceptions.py`、`types.py`：基础设施与通用类型。

### `vision`

- 当前主线优先使用轻量 Reader：
  - `main_view_reader.py`
  - `minimap_reader.py`
  - `state_reader.py`
- `base_detector.py` 与 `mock_detector.py` 保留检测器抽象和兼容入口。
- `coordinate_mapper.py` 仍用于坐标映射类能力，但不再作为 README 层面的主叙事中心。

### `logic`

- `fixed_route_pipeline.py` 是当前主决策入口。
- `guard_layer.py` 负责 HP/MP、重量、药水等守护判断。
- `route_run_controller.py` 负责副本内固定路线推进。
- `maintenance_controller.py` 负责副本后维护流程。
- `world_model.py` 与 `bot_fsm.py` 仍存在，但当前主循环不再依赖它们做最终决策，主要用于兼容旧链路和 UI 观察面。

### `input`

- `mock_driver.py` 用于测试与无害验证。
- `input_driver.py` 提供真实输入驱动。
- `kill_switch.py` 与 `system.kill_switch_key` 共同保证紧急停止能力。

### `ui`

- `ui.main_window.MainWindow` 是 `main.py --ui` 的默认控制面板入口。
- `ui.timeline_window.TimelineWorkbenchWindow` 是独立辅助工具，不是当前默认运行主线。
- `ui/threads/`、`ui/widgets/` 提供 UI 支撑层，不参与核心决策。

## 3. 启动模式

### 控制台模式

- 命令：`python3 main.py -c configs/config.yaml`
- 作用：直接运行固定路线主链路。

### UI 模式

- 命令：`python3 main.py -c configs/config.yaml --ui`
- 作用：创建 `MainWindow`，通过 `EngineThread` 与核心引擎通信。

### 测试模式

- 默认配置可结合 `mock` 捕获和 `MockInputDriver` 运行。
- 目标是先验证链路稳定性，再切换到真实输入和真实捕获。

## 4. 当前架构约束

- 捕获链路允许平台差异，但接口必须统一落在 `CaptureEngine` 抽象上。
- 固定路线 MVP 是当前主决策链路，新增逻辑应优先接入 `FixedRoutePipeline` 或其下游控制器，而不是回退到旧的通用状态机叙事。
- UI 必须是可选层，不能让核心运行依赖 PyQt 才能启动。
- 配置项统一落在 `configs/config.yaml` 与 `core/config.py`，避免把阈值散落在代码中。

## 5. 非主线能力

下列内容仍可保留代码或历史文档，但不再作为当前仓库默认主线：

- 大而全的需求、里程碑、协作分工文档
- 通用 YOLO 训练与数据工作台专题
- 早期阶段性的 UI 方案稿和一次性排障记录

这些内容已迁入 `docs/archive/`，仅用于追溯，不再作为当前实现依据。
