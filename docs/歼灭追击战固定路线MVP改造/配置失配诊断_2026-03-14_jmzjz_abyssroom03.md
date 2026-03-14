# 配置失配诊断：jmzjz_abyssroom03

- 诊断日期：2026-03-14
- 输入素材：`assets/video/jmzjz_abyssroom03_frames/` 中的 25 张第二轮截图
- 诊断基线：当前仓库 `configs/config.yaml`
- 目标：判断当前配置问题主要来自 `ROI` 偏移、阈值不匹配，还是素材不足

## 1. 诊断结论

当前问题的主因不是单一阈值，而是 **ROI 与真实 HUD/状态信号明显失配**。

这意味着：

1. 现在不应先调 `MainViewReader` 和 `MinimapReader` 的阈值。
2. 应先修正 `main_view`、`minimap`、`ui_rois` 的位置。
3. `StateReader` 中的部分字段在当前正常战斗 HUD 下根本没有可读信号，不能强行做成“伪精确读取”。

补充说明：

后续补充视频已经提供了背包/药水与商店/维修界面的正样本，
其中 `inventory_weight_bar`、`vendor_ui_open` 和维护流程约束见
[补充视频分析：维护流程与 StateReader](./补充视频分析_2026-03-14_维护流程与StateReader.md)。

## 2. 当前 Reader 诊断结果

基于当前配置运行 25 张截图，观测到：

1. `MainViewReader`
   - 大多数帧被判为 `combat_room`
   - `00:12`、`00:15` 的加载画面没有被识别成 `transition`
   - `05:00`、`05:05` 的结算画面没有被识别成 `run_finished`
   - 仅 `02:45 - 03:30` 一段被判成 `clear_room`

2. `MinimapReader`
   - 全部帧都输出 `MINIMAP_NEIGHBOR_DARK`
   - `special_state` 全部为 `NONE`
   - 说明当前 `neighbor_roi / special_roi` 没有截中真正有效的小地图内容

3. `StateReader`
   - 多数战斗帧的 `hp/mp/weight` 数值几乎固定
   - `inventory_weight_ratio` 常年接近 `0.85`
   - `vendor_ui_open` 始终为 `False`
   - 说明 `ui_rois` 中多个 ROI 目前不对应真实目标语义

## 3. 关键 ROI 问题

### 3.1 `main_view`

1. `transition_roi`
   - 当前截到的是角色中部战斗区域
   - 对加载/黑屏并不稳定

2. `clear_roi`
   - 当前截到的是背景竹林区域
   - 没有稳定覆盖“清房提示文字”或明显的清房视觉信号

3. `boss_roi`
   - 当前覆盖到了 top-right 任务标题栏附近
   - 位置可能部分有效，但现阶段证据不足

4. `finish_roi`
   - 当前落在右下技能栏/地面区域
   - 完全没有覆盖 `05:00` 结算界面的主文字和评级信号

### 3.2 `minimap`

1. 当前视频里，小地图真实位置在 top-right 的大棕色“地图”面板内。
2. 当前 `neighbor_roi` 主要截到了地图标题条和面板上沿。
3. 当前 `special_roi` 也没有落在稳定的特殊状态信号上。

结论：

`MinimapReader` 当前几乎等于在看错区域，因此现阶段任何小地图阈值结论都不可信。

### 3.3 `ui_rois`

1. `hp_bar / mp_bar`
   - 现在的 ROI 没有稳定落在真实血蓝填充条上
   - 导致读数在多数帧里异常稳定，缺少真实变化

2. `inventory_weight_bar`
   - 当前落点不对应实际重量条
   - 更关键的是，正常战斗 HUD 下并未看到明显的重量条显示

3. `vendor_flag`
   - 当前截到的是任务/说明文字区域，不是商店界面信号

4. `potion_flag`
   - 当前截到的是左下地面/界面边缘，不是药水状态图标

## 4. 对 P0 的直接影响

### 4.1 现在可以继续推进的

1. 基于第二轮截图继续拆房间时间轴
2. 先复核 `main_view` 和 `minimap` 的 ROI 位置
3. 先把 `run_finished / transition / combat` 三类状态做实

### 4.2 现在不能直接下结论的

1. `free_slots`
2. `inventory_weight_ratio`
3. `vendor_ui_open`
4. `potion_cd_ready` 的真实阈值

原因不是代码没写，而是 **当前素材没有提供足够稳定的真实视觉信号**。

## 5. 下一批最需要补的素材

为了继续推进 P0，下一批素材应优先补这几类：

1. `transition` 边界帧
   - 建议围绕 `00:12 - 00:17` 多截前后各 2 帧
   - 时间点清单：`docs/歼灭追击战固定路线MVP改造/jmzjz_abyssroom03_补充截图_transition.txt`

2. `clear_room / boss_room` 边界帧
   - 建议围绕 `04:42 - 04:58` 再补 6 到 10 张
   - 时间点清单：`docs/歼灭追击战固定路线MVP改造/jmzjz_abyssroom03_补充截图_endgame.txt`

3. 背包或重量相关界面
   - 如果后续要做 `inventory_weight_ratio / free_slots`，需要提供“打开背包后的截图或视频”

4. 药水不可用或冷却中样本
   - 当前截图只有“药水栏存在”，没有明确的冷却/灰态对照

5. 商店/维修界面样本
   - 如果后续要继续做维护流程，需要至少 1 组真实界面截图

## 6. 补图命令

### 6.1 transition 边界

```bash
python3 scripts/extract_video_frames.py \
  --video /mnt/e/code/AradVision/assets/video/jmzjz_abyssroom03.mp4 \
  --times-file /mnt/e/code/AradVision/docs/歼灭追击战固定路线MVP改造/jmzjz_abyssroom03_补充截图_transition.txt \
  --output /mnt/e/code/AradVision/assets/video/jmzjz_abyssroom03_transition_frames \
  --prefix jmzjz_abyssroom03_transition
```

### 6.2 终段 clear / boss / result

```bash
python3 scripts/extract_video_frames.py \
  --video /mnt/e/code/AradVision/assets/video/jmzjz_abyssroom03.mp4 \
  --times-file /mnt/e/code/AradVision/docs/歼灭追击战固定路线MVP改造/jmzjz_abyssroom03_补充截图_endgame.txt \
  --output /mnt/e/code/AradVision/assets/video/jmzjz_abyssroom03_endgame_frames \
  --prefix jmzjz_abyssroom03_endgame
```

## 7. 建议的实现顺序

1. 先固定 `main_view` 与 `minimap` 的 ROI
2. 再验证 `run_finished / transition / combat / clear / boss`
3. 再决定 `StateReader` 中哪些字段本轮真能做
4. 最后再进入 `dungeon_run.enabled`、`WGC/MSS/F12` 的联调
