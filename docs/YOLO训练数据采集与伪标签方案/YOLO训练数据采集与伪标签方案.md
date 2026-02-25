# YOLO训练数据采集与伪标签方案

**文档主题**: YOLO训练数据采集与伪标签方案  
**文档路径**: `docs/YOLO训练数据采集与伪标签方案/YOLO训练数据采集与伪标签方案.md`  
**版本**: v1.0  
**日期**: 2026-02-25  
**角色**: 架构与逻辑工程师（yangmq17）

## 1. 背景
当前项目已完成输入链路与UI画面预览验证，下一阶段瓶颈转移到视觉训练数据。现有 `scripts/capture_training_data.py` 可用，但与当前捕获架构（`core/capture.py` 的 WGC/MSS 门面）解耦，且缺少可追溯元数据、质量过滤和伪标签闭环。

## 2. 目标
1. 提供统一的数据采集脚本，复用项目现有捕获与配置体系。  
2. 支持可控的“自动打标签”能力：
- 场景级标签（可靠）
- 目标框伪标签（可复核）
3. 形成“采集 -> 过滤 -> 元数据 -> 伪标签 -> 人工复核 -> 训练”的标准流程。

## 3. 范围与非目标
### 3.1 本次范围
1. 新增 `scripts/collect_yolo_data.py`（核心采集脚本）。
2. 新增 `configs/config.yaml` 中 `dataset` 配置段（采样参数、输出目录、热键、过滤阈值）。
3. 新增元数据文件输出（`session_manifest.json`、`samples.jsonl`）。
4. 新增离线伪标签脚本 `scripts/generate_pseudo_labels.py`（可选开关）。

### 3.2 非目标
1. 本次不追求“全自动高精度标注替代人工”。
2. 本次不实现完整训练流水线自动化（训练脚本仍按现有文档执行）。
3. 本次不覆盖 Linux/macOS 全平台热键差异，先聚焦 Windows。

## 4. 现有资源复用策略
1. 捕获: 复用 `core.capture.create_capture_engine`（支持 `wgc/mss/mock` 与降级策略）。
2. 配置: 复用 `core.config.ConfigLoader`。
3. 日志: 复用 `core.logger`，统一记录采集会话。
4. 分析: 复用 `scripts/analyze_dataset.py` 输出采集后统计。
5. 类别定义: 对齐 `monster/hero/item/gate/boss`（YOLO专项文档既有定义）。

## 5. 功能设计
### 5.1 P0（首版必须）
1. 启动采集会话：读取配置、初始化捕获后端、打印 `requested_backend/active_backend`。
2. 自动采样：按固定间隔写入图片（默认 0.5s，可配置）。
3. 热键控制：开始/暂停/停止、手动快照、场景标签切换。
4. 质量过滤：
- 模糊过滤（拉普拉斯方差阈值）
- 重复帧过滤（帧差阈值或哈希相似度）
5. 数据落盘：
- 图片文件
- `samples.jsonl`（时间戳、场景标签、后端、清晰度、是否过滤）
- `session_manifest.json`（会话级统计）

### 5.2 P1（效率增强）
1. 采样配额提醒（按场景/类别目标计数）。
2. 采集后自动生成 `classes.txt` 与训练目录骨架。
3. 一键调用 `scripts/analyze_dataset.py` 并保存分析报告。

### 5.3 P2（伪标签）
1. 离线伪标签生成：
- 输入采集图片
- 使用 detector 推理产生候选框
- 按置信度、尺寸、长宽比过滤
- 输出 YOLO txt 到 `labels_pseudo/`
2. 伪标签质量分层：高置信度直接入复核队列，低置信度进入人工重标队列。

## 6. 自动打标签原理
### 6.1 场景级标签（稳定）
1. 通过热键切换当前场景状态（如 `combat`, `navigate`, `loot`, `boss_room`）。
2. 每张图继承当前状态，写入元数据。
3. 优点：实现快、稳定性高、便于后续抽样与分桶。

### 6.2 目标框伪标签（半自动）
1. 先由模型输出候选框（预测 `class + bbox + conf`）。
2. 规则过滤：
- `conf >= threshold[class]`
- bbox 面积在合理区间
- 异常长宽比剔除
3. 跨帧一致性检查（可选）：同目标短时间轨迹应连续，离群框降权。
4. 导出 YOLO 标注文件，供 LabelImg/CVAT 快速校正。

### 6.3 质量结论
1. 场景标签可接近全自动。
2. 目标框属于“伪标签”，必须人工抽检与修正，不可直接视为金标准。

## 7. 技术栈
1. 语言: Python 3.10+。
2. 捕获: 项目现有 `WGC/MSS`（`core/capture.py`）。
3. 图像处理: `opencv-python`, `numpy`。
4. 热键: `keyboard`（Windows）。
5. 数据格式: `jpg/png + jsonl + yaml`。
6. 日志: `loguru`（项目封装 logger）。

## 8. 配置设计（建议新增到 config.yaml）
```yaml
dataset:
  output_dir: assets/images/raw
  session_name: auto
  image_format: jpg
  interval_sec: 0.5
  max_images: 2000
  enable_blur_filter: true
  blur_threshold: 80.0
  enable_dedup_filter: true
  dedup_diff_threshold: 3.0
  default_scene: combat
  hotkeys:
    start_pause: F8
    stop: F12
    snapshot: F9
    scene_combat: 1
    scene_navigate: 2
    scene_loot: 3
    scene_boss: 4
  pseudo_label:
    enabled: false
    detector: mock
    thresholds:
      monster: 0.60
      hero: 0.65
      item: 0.50
      gate: 0.55
      boss: 0.50
```

## 9. 目录与产物规范
```text
assets/images/raw/
  <session_name>/
    images/
      combat_000001.jpg
      navigate_000002.jpg
    meta/
      samples.jsonl
      session_manifest.json
      classes.txt
```

说明:
1. `samples.jsonl`: 每行一个样本，包含采集与过滤字段。
2. `session_manifest.json`: 会话汇总（总数、过滤率、场景分布、后端信息）。
3. 如启用伪标签，新增 `labels_pseudo/*.txt`。

## 10. CLI 设计（草案）
```bash
python scripts/collect_yolo_data.py \
  --config configs/config.yaml \
  --session-name day1_luolan \
  --backend wgc \
  --no-fallback \
  --interval 0.5 \
  --max-images 1000
```

可选参数:
1. `--scene <name>`：默认场景。
2. `--output-dir <path>`：输出路径覆盖配置。
3. `--dry-run`：只验证捕获链路，不落盘。

## 11. 分阶段实施计划
### 阶段 A（0.5 天）
1. 完成 P0 采集主流程与热键控制。
2. 输出图片与会话元数据。

### 阶段 B（0.5 天）
1. 接入质量过滤与统计。
2. 打通 `analyze_dataset.py` 报告。

### 阶段 C（1 天）
1. 实现伪标签离线脚本。
2. 建立“伪标签 -> 人工复核”操作说明。

## 12. 验收标准
1. 30 分钟采集不中断，无异常崩溃。
2. 会话结束后可得到完整图片与元数据。
3. 过滤策略生效，重复帧比例明显下降。
4. 采集日志可追溯（包含后端、参数、起止时间）。
5. 伪标签输出文件可被 YOLO 训练流程直接读取（如启用）。

## 13. 风险与应对
1. WGC 不可用导致采集失败。
- 应对: 明确 `allow_fallback` 策略；调试阶段建议禁止降级，定位根因。
2. 自动伪标签噪声高。
- 应对: 按置信度分层 + 强制人工抽检。
3. 采样过密导致磁盘压力。
- 应对: 控制 `interval/max_images`，会话级限额与空间预检查。

## 14. 待确认问题（用于下一轮讨论）
1. 首批目标量级是 500、1000 还是 2000 张？
2. 首版是否立即包含伪标签功能，还是先只做高质量采集？
3. 场景标签集合是否固定为 `combat/navigate/loot/boss`？
4. 伪标签首版是否只覆盖 `monster/hero/gate` 三类？

