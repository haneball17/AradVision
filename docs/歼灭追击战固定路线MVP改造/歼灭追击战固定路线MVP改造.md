# 歼灭追击战固定路线 MVP 改造

## 1. 目标

本专题只服务《歼灭追击战》固定路线 MVP。

当前主线目标：

- 用固定路线状态机替代通用怪物/拾取/寻路主线
- 用主画面状态识别、小地图校验、HP/MP 守护层驱动副本内闭环
- 在回到稳定城镇等待区后切入维护流程的 dry run 检查

本专题不把整屏通用 YOLO 作为当前版本主链路。

## 2. 当前边界

当前版本明确包含：

- `MainViewReader`
- `MinimapReader`
- `StateReader`
- `GuardLayer`
- `RouteRunController`
- `MaintenanceController`
- `FixedRoutePipeline`

当前版本明确不包含：

- 通用副本导航
- 通用整屏 YOLO 决策链路
- 用整屏门检测或通用寻路来决定下一房间出口
- `loot` 主线拾取
- 切角色
- 副本选择界面
- 真实卖店点击

`YOLO 通用方案` 仅保留为后续升级目标。
本专题只在状态分层、Reader 接口、配置结构、房间脚本和维护流程边界上预留扩展余量，不展开其具体实现内容。

## 3. 实现结果

### 3.1 新运行管线

主入口和 UI 引擎线程默认切换为：

```text
Capture
  -> MainViewReader
  -> StateReader
  -> GuardLayer
  -> MinimapReader
  -> RouteRunController
  -> MaintenanceController
  -> InputDriver
```

### 3.2 新状态层

新增状态分层：

- `MainViewState`
- `MinimapPathState`
- `MinimapSpecialState`
- `GuardAction / GuardDecision`
- `MaintenanceState`

`GameContext` 已扩展为可承载：

- 主画面状态
- 小地图状态
- 预期房间索引
- 守护层决策
- 维护流程状态
- 过图耗时
- 背包重量与格子数占位字段

### 3.3 配置结构

`configs/config.yaml` 新增 `dungeon_run` 段，集中承载：

- 主画面 ROI
- 小地图 ROI
- UI ROI
- 守护层阈值
- 职业画像
- 维护流程阈值
- 固定路线房间脚本

当前 `room_scripts` 只提供结构示例，真实《歼灭追击战》路线仍需现场逐房间补齐。

### 3.4 当前找门与房间推进口径

当前已实现事实：

- `RouteRunController` 当前依据 `room_scripts.expected_exit_direction`、`exit_action_template` 与 `MinimapPathState` 触发出门，不做整屏通用找门或完整通用寻路。
- `MinimapReader` 当前负责推进状态校验与异常信号提示，不承担像素级导航职责。
- `door_confirmation_roi` 已在配置结构中预留，但当前尚未形成完整的“门前确认 -> 对准 -> 进门”闭环。

后续实现建议：

- 固定路线仍然决定“去哪边”，视觉只负责局部辅助确认，不反向推翻 `room_scripts`。
- 出门流程后续应细化为三阶段：
  1. 去目标边缘工作区
  2. 在目标边缘工作区局部扫描门
  3. 对准并进门
- 人物位置建议主用 YOLO `hero`，再从检测框推导 `foot_point`，不建议用纯 ROI 识别人物站位。
- 多门房的正确门应先由 `room_idx -> expected_exit_direction` 决定，再在目标方向局部窗口中筛选候选门。
- 出门失败时应优先做房间级纠偏与局部恢复，主线采用“垂直/侧向绕行 -> 反向回退 -> 最后跳跃”的对称规则，而不是一开始就切成全图通用寻路。

### 3.5 当前 YOLO 辅助训练与清房拾取口径

当前已实现事实：

- `FixedRoutePipeline` 当前会把检测结果中的 `hero / items / doors` 放入 `GameContext`，但默认检测器仍以 `MockYoloDetector` 为主，真实 YOLO 还不是现行主链路。
- 当前 `RouteRunController` 还没有“清房后脚底拾取阶段”，现状仍是清房后直接进入出门流程。
- 仓库中已有 [scripts/capture_training_data.py](../../scripts/capture_training_data.py) 和 [scripts/analyze_dataset.py](../../scripts/analyze_dataset.py) 可用于原始素材采集与分布检查，但当前没有正式训练脚本和标准数据集目录。

后续实现建议：

- 当前 YOLO 不应按“通用 DNF 全自动检测器”去训练，而应按固定路线 MVP 的局部辅助感知去训练。
- 训练顺序建议按 `hero -> hero + gate -> hero + gate + item` 分阶段推进：
  1. `hero`：服务人物位置、`foot_point`、卡住判定与边缘工作区判断
  2. `gate`：服务目标方向局部门确认，不负责决定路线方向
  3. `item`：只在清房后、人物脚底局部窗口中辅助判断是否需要按 `X`
- `item` 不应进入战斗中整屏主检测，也不应升级成通用拾取寻路。
- 清房后拾取建议挂在固定路线控制器中，流程为：
  1. 清房确认
  2. 若存在 `hero`，仅在脚底局部窗口检查 `item`
  3. 若检测到 `item`，执行 `pick_up`，即 `X`
  4. 每次按键后复检，最多执行有限次数
  5. 无 `item` 或达到预算后再进入出门流程
- 默认不追求“100% 全捡”，而优先保证主线推进稳定；若后续实机证明误检过高，可退化成“清房后固定补按 `X` 若干次”的无检测方案。

## 4. 后续升级预留

文档允许保留如下升级目标，但当前不实现细节：

- 主画面 YOLO 增强识别
- 副本内 `hero / gate` 局部检测增强
- 固定路线下的 `hero / gate / item` 局部辅助感知训练与接入
- 小地图 small object YOLO 增强识别
- 副本外复杂 UI 的视觉检测增强
- 固定路线下的局部通用恢复

后续升级只应挂接到现有边界：

- `MainViewReader`
- `MinimapReader`
- `StateReader`
- `FixedRoutePipeline`

不应反向把通用化逻辑塞回当前固定路线控制器本体。

## 5. 参考依据

核实日期：2026-03-14

- Ultralytics 文档：<https://docs.ultralytics.com/>
- PyTorch 安装入口：<https://pytorch.org/get-started/locally/>
- CVAT GitHub：<https://github.com/cvat-ai/cvat>
- LabelImg GitHub：<https://github.com/HumanSignal/labelImg>
- DFO World Status：<https://wiki.dfo-world.com/view/Status>
- DFO World Status Effects：<https://wiki.dfo-world.com/view/Status_Effects>
- DFO World Items：<https://wiki.dfo-world.com/view/Items>
- StrategyWiki Gameplay：<https://strategywiki.org/wiki/Dungeon_Fighter_Online/Gameplay>
- StrategyWiki Walkthrough：<https://strategywiki.org/wiki/Dungeon_Fighter_Online/Walkthrough>

## 6. 当前遗留项

- `configs/config.yaml` 中 ROI 和房间脚本仍需结合真实运行分辨率继续复核
- ROI 复核流程改由 `CVAT` 承担，仓库内不再维护专用离线 ROI 标定工具
- 维护流程当前只做 dry run 状态切换和日志输出，不执行真实出售
- 固定路线下的“三阶段找门 + 分层纠偏”仍停留在设计收口阶段，尚未写入当前控制器
- 通用 YOLO 仍保留为后续目标，不在本专题展开

## 7. P0 实机复验与设计资料

- [P0 实机复验资料清单](./P0实机复验资料清单.md)
- [视频分析：jmzjz_abyssroom03](./视频分析_2026-03-14_jmzjz_abyssroom03.md)
- [配置失配诊断：jmzjz_abyssroom03](./配置失配诊断_2026-03-14_jmzjz_abyssroom03.md)
- [补充视频分析：维护流程与 StateReader](./补充视频分析_2026-03-14_维护流程与StateReader.md)
- [固定路线找门与纠偏设计](./固定路线找门与纠偏设计.md)
- [固定路线 YOLO 辅助感知与清房拾取设计](./固定路线YOLO辅助感知与清房拾取设计.md)
