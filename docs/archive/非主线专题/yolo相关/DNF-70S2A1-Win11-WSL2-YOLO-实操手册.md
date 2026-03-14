# DNF 70S2A1《歼灭追击战》固定路线 MVP 手把手实操手册

> 核实日期：2026-03-14
>
> 目标副本：`歼灭追击战`
>
> 当前前提：路线固定、每次都刷全图、最后再进 Boss 房、无随机性
>
> 当前环境：`Windows 11 + WSL2 + RTX 5090 D 32GB + torch 2.12.0.dev20260312+cu128 + ultralytics 8.4.21`
>
> 项目目录：`D:\word\yolo\game-detection\`
>
> WSL 路径：`/mnt/d/word/yolo/game-detection/`

## 本轮会话后的结论

1. 这份文档的主线目标不是“做一个通用 DNF YOLO 检测器”，而是“稳定刷完《歼灭追击战》一整把”。
2. 该副本路线固定，所以主决策器应当是固定路线状态机，不是动态路径规划。
3. 由于掉落直接出现在角色脚下，`loot` 继续降级保留，不进入 MVP 主线。
4. 由于你的职业可以全小地图攻击怪物，首版优先级从“逐怪定位”改成“房间状态判定、过图判定、Boss 房进入时机判定”。
5. 血量/蓝量监控和吃药已经进入主线，它不是后续优化，而是副本内的全局守护层。
6. 背包负重、格子数、自动卖指定稀有度以下物品属于副本外维护流程，放在 `FINISH_RUN` 之后，而不是副本中。
7. “找到下个门”不做成通用寻路，而是做成“固定路线 + 房间级出门脚本 + 过图确认”的闭环。
8. 如果要加小地图，最好的做法仍然是独立 ROI、独立状态编码、接入固定路线状态机做校验。
9. `切角色`、`副本选择场景`、`loot` 都不是删除，而是降级保留到后续版本。

## 参考资料

- DFO World Status: <https://wiki.dfo-world.com/view/Status>
- DFO World Items: <https://wiki.dfo-world.com/view/Items>
- StrategyWiki DFO Gameplay: <https://strategywiki.org/wiki/Dungeon_Fighter_Online/Gameplay>
- StrategyWiki DFO Walkthrough: <https://strategywiki.org/wiki/Dungeon_Fighter_Online/Walkthrough>
- Ultralytics Quickstart: <https://docs.ultralytics.com/quickstart/>
- Ultralytics Track Mode: <https://docs.ultralytics.com/modes/track/>
- Ultralytics SAHI Tiled Inference: <https://docs.ultralytics.com/guides/sahi-tiled-inference/>
- Ultralytics Detect Dataset Format: <https://docs.ultralytics.com/datasets/detect/>
- PyTorch 安装入口: <https://pytorch.org/get-started/locally/>
- FFmpeg 下载页: <https://ffmpeg.org/download.html>
- LabelImg GitHub README: <https://github.com/HumanSignal/labelImg/blob/master/README.rst>
- CVAT GitHub README: <https://github.com/cvat-ai/cvat/blob/develop/README.md>
- Ultralytics negative images 讨论: <https://github.com/ultralytics/ultralytics/issues/5044>
- Ultralytics background / negative images 讨论: <https://github.com/ultralytics/ultralytics/issues/8889>

## 0. MVP 目标与边界

### 目标

这份文档的唯一主目标是：

- 从已经进入《歼灭追击战》副本后的第一房间开始
- 按固定顺序清完所有普通房
- 最后进入 Boss 房
- 稳定完成一次完整通关

### 完成标准

下面 8 条全部满足，才算 MVP 跑通：

1. 系统能识别“当前还在普通房战斗中”
2. 系统能识别“当前房间已清空，可以推进”
3. 系统能识别“正在过图/载入/不可操作”
4. 系统能在最后一个普通房结束后才进入 Boss 房
5. 系统能监控 HP，并在阈值触发时自动吃药
6. 系统能通过固定路线脚本找到当前房间的出口并完成过图
7. 系统能识别“通关结束，停止本次运行”
8. 系统能在通关后进入维护流程检查负重/格子数

### 不在 MVP 内的内容

- 角色切换
- 城镇导航
- 副本选择界面
- 掉落物视觉搜物
- 动态路径规划
- 多副本泛化
- 通用职业泛化
- 小地图主导的通用导航

### 为什么这样定

这不是偷工减料，而是按你这个版本和这个副本的真实条件做技术收缩：

- 地图固定，路径固定，所以先不用做“路线推理”
- 掉落直接出现在脚下，所以先不用做“掉落物检测”
- 可以全小地图攻击，所以先不用追求“逐怪精确框”
- DFO 的 HP/MP、负重和 NPC 交易都是稳定的系统机制，适合作为规则层，不适合作为首版 YOLO 任务  
  来源：<https://wiki.dfo-world.com/view/Status>  
  来源：<https://wiki.dfo-world.com/view/Items>  
  来源：<https://strategywiki.org/wiki/Dungeon_Fighter_Online/Gameplay>

## 1. 实现优先级重排

### P0：必须先做

- 固定路线状态机
- 房间战斗中 / 房间已清空判定
- 过图 / 黑屏 / 载入判定
- Boss 房进入时机判定
- 通关结束判定
- 房间级出门脚本

### P0.5：紧贴主线的全局守护层

- HP 监控
- MP 监控
- 药水使用
- 药水耗尽保护

### P1：建议做，但不阻塞 MVP

- 右上角小地图 ROI 截取
- 小地图房间序号校验
- 小地图清房辅助判据
- 小地图用于异常恢复

### P1.5：副本外维护流程

- 背包负重检查
- 格子数检查
- 自动卖指定稀有度以下的物品
- 修理 / 补药

### P2：可以靠后

- 通用 YOLO 主画面检测
- 小地图专用 YOLO 模型
- `loot` 检测
- `切角色` 负样本
- `副本选择` 场景识别

### 为什么小地图不是 P0

外部资料和当前副本条件放在一起看，结论很清楚：

- StrategyWiki 提到 DFO 的小地图会显示房间布局、方向和 Boss 房信息，这说明它适合做“拓扑校验”  
  来源：<https://strategywiki.org/wiki/Dungeon_Fighter_Online/Mechanics>
- 但你的《歼灭追击战》路线固定、无随机性，所以首版没有必要依赖小地图做实时寻路决策
- 因此，小地图在 MVP 中最合适的角色是“校验器”和“恢复器”，不是主控制器

## 2. 总体实现架构

MVP 推荐架构不是“一个大 YOLO 包打天下”，而是下面这条线：

```text
固定分辨率录屏
↓
全局守护层（HP/MP/药水）
↓
主画面状态判断
↓
固定路线状态机
↓
房间级出门脚本
↓
过图与房间切换
↓
最后进入 Boss 房
↓
通关结束
↓
副本外维护流程（卖店 / 修理 / 补药）
```

如果要加小地图，建议变成：

```text
主画面状态判断
        ↓
固定路线状态机 ← 小地图 ROI 校验模块
        ↓
房间级出门脚本
        ↓
异常恢复 / 房间编号确认
```

### 主画面模块负责什么

- 当前房间是否仍在战斗
- 当前房间是否已清空
- 当前是否过图 / 载入 / 黑屏
- 当前是否进入 Boss 房
- 当前是否已经通关

### 小地图模块负责什么

- 当前房间位置是否与预期一致
- Boss 房是否在预期位置
- 当前是否已经误入或跳过某个房间
- 当前房间是否已经满足推进条件

### 守护层负责什么

- 当前 HP 是否低于阈值
- 当前 MP 是否低于阈值
- 当前是否可以安全使用药水
- 当前药水是否耗尽
- 当前是否需要暂停房间逻辑

### 维护流程负责什么

- 当前负重是否过高
- 当前背包格子是否接近满
- 当前是否已经打开卖店 UI
- 当前是否需要卖掉低于阈值的物品
- 当前是否需要修理或补药

### 为什么不做三块统一检测

不推荐在 MVP 里把窗口硬切成：

- 副本主画面
- 右上角小地图
- 下方 UI

然后三块一起上 YOLO。

原因：

- 主画面和小地图是两种完全不同的视觉任务
- 小地图是典型 small object 场景，更适合独立 ROI 和局部放大
- 下方 UI 更像状态读取，不像目标检测主任务
- HP/MP、负重、卖店、修理这类问题明显更适合固定 ROI + 规则，而不是整屏检测

Ultralytics 官方把 tracking、small object sliced inference 分开讲，CVAT 也把 video / track / interpolation 单独支持，这都说明这类任务不适合在一开始混为一个模型。  
来源：<https://docs.ultralytics.com/modes/track/>  
来源：<https://docs.ultralytics.com/guides/sahi-tiled-inference/>  
来源：<https://github.com/cvat-ai/cvat/blob/develop/README.md>

## 2.5 为未来通用化预留的设计边界

这一节不是要把通用化逻辑拉进当前 MVP，而是把接口层次先固定住。

原则只有一条：

- 当前实现仍然只服务《歼灭追击战》固定路线 MVP
- 未来多副本、多职业、副本外全链路能力，只通过扩展层接入
- 不允许为了未来通用化，把当前主线做重

建议长期固定 5 层状态：

- `main_view_state`
  - 当前最小集：`combat_room / clear_room / transition / boss_room / run_finished`
  - 后续可扩：`town_idle / dungeon_select / vendor_ui_open / character_select`
- `minimap_path_state`
  - 当前只负责清房推进和 Boss-only 特判
  - 后续可扩成房间拓扑和通用导航输入
- `minimap_special_state`
  - 当前已有 `ABYSS_ROOM_PRESENT`
  - 后续新增特殊房间时，只在这一层扩展
- `guard_state`
  - 当前只覆盖 HP/MP/药水
  - 后续可扩药水不足、死亡恢复、异常停机
- `maintenance_state`
  - 当前只覆盖卖店 / 修理 / 补药
  - 后续可扩回城、重新选图、连续刷图闭环

这里要强调两件事：

- 这些层次现在主要用于命名和边界隔离，不代表本轮都要实现
- 后续扩展也不要把新能力反塞回固定路线状态机本体

## 3. 环境与项目现状检查

### 先确认现状

当前目录里已经有一套通用 YOLO 项目结构和一份较早的 DNF 文档：

- [README.md](/mnt/d/word/yolo/game-detection/README.md)
- [DNF70_WORKFLOW.md](/mnt/d/word/yolo/game-detection/DNF70_WORKFLOW.md)

当前目录里的 `classes.txt` / `dataset.yaml` 仍然可以保留，但它们不再是这份 MVP 主线的强依赖。

### 关键事实

1. 当前 `scripts/train.py` 和 `scripts/predict.py` 在 WSL2 下仍然硬编码 `D:/...` 路径，不适合作为当前 MVP 主命令入口。
2. 当前机器已经验证：
   - `nvidia-smi` 正常
   - `torch.cuda.is_available()` 为 `True`
   - `ultralytics` 可用

### 建议先执行

```bash
cd /mnt/d/word/yolo/game-detection
source ~/.venv-yolo/bin/activate

nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
python -c "import torch; print('torch=', torch.__version__); print('cuda=', torch.cuda.is_available()); print('gpu=', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
yolo version
ffmpeg -version
```

### 额外建议目录

为了不污染当前通用 YOLO 数据，你可以新增一套 MVP 目录：

```bash
mkdir -p /mnt/d/word/yolo/game-detection/frames/mvp_main
mkdir -p /mnt/d/word/yolo/game-detection/frames/mvp_minimap
mkdir -p /mnt/d/word/yolo/game-detection/review/mvp
mkdir -p /mnt/d/word/yolo/game-detection/backups/mvp_notes
mkdir -p /mnt/d/word/yolo/game-detection/backups/mvp_logs
```

## 4. 固定路线与房间脚本表

### 这是第一步，不是可选项

因为你的副本路线固定，所以 MVP 的真正核心不是“训练模型学会走路”，而是先把固定路线表和每个房间的出门动作记成可执行规则。

### 推荐做法

先手工跑 3 次《歼灭追击战》，每次都记录：

- `room_idx`
- 房间类型
- 进入后是否立刻可攻击
- 房间清空后通往哪一个方向
- 该房间出门动作是否只需水平移动
- 最后一个普通房后面是否直接是 Boss 房

### 路线表模板

把下面表格复制到你的笔记里，实际填一次：

| room_idx | 类型 | expected_exit_direction | exit_action_template | door_confirmation_roi | transition_timeout_ms | is_last_normal_room | route_policy_tag | room_feature_tag | next_step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | normal | RIGHT | move_right_hold_1200 | right_door_roi | 1800 | false | fixed_full_clear | normal | go_next_normal |
| 02 | normal | RIGHT | move_right_hold_800_then_jump | right_door_roi | 2200 | false | fixed_full_clear | normal | go_next_normal |
| 03 | normal | UP | move_up_platform_then_right | upper_gate_roi | 2500 | false | fixed_full_clear | platform | go_next_normal |
| N | normal | RIGHT | move_right_hold_1500 | boss_gate_roi | 2200 | true | fixed_full_clear | normal | enter_boss |
| BOSS | boss | STOP | none | none | none | false | fixed_full_clear | boss | stop_after_finish |

### 为什么必须手工记

你已经明确说明这个副本“每次都刷全图，路线固定，没有随机性”。  
在这种情况下，最稳的做法不是让视觉模型去推断路线，而是把路线写死，让视觉只负责判断“当前房间状态”和“出门是否成功”。

### 为什么路线表字段现在就要按通用格式保留

虽然当前只跑《歼灭追击战》，但路线表不要收缩成“只够这一张图”的格式。

建议现在就保留两个预留字段：

- `route_policy_tag`
  - 当前默认：`fixed_full_clear`
  - 后续可扩：`rush_boss`、`branch_priority_left_first`
- `room_feature_tag`
  - 当前默认：`normal`
  - 后续可扩：`platform`、`vertical`、`special_room`、`event_room`

这两个字段当前主要用于记录和命名，不要求在 MVP 里驱动额外逻辑。

## 5. MVP 主线：先做房间状态识别，不先做整屏目标检测

### 推荐识别的主状态

MVP 最小主状态集建议是：

- `combat_room`
- `clear_room`
- `transition`
- `boss_room`
- `run_finished`

### 这比 `enemy / boss / loot / gate` 更适合当前副本

原因：

- 你能全小地图攻击，不依赖逐怪精确定位
- 地图路线固定，不需要通用门识别来决定去哪
- 掉落物自动出现在脚下，不需要通过视觉扫地

所以当前最有价值的问题其实是：

- 这一房还没打完吗
- 现在能过图了吗
- 这是 Boss 房了吗
- 这次副本结束了吗

### 推荐的数据采样

录制 5 到 10 次完整《歼灭追击战》视频，重点覆盖：

- 普通房战斗中
- 普通房清空后
- 过图瞬间
- 黑屏或载入帧
- Boss 房刚进入
- Boss 房战斗中
- 通关结算

### 抽帧建议

先用场景变化抽帧，再对过图和 Boss 房补固定帧率：

```bash
cd /mnt/d/word/yolo/game-detection
source ~/.venv-yolo/bin/activate

python scripts/extract_keyframes.py \
  --video /mnt/d/word/yolo/game-detection/videos/raw/jmzjz_run01.mp4 \
  --method scene \
  --threshold 0.18 \
  --output /mnt/d/word/yolo/game-detection/frames/mvp_main
```

```bash
python scripts/extract_keyframes.py \
  --video /mnt/d/word/yolo/game-detection/videos/raw/jmzjz_run01.mp4 \
  --method fps \
  --fps 2 \
  --output /mnt/d/word/yolo/game-detection/frames/mvp_main
```

### 标注建议

这里不要一上来就把所有帧都做 bbox。  
先按状态挑样本，再决定是否需要 YOLO 子任务。

你至少应手工分出下面几组图片：

- `combat_room`
- `clear_room`
- `transition`
- `boss_room`
- `run_finished`

### 这一阶段可不可以先不用 YOLO

可以，而且我建议你先这样做。

原因：

- 固定副本 + 固定分辨率 + 固定 HUD，本来就适合模板匹配、ROI 规则判断、简单分类
- YOLO 更适合在“必须定位小目标或不规则对象”时引入
- 这能让 MVP 更快跑通

## 6. 小地图 ROI、状态编码与固定路线接入

### 结论

最好的做法是：

1. 小地图单独裁成 ROI
2. 单独采样、单独标注、单独训练
3. 输出“房间图状态”，不要直接输出动作
4. 把它接到固定路线状态机后面当校验模块

### 小地图 ROI 截取规范

小地图只从右上角固定 ROI 裁切，不做整屏搜索。

推荐保留两层框：

- `roi_outer`：完整小地图容器与边框，用于人工校准
- `roi_inner`：去掉边框装饰后的实际判定区域，用于算法输入

建议记录成：

```yaml
minimap_roi:
  screen_size: [W, H]
  outer: [x, y, w, h]
  inner: [x, y, w, h]
  resize_scale: 2
```

推荐裁切顺序：

1. 固定游戏分辨率和窗口位置
2. 截 1 张静态全屏图
3. 量出右上角小地图外框
4. 裁出 `roi_outer`
5. 再裁 `roi_inner`
6. 默认把 `roi_inner` 放大 2 倍
7. 只有仍然看不清小图标时再上 SAHI

示例命令，坐标按你的实际分辨率填写：

```bash
ffmpeg -i /mnt/d/word/yolo/game-detection/videos/raw/jmzjz_run01.mp4 \
  -vf "crop=<W>:<H>:<X>:<Y>,fps=2" \
  /mnt/d/word/yolo/game-detection/frames/mvp_minimap/minimap_%06d.jpg
```

### 小地图状态编码规范

在这个副本里，小地图最关键的不是房间图标本身，而是相邻房间状态变化。

这里要先把两层状态拆开：

- `minimap_path_state`
  - 只负责判断“当前房间是否可推进”
- `minimap_special_state`
  - 只负责记录特殊房间信号，例如 `ABYSS_ROOM_PRESENT`

固定编码如下：

- `MINIMAP_NEIGHBOR_DARK`
  - 视觉定义：相邻房间图标持续暗色
  - 业务含义：当前房间未清完
- `MINIMAP_NEIGHBOR_FLASH_QMARK`
  - 视觉定义：相邻未访问房间显示闪烁问号
  - 业务含义：当前房间已清完，可进入下一普通房
- `MINIMAP_BOSS_ONLY_READY`
  - 视觉定义：没有问号房间，但只剩 Boss 房作为相邻可进入目标
  - 业务含义：当前房间已清完，且下一步应准备进入 Boss
- `CLEAR_PENDING`
  - 视觉定义：状态刚变化，尚未过防抖窗口
  - 业务含义：暂不推进，等待稳定确认

固定判据优先级：

1. `FLASH_QMARK`
2. `BOSS_ONLY_READY`
3. 否则 `DARK`

固定防抖规则：

- 任一状态变化必须连续稳定 `300-500ms` 或 `8-15` 帧才确认
- 否则统一记为 `CLEAR_PENDING`

Boss-only 特判固定写法：

```text
if flash_qmark_detected and stable:
    room_clear = true
    next_room_type = normal
elif boss_is_only_adjacent_target and stable:
    room_clear = true
    next_room_type = boss
else:
    room_clear = false
```

### 小地图特殊房间状态：`abyss_room`

这里统一使用 `abyss_room`，不要使用 `elite_room`。

原因：

- DNF 里普通房间也会刷出绿名怪，通常也会被叫“精英怪”
- `elite_room` 很容易和怪物层的 `elite_enemy` 混掉
- 你这里讨论的是房间类型，不是怪物类型

推荐命名固定为：

- 房间层：`abyss_room`
- 怪物层：`elite_enemy`
- Boss 层：`boss_enemy`

在当前版本里，右上角小地图的深渊怪物房间图标有两种视觉变体：

- `abyss_room_icon_large`
- `abyss_room_icon_small`

无论大小，两者都只映射到同一个业务状态：

- `ABYSS_ROOM_PRESENT`

固定写法：

```text
if abyss_room_icon_large_detected or abyss_room_icon_small_detected:
    minimap_special_state = ABYSS_ROOM_PRESENT
else:
    minimap_special_state = NONE
```

实现约束：

- `ABYSS_ROOM_PRESENT` 只是“特殊房间存在”信号
- 它不替代 `MINIMAP_NEIGHBOR_DARK / FLASH_QMARK / BOSS_ONLY_READY`
- 它不单独触发推进到下一房
- 它不改变《歼灭追击战》的固定路线顺序

当前样本策略：

- 本地现有样本只覆盖 `abyss_room_icon_large`
- `abyss_room_icon_small` 先预留接口，不阻塞 MVP
- 在未补齐小图标样本前，允许只启用 `large` 模板
- 后续补到 `small` 样本后，继续映射到 `ABYSS_ROOM_PRESENT`，不新增业务分支

### 小地图如何接入固定路线状态机

小地图不直接驱动动作，只给固定路线状态机提供校验输入。

固定输入表：

- `main_view_state`
- `minimap_path_state`
- `minimap_special_state`
- `expected_room_index`

推荐接入顺序：

1. 先由主画面判断是不是 `transition / run_finished / boss_room`
2. 若当前在普通房，才读取 `minimap_path_state`
3. 若 `minimap_special_state == ABYSS_ROOM_PRESENT`，只做记录和校验，不改变路线分支
4. 若 `minimap_path_state == MINIMAP_NEIGHBOR_FLASH_QMARK`，允许转入下一普通房
5. 若 `minimap_path_state == MINIMAP_BOSS_ONLY_READY` 且 `expected_room_index` 已到最后普通房，允许转入 Boss
6. 若 `expected_room_index` 未到最后普通房却出现 `BOSS_ONLY_READY`，记为异常，进入房间索引校验失败分支

推荐伪代码：

```text
if main_view_state == run_finished:
    FINISH_RUN
elif main_view_state == transition:
    WAIT_TRANSITION
elif current_room_is_last_normal_room and minimap_path_state == MINIMAP_BOSS_ONLY_READY:
    ENTER_BOSS_LAST
elif minimap_path_state == MINIMAP_NEIGHBOR_FLASH_QMARK:
    ADVANCE_TO_NEXT_FIXED_ROOM
else:
    CLEAR_CURRENT_ROOM
```

补充说明：

- `minimap_special_state == ABYSS_ROOM_PRESENT` 时，继续按固定路线执行
- 它可以写入日志、样本统计或异常恢复，但不能替代清房主判据
- 即使暂时没识别出 `ABYSS_ROOM_PRESENT`，只要 `minimap_path_state` 正常，主流程仍可继续

### 为什么 `minimap_special_state` 要单独保留

这是当前手册里最重要的通用化预留位之一。

当前：

- `minimap_path_state` 只服务“能不能推进”
- `minimap_special_state` 只服务“当前是否出现特殊房间信号”

后续如果要加更多特殊房间，也应该继续放在这一层，例如：

- `TREASURE_ROOM_PRESENT`
- `EVENT_ROOM_PRESENT`
- 其他自定义特殊房间标记

不要把这些特殊状态混进 `minimap_path_state`，否则后面一扩副本就会把清房主判据搅乱。

### 标注工具建议

- 主画面静态样本：`LabelImg`
- 小地图连续视频帧：`CVAT` 更合适

原因：

- LabelImg 本质是图像级 bbox 工具，适合轻量修正  
  来源：<https://github.com/HumanSignal/labelImg/blob/master/README.rst>
- CVAT 原生支持 video / track / interpolation，更适合小地图这种视频连续标注  
  来源：<https://github.com/cvat-ai/cvat/blob/develop/README.md>

如果只是补 `abyss_room_icon_large / small` 这类小地图固定图标，首版优先顺序建议是：

1. 固定 ROI
2. 模板匹配 / 规则识别
3. 样本足够后再考虑小地图专用 YOLO

### 小地图 YOLO 增强版最小类集

如果后面确实要做小地图专用 YOLO，建议从最小类集开始：

```text
player_marker
boss_marker
reachable_room
```

不要一开始就去标：

- 所有门方向
- 所有房间边框
- 所有图标细节

## 7. 血量与药水守护层

### 为什么它必须进主线

DFO World 的 `Status` 页面明确说明：

- `HP` 是生命值，归零会死亡
- `MP` 是技能资源
- 角色有固定快捷栏与状态栏逻辑

来源：<https://wiki.dfo-world.com/view/Status>

所以血量/蓝量监控不是优化项，而是副本内随时可能打断当前动作的全局守护层。

### 守护层输入

- `hp_ratio`
- `mp_ratio`
- `is_transition`
- `potion_cd_ready`
- `potion_stock_available`
- `class_requires_mp`

### 守护层输出

- `use_hp_potion`
- `use_mp_potion`
- `pause_room_logic`
- `abort_run`

### 默认阈值

- `hp_critical_threshold = 0.25`
- `hp_low_threshold = 0.45`
- `mp_low_threshold = 0.20`

### 推荐规则

```text
if hp_ratio < hp_critical_threshold:
    pause_room_logic
    use_hp_potion
elif hp_ratio < hp_low_threshold and potion_cd_ready and not is_transition:
    use_hp_potion

if class_requires_mp and mp_ratio < mp_low_threshold and potion_cd_ready and not is_transition:
    use_mp_potion

if hp_ratio < hp_critical_threshold and potion_stock_available == false:
    abort_run
```

### 为什么不用 YOLO

这里不建议上 YOLO。  
最稳的方式是：

- 固定 ROI 读取血条/蓝条
- 算颜色百分比或做简单数值/OCR
- 再触发固定快捷键

### 必须写入文档的边界条件

- 过图/黑屏时不触发吃药
- 连续吃药必须有冷却防抖
- 药水耗尽时要停机或回城，不允许死磕

### 为未来多职业保留的接口

当前守护层规则仍然直接按你现在的职业特性来写，但文档里要先留一个接口名：

- `class_profile`

它的职责是：

- 描述当前职业是否依赖 MP
- 描述技能循环偏好
- 描述是否依赖追怪或近身
- 描述 HP/MP 阈值是否需要特殊调整

当前 MVP 默认可以记成：

```text
class_profile = map_wide_attack_current_class
```

这只是命名预留，不要求本轮就把职业策略层单独实现出来。

## 8. 固定路线下如何找到下个门

### 先改口径：这不是通用寻路

对《歼灭追击战》来说，这一步不应该写成“pathfinding”，而应该写成：

**固定路线下的定向出门**

### 为什么

- 你的副本路线固定
- 你已经知道下一个房间方向
- StrategyWiki 提到房间清空后门会亮，Boss 门还会有不同颜色闪烁  
  来源：<https://strategywiki.org/wiki/Dungeon_Fighter_Online/Walkthrough>

所以最稳的方法不是“全图找门”，而是“按房间脚本前往预期出口，再确认过图成功”。

### 推荐流程

```text
CLEAR_CURRENT_ROOM
  ↓
LOOKUP_EXPECTED_EXIT(room_idx)
  ↓
SEEK_EXPECTED_DOOR(direction)
  ↓
EXECUTE_EXIT_ACTION_TEMPLATE
  ↓
WAIT_TRANSITION
  ↓
CONFIRM_NEXT_ROOM_INDEX
```

### 三层实现结构

第一层，查表：

- 从固定路线表读出 `expected_exit_direction`
- 读出该房间的 `exit_action_template`

第二层，门确认：

- 只检查预期方向的门 ROI
- 不做整屏搜门
- 只确认它是否已经点亮 / 可进入

第三层，过图确认：

- 主画面进入黑屏 / 载入
- 或小地图房间索引变化
- 或主状态进入 `transition`

只要任一成立，就算成功进房。

### 出门脚本模板建议

```text
move_right_hold_1200
move_right_hold_800_then_jump
move_left_hold_1000
move_up_platform_then_right
move_down_drop_then_left
```

### 平台房 / 垂直房间的处理

如果某房间不是简单的左右移动，就不要偷懒复用通用方向动作。  
直接把该房间单独记录成房间脚本。

### 超时与恢复

推荐给每个房间一个 `transition_timeout_ms`：

- 超时后仍未过图：重新读取门 ROI
- 再失败：重新采样小地图状态
- 仍失败：记录日志并停机，不要无限乱跑

## 9. 副本结束后的维护流程：负重、格子数与自动卖店

### 为什么放在这里

DFO World 的 `Status` 页面明确有 `Max Inventory Weight`。  
DFO World 的 `Items` 页面说明稀有度可以通过名称和边框颜色区分。  
StrategyWiki 的 `Gameplay` 页面明确 NPC 可以买玩家的东西。

来源：

- <https://wiki.dfo-world.com/view/Status>
- <https://wiki.dfo-world.com/view/Items>
- <https://strategywiki.org/wiki/Dungeon_Fighter_Online/Gameplay>

所以这部分天然属于副本外的维护流程，不属于副本内逻辑。

### 推荐触发时机

下列任一满足时进入维护流程：

- 当前副本已结束
- `inventory_weight_ratio > 0.85`
- `free_slots < 8`
- 药水库存低于最低保有量

### 维护状态机

```text
FINISH_RUN
  ↓
GO_SAFE_SERVICE_AREA
  ↓
OPEN_INVENTORY
  ↓
CHECK_WEIGHT_AND_SLOTS
  ↓
OPEN_VENDOR
  ↓
SELL_LOW_RARITY_ITEMS
  ↓
REPAIR_AND_RESTOCK
  ↓
READY_NEXT_RUN
```

### 默认卖店策略

默认阈值建议：

- `sell_rarity_threshold = Rare 以下`

实际等价于：

- 默认只卖 `Common / Uncommon`
- `Rare` 及以上默认保留

### 卖店安全规则

第一版固定规则：

- 只在 `vendor_ui_open == true` 时允许卖
- 只卖低于阈值的物品
- 不卖：
  - 已装备物品
  - 任务物品
  - 白名单保留物品
  - 不确定稀有度的物品

### 默认必须开启 dry run

这一步有真实销毁风险，所以文档里固定默认值：

```text
sell_dry_run = true
```

第一版先做：

- 扫描
- 记录
- 高亮候选项

确认无误后再打开真实出售。

### 推荐实现方式

这里也不建议一开始上 YOLO。

更稳的方式是：

- 背包和卖店 UI 固定 ROI
- 稀有度颜色/边框颜色判定
- 必要时用 OCR 读名字或稀有度文字
- 先做日志模式，再做自动点击

### 为未来连续刷图预留的接口

当前维护流程只覆盖“一次通关后的维护”，但文档里建议先预留：

- `loop_controller_state`

它后续会负责：

- 回城
- 重新补给
- 重新选图
- 再次进图

当前 MVP 不要求实现这些动作，只需要明确它们不属于固定路线状态机本体。

## 10. 什么时候才上 YOLO 训练

### MVP 阶段

MVP 阶段不要把 YOLO 训练当成默认第一步。

更合理的顺序是：

1. 固定路线表
2. 主画面状态识别
3. 小地图校验
4. 血量与药水守护层
5. 出门脚本
6. 副本外维护流程
7. 再看哪里必须用 YOLO

### 哪些情况值得上 YOLO

下面这些场景，YOLO 才有明显价值：

- 你发现 `boss_room` 和 `combat_room` 很难靠规则区分
- 你需要稳定识别小地图上的小符号
- 你准备把卖店环节做成复杂 UI 检测
- 你准备从固定副本扩展到更多副本

### 如果真的要训练 YOLO

建议新建独立数据集，不要覆盖根目录当前通用配置：

- `dataset/mvp_room_state/`
- `dataset/mvp_minimap/`

并且不要直接复用当前根目录的 11 类 DNF 配置。

### 可选的最小 YOLO 训练命令

仅当你已经准备好独立数据集后，再用类似命令：

```bash
source ~/.venv-yolo/bin/activate

yolo detect train \
  data=/mnt/d/word/yolo/game-detection/dataset/mvp_minimap.yaml \
  model=yolo11n.pt \
  epochs=60 \
  imgsz=640 \
  batch=16 \
  device=0 \
  workers=1 \
  project=/mnt/d/word/yolo/game-detection/training/runs \
  name=jmzjz_minimap_v1 \
  exist_ok=True
```

### 为什么不直接用当前 `scripts/train.py`

因为它在 WSL2 下仍然是 `D:/...` 硬编码路径，当前不适合直接照搬。

## 11. 降级但保留的后续版本项

这三项不是删除，而是明确降级。

### 1. `loot`

当前处理：

- 从 MVP 主线移出
- 不再作为首版视觉检测目标

保留原因：

- 如果以后更换职业
- 如果以后掉落机制不同
- 如果以后要做更通用的副本脚本

那 `loot` 仍然可能回到检测链路里。

### 2. `切角色`

当前处理：

- 从“负样本必备”降级为“全链路版本再加”

保留原因：

- Ultralytics 社区关于 negative images 的讨论表明，副本外背景帧确实可以降低误检  
  来源：<https://github.com/ultralytics/ultralytics/issues/5044>  
  来源：<https://github.com/ultralytics/ultralytics/issues/8889>
- 但对当前“已进入副本后的固定路线 MVP”并不是刚需

### 3. `副本选择场景`

当前处理：

- 从 MVP 中移出
- 不作为首版数据采集范围

保留原因：

- 如果未来你的系统起点要前移到城镇、频道或副本选择界面
- 那这部分会变成独立的场景识别 / UI 状态模块

### 其他靠后的升级项

- 动态路径规划
- 多副本支持
- 多职业适配
- 小地图主导式导航
- 通用整屏 YOLO 检测器

## 11.5 大后期通用化升级路线图

这一节不是当前实现清单，只是把以后应该接在哪一层写清楚。

### 1. 多副本支持

- 接入位置：`route_policy_tag + room_feature_tag + minimap_path_state`
- 目标：从单副本固定路线扩成多副本可配置路线

### 2. 多职业策略层

- 接入位置：`class_profile`
- 目标：把你当前职业的特例从主状态机里抽出去

### 3. 副本外全链路场景识别

- 接入位置：`main_view_state + maintenance_state + loop_controller_state`
- 目标：覆盖城镇、卖店、修理、选图、再次进图

### 4. 小地图拓扑与通用导航

- 接入位置：`minimap_path_state + minimap_special_state`
- 目标：从当前“校验器”升级到“房间拓扑读取器”

## 12. 推荐的单日落地顺序

| 时间段 | 做什么 | 结果 |
| --- | --- | --- |
| 09:00-09:30 | 检查环境和目录 | GPU、WSL、FFmpeg、YOLO 全通 |
| 09:30-10:30 | 手工跑 3 次《歼灭追击战》并记固定路线表和房间脚本 | 拿到 `room_idx + exit_action_template` |
| 10:30-12:00 | OBS 录制 5 次完整副本视频 | `videos/raw` 有足够样本 |
| 13:30-14:30 | 抽主画面状态帧 | `frames/mvp_main` 就位 |
| 14:30-15:30 | 手工整理 `combat/clear/transition/boss/finish` | 状态样本就位 |
| 15:30-16:00 | 校准小地图 ROI | `mvp_minimap` 输入范围稳定 |
| 16:00-17:00 | 写清房间清房判据和 Boss-only 特判 | 小地图状态编码稳定 |
| 17:00-18:00 | 加入 HP/MP 守护层规则 | 房间逻辑可被安全打断 |
| 18:00-19:00 | 为每个房间补出门脚本 | `expected_exit_direction + exit_action_template` 就位 |
| 19:00-20:00 | 设计维护流程 | 卖店 / 修理 / 补药顺序确定 |

## 13. 常见问题

### 1. 为什么这版文档不再以 `enemy / boss / loot / gate` 为中心

因为《歼灭追击战》当前的真实约束已经变了：

- 路线固定
- 全图必刷
- 掉落不用搜
- 职业能全图打怪

这时继续把主问题定义成“通用目标检测”并不经济。

### 2. 为什么没有直接要求做小地图路径规划

因为这个副本没有随机性。  
固定路线副本里，路径规划不是首版瓶颈，房间状态判断和出门脚本才是。

### 3. 为什么吃药必须进主线

因为 HP/MP 是稳定系统状态，而且死亡会直接打断一整把副本。  
这不是优化项，而是副本内的守护层。

### 4. 为什么卖垃圾不放在副本中

因为负重/格子数问题确实存在，但卖东西需要安全场景、稳定 UI 和 NPC 交易界面。  
把它放进副本中只会打断主状态机。

### 5. “找下个门”为什么不做通用寻路

因为你已经知道路线和方向。  
这时候做通用寻路是过度设计，做“房间级出门脚本”更稳。

### 6. 什么时候应该考虑 CVAT

当你出现下面任一情况：

- 小地图视频帧很多
- 需要连续跟踪房间图标
- 需要多人协作
- 想减少重复人工框选

当前 MVP 仍然可以先用简单方式跑通，不必一开始上重平台。

### 7. 为什么这里用 `abyss_room` 而不是 `elite_room`

因为 `elite_room` 在 DNF 语境里很容易和绿名怪混淆。  
这份手册里统一约定：

- `abyss_room` 表示深渊怪物房间
- `elite_enemy` 表示普通房里的绿名怪
- `boss_enemy` 表示 Boss

这样后面无论是写状态机、样本目录还是日志字段，都不会把“房间类型”和“怪物类型”混成一层。

### 8. 当前项目里哪些现有内容要小心不要混用

- 根目录当前 `classes.txt`
- 根目录当前 `dataset.yaml`
- 旧版 [DNF70_WORKFLOW.md](/mnt/d/word/yolo/game-detection/DNF70_WORKFLOW.md) 里的通用怪物/掉落/小地图混合思路

这三者都不是这份《歼灭追击战》固定路线 MVP 的默认主线。

### 9. 为什么现在要预留通用化接口，但不把通用化逻辑写进主线

因为当前目标仍然是先跑通固定路线 MVP。  
如果现在就把多副本、多职业、城镇导航全塞进主线，交付速度会明显下降。

但如果现在不先把状态层、路线表字段和扩展位命名统一，后面一旦做通用化，就会反过来推翻这份手册的结构。

所以当前最佳做法是：

- 正文继续只写固定路线 MVP
- 通用化只预留接口和扩展位置
- 等 MVP 稳定后，再按章节逐层外扩

## 结尾提醒

这份手册现在的核心思想是：

- 先把《歼灭追击战》当成固定流程问题
- 再把视觉缩成状态判定问题
- 把 HP/MP 守护层提前到主线
- 把出门动作写成房间脚本，而不是通用寻路
- 把卖店放到副本结束后的维护流程
- 小地图先做校验，不先做主控制
- 现在就把状态层和接口边界固定好，但不提前实现通用化逻辑
- `loot / 切角色 / 副本选择` 全部降级保留，不删除

这会比“先做一个通用 DNF YOLO 检测器”更快跑通你当前真正要的 MVP。
