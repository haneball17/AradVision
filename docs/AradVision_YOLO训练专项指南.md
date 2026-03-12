# AradVision YOLO 训练专项指南

**状态**: 采用外部视频流采集方案
**最后更新**: 2026-03-12

## 1. 当前原则

- YOLO 训练仍然独立于自动化主链路开发。
- 仓库内不再承担训练数据采集工作台职责。
- 原始资产获取方式改为外部录屏工具或你自己的视频流截取方案。
- 仓库只维护导入约定、训练依赖说明和模型接入路径。

## 2. 推荐数据流程

```text
外部录屏/视频流 -> 仓库外原始视频存储 -> 仓库外拆帧/初筛 -> 按规范导入 -> 标注/训练 -> 模型回灌
```

## 3. 数据采集

### 3.1 采集方式

- 使用你熟悉的录屏工具或视频流截取方式录制原始素材。
- 录制时尽量固定分辨率、帧率和游戏区域，减少后续清洗成本。
- 原始视频不建议进入 git；优先保存在仓库外的独立资产目录。

### 3.2 录制建议

- 固定游戏分辨率，例如 `1920x1080`
- 录制完整战斗、过图、掉落等关键场景
- 保留场景切换前后的上下文，方便后续筛帧
- 同一角色、同一地图、同一 UI 布局尽量按会话分组

### 3.3 会话命名

推荐会话标识：

```text
YYYYMMDD_<主题或地图>_<来源标识>
```

示例：

```text
20260312_loran_obs
20260312_boss_route_capturecard
```

## 4. 导入约定

如果需要在仓库内做本地暂存，只使用以下 gitignore 目录：

- `assets/videos/`
- `assets/imported/`
- `assets/frames/`

推荐导入结果结构：

```text
assets/imported/<session_id>/
├── images/
└── manifest.json
```

`manifest.json` 最小字段：

```json
{
  "session_id": "20260312_loran_obs",
  "source_video": "D:/AradVisionAssets/videos/20260312_loran_obs.mp4",
  "capture_time": "2026-03-12T20:00:00+08:00",
  "fps": 60,
  "resolution": "1920x1080",
  "scene_hint": "combat",
  "game_build_or_region": "DNF Taiwan",
  "notes": "boss room + loot segment"
}
```

## 5. 标注与训练

- 标注工具自行选择，但标注输出应与训练脚本兼容。
- 训练依赖仍然建议使用独立环境，避免污染主运行环境。
- 训练完成后，只把模型文件放到 `models/` 本地目录，不直接提交大模型文件。

基础依赖示例：

```bash
pip install torch torchvision torchaudio
pip install ultralytics opencv-python pyyaml numpy pillow
```

## 6. 模型接入

训练好的模型接入方式不变：

1. 将模型放到 `models/` 本地目录
2. 在 `configs/config.yaml` 中更新 `detector.model_path`
3. 保留 Mock 回退能力
4. 用主链路测试验证真实检测结果

## 7. 当前不再做的事情

- 仓库内训练数据工作台
- 时间线采集/筛选/预标注 UI
- 依赖工作台的仓库内数据收集说明

如需查看历史方案，请参考归档说明或切换到工作台归档分支。
