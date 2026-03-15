# AradVision 架构设计文档

## 1. 当前定位

AradVision 当前主线仍然是《歼灭追击战》固定路线 MVP，不是已经完成的“通用全自动 YOLO 平台”，也不是已经接入 LLM 的智能代理系统。

当前已落地的真实主链路是：

```text
CaptureEngine
  -> MainViewReader / MinimapReader / StateReader
  -> GuardLayer / RouteRunController / MaintenanceController
  -> FixedRoutePipeline
  -> InputDriver
```

`main.py` 与 `ui/threads/engine_thread.py` 当前都围绕这条主链路装配和运行。

## 2. 当前实现边界

### `core`

- `config.py`：配置数据结构与加载入口。
- `capture.py`：`Mock / MSS / WGC` 捕获后端与统一工厂。
- `logger.py`、`exceptions.py`、`types.py`：基础设施与共享类型。

### `vision`

- 当前主线优先使用轻量 Reader：
  - `main_view_reader.py`
  - `minimap_reader.py`
  - `state_reader.py`
- `base_detector.py` 与 `mock_detector.py` 保留检测器抽象和兼容入口。
- `coordinate_mapper.py` 保留为坐标映射类辅助能力，不再作为当前主叙事中心。

### `logic`

- `fixed_route_pipeline.py` 是当前默认决策入口。
- `guard_layer.py` 负责 HP/MP、重量、药水等守护判断。
- `route_run_controller.py` 负责副本内固定路线推进。
- `maintenance_controller.py` 负责副本后维护流程。
- `world_model.py` 与 `bot_fsm.py` 仍存在，但当前主循环不再依赖它们做最终决策。

### `input`

- `mock_driver.py` 用于测试与无害验证。
- `input_driver.py` 提供真实输入驱动。
- `kill_switch.py` 与 `system.kill_switch_key` 共同保证紧急停止能力。

### `ui`

- `ui.main_window.MainWindow` 是 `main.py --ui` 的默认控制面板入口。
- `ui.timeline_window.TimelineWorkbenchWindow` 是独立辅助工具，不是当前默认运行主线。
- `ui/threads/`、`ui/widgets/` 提供 UI 支撑层，不参与核心决策。

## 3. 四层目标架构

在不改变当前 MVP 目标的前提下，项目长期架构目标应整理为四层：

```text
平台层
  -> 游戏适配层
      -> 玩法策略层
          -> 决策层
```

### 3.1 平台层

职责：

- 截图采集
- 输入输出
- 窗口管理
- DPI / 坐标映射
- 安全熔断

当前对应模块：

- `core/capture.py`
- `input/*`
- `vision/coordinate_mapper.py`
- `input/kill_switch.py`

这一层的目标是尽量不带具体游戏语义，未来可按平台或运行环境替换。

### 3.2 游戏适配层

职责：

- 读取当前游戏的结构化状态
- 定义当前游戏的对象模型、场景模型和动作模型
- 对接固定 ROI 识别与 YOLO 检测能力

当前对应模块：

- `MainViewReader`
- `MinimapReader`
- `StateReader`
- `BaseDetector / MockDetector`

长期应在这一层补齐但当前尚未正式实现的接口包括：

- `GlobalSceneReader`
- `PerceptionSnapshot`
- `PerceptionAssembler`
- 游戏级对象类型与动作意图模型

### 3.3 玩法策略层

职责：

- 定义“某个玩法如何跑”
- 封装固定路线、副本流程、维护流程和未来通用 YOLO 流程

当前对应模块：

- `FixedRoutePipeline`
- `RouteRunController`
- `MaintenanceController`

长期目标：

- 当前 `FixedRoutePipeline` 保留为已适配副本的固定路线实现
- 后续新增 `GeneralYoloPipeline` 作为未适配副本的通用流程实现
- 通过 `GamePipeline` 和 `DungeonRegistry` 一类抽象统一装配入口

### 3.4 决策层

职责：

- 选择当前高层任务
- 选择当前应使用哪种玩法链路
- 处理异常恢复、暂停、回退和未来 LLM 策略

当前状态：

- 当前仓库仍以规则化流程决策为主
- `LLM Policy` 还没有接入

长期目标：

- 保留规则决策作为默认可回退方案
- 未来将 LLM 接到高层策略位置，而不是低层输入位置

## 4. 双链路与感知原则

项目长期应明确以下原则：

1. 已适配副本走 `ROI + 固定流程`。
2. 未适配副本走 `YOLO + 通用流程`。
3. 静态 UI 元素优先使用固定 ROI / 规则法。
4. 动态空间目标优先使用 YOLO 检测。
5. `LLM` 只读取结构化感知结果、下发高层控制意图，不直接发底层键鼠。

这意味着未来会并存两类玩法实现：

- `FixedRoutePipeline`
- `GeneralYoloPipeline`

但当前默认主链路仍只有前者。

## 5. 当前实现与目标架构的关系

当前实现不是要被推翻，而是要被挂到更高层的正确抽象下面：

- 当前 Reader 资产属于 DNF 的首版游戏适配层实现。
- 当前 `FixedRoutePipeline` 属于玩法策略层中的固定路线实现。
- 当前 `GuardLayer`、捕获和输入能力属于可复用的平台基础能力。
- 当前 ROI、阈值、`room_scripts`、实机分析文档都是现阶段有效资产，不应因长期规划被废弃。

当前仍未正式实现、但需要作为后续演进目标保留的接口包括：

- `GlobalSceneReader`
- `PerceptionSnapshot`
- `PerceptionAssembler`
- `GamePipeline`
- `DungeonRegistry`
- `PolicyEngine`

这些接口当前只能作为目标架构口径，不能写成已经落地的事实。

## 6. 启动模式

### 控制台模式

- 命令：`python3 main.py -c configs/config.yaml`
- 作用：直接运行当前固定路线主链路。

### UI 模式

- 命令：`python3 main.py -c configs/config.yaml --ui`
- 作用：创建 `MainWindow`，通过 `EngineThread` 与核心引擎通信。

### 测试模式

- 默认配置可结合 `mock` 捕获和 `MockInputDriver` 运行。
- 目标是先验证当前主链路稳定性，再切换到真实输入和真实捕获。

## 7. 当前架构约束

- 捕获链路允许平台差异，但接口必须统一落在 `CaptureEngine` 抽象上。
- 固定路线 MVP 是当前唯一默认主决策链路，新增逻辑应优先接入 `FixedRoutePipeline` 或其下游控制器。
- UI 必须是可选层，不能让核心运行依赖 PyQt 才能启动。
- 配置项统一落在 `configs/config.yaml` 与 `core/config.py`，避免把阈值散落在代码中。
- 长期抽象必须以“外扩式重构”为原则，不能为了跨游戏复用而推倒当前 MVP 资产。
- 跨游戏复用的目标应通过新增游戏适配层实现，而不是提前抽空当前 DNF 语义。

## 8. 非主线能力

下列内容仍可保留代码或历史文档，但不再作为当前仓库默认主线：

- 大而全的需求、里程碑、协作分工文档
- 通用 YOLO 训练与数据工作台专题
- 早期阶段性的 UI 方案稿和一次性排障记录

这些内容已迁入 `docs/archive/`，仅用于追溯，不再作为当前实现依据。
