# YOLO训练数据采集与伪标签方案

**文档主题**: YOLO训练数据采集与伪标签方案  
**文档路径**: `docs/YOLO训练数据采集与伪标签方案/YOLO训练数据采集与伪标签方案.md`  
**版本**: v1.3  
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

## 2.1 已冻结决策（本轮确认）
1. 首批采集目标量级：`1000` 张，按 `500 + 500` 两阶段执行。  
2. 首版不在采集主流程中启用伪标签，先完成高质量采集闭环。  
3. 场景标签采用“核心固定 + 可扩展”：`combat/navigate/loot/boss/other`。  
4. 伪标签首版仅覆盖 `monster/hero/gate` 三类。  

## 2.2 决策理由（用于执行约束）
1. 1000 张是效率与质量平衡点。500 张仅够流程验证，2000 张会显著推高首轮标注成本。  
2. 采集主流程优先稳定性。伪标签依赖模型质量，前置会引入噪声与排障复杂度。  
3. 场景标签必须有 `other` 兜底，避免菜单、过场、空房间等异常帧污染核心桶。  
4. `monster/hero/gate` 更适合首轮伪标签；`item/boss` 样本稀疏且更易误检，后续扩展更稳妥。  

## 2.3 评审建议采纳矩阵（v1.2）
| 建议项 | 结论 | 落地阶段 | 说明 |
|---|---|---|---|
| 增强元数据可追溯字段 | 采纳 | P0 | 直接提升排障与数据质检效率。 |
| 场景标签视觉反馈与告警 | 采纳 | P0 | 降低人工忘切场景导致的标签污染。 |
| 采集前磁盘空间检查 | 采纳 | P0 | 低成本高收益，避免中途失败。 |
| 会话级实验 ID + 配置快照 | 采纳 | P0 | 强化可复现性与回溯能力。 |
| 动态模糊阈值 | 调整后采纳 | P1 | 首版仅记录建议阈值，默认不自动生效。 |
| 伪标签阈值校准流程 | 调整后采纳 | P1 | 基于 100 张金标准后再固化阈值。 |
| SSIM 重复帧检测 | 调整后采纳 | P1 | 作为可选开关，默认维持轻量实现。 |
| 场景自动检测 | 暂缓 | P2 | 规则/模型维护成本高，首版不引入。 |
| 实时可视化面板 | 暂缓 | P2 | 先用日志与会话报告满足需求。 |

## 2.4 训练工程增强采纳矩阵（v1.3）
| 建议项 | 结论 | 落地阶段 | 说明 |
|---|---|---|---|
| 数据集科学划分（防泄露） | 采纳 | P0 | 训练/验证可靠性的基础保障。 |
| YOLO 格式验证工具 | 采纳 | P0 | 防止“可导出但不可训练”。 |
| 伪标签版本管理 | 采纳 | P1 | 支持模型迭代比较与回溯。 |
| 目标级统计信息 | 调整后采纳 | P1 | 作为衍生统计产物，不污染采集主记录契约。 |
| 数据增强配置 | 调整后采纳 | P1 | 优先复用 Ultralytics 训练参数体系。 |
| 目标尺寸分析 | 采纳 | P1 | 用于分布健康检查与异常排查。 |
| 困难样本挖掘 | 暂缓 | P2 | 有价值但实现成本较高。 |
| 标注审查工具 | 暂缓 | P2 | 先用 CVAT/LabelImg + 轻量脚本。 |
| 完整实验追踪平台 | 暂缓 | P2 | 先以 manifest + 目录规范过渡。 |

## 3. 范围与非目标
### 3.1 本次范围
1. 新增 `scripts/collect_yolo_data.py`（核心采集脚本）。
2. 新增 `configs/config.yaml` 中 `dataset` 配置段（采样参数、输出目录、热键、过滤阈值）。
3. 新增元数据文件输出（`session_manifest.json`、`samples.jsonl`）。
4. 新增数据集划分与防泄露策略（导出阶段产出 train/val/test）。
5. 新增 YOLO 格式验证脚本（导出后自动或手动执行）。
6. 预留离线伪标签接口，不纳入首版采集主流程。

### 3.2 非目标
1. 本次不追求“全自动高精度标注替代人工”。
2. 本次不实现完整训练流水线自动化（训练脚本仍按现有文档执行）。
3. 本次不覆盖 Linux/macOS 全平台热键差异，先聚焦 Windows。
4. 本次不在 UI 文档中展开训练工程细节，统一收敛到本专题文档。

## 4. 现有资源复用策略
1. 捕获: 复用 `core.capture.create_capture_engine`（支持 `wgc/mss/mock` 与降级策略）。
2. 配置: 复用 `core.config.ConfigLoader`。
3. 日志: 复用 `core.logger`，统一记录采集会话。
4. 分析: 复用 `scripts/analyze_dataset.py` 输出采集后统计。
5. 类别定义: 对齐 `monster/hero/item/gate/boss`（YOLO专项文档既有定义）。

## 5. 功能设计
### 5.1 P0（首版必须）
1. 启动采集会话：读取配置、初始化捕获后端、打印 `requested_backend/active_backend`。
2. 自动采样：按固定间隔写入图片（默认 0.5s，可配置），首批目标 1000 张。
3. 热键控制：开始/暂停/停止、手动快照、场景标签切换。
4. 质量过滤：
- 模糊过滤（拉普拉斯方差阈值）
- 重复帧过滤（MSE 或轻量帧差）
5. 数据落盘：
- 图片文件
- `samples.jsonl`（含窗口状态、分辨率、过滤原因、质量分数）
- `session_manifest.json`（会话级统计、实验ID、配置快照路径）
6. 可追溯与防错：
- 采集前磁盘空间检查，空间不足则告警并拒绝启动
- 场景标签视觉反馈（周期打印当前场景与分布）
- 单场景连续超阈值告警，提醒切换标签
7. 导出阶段数据集划分（防泄露）：
- 默认按 `group_by=session/time_chunk` 进行分组划分，避免近邻帧跨集合泄露
- 比例默认 `train/val/test = 0.8/0.15/0.05`
- 支持按场景分层约束，保证主要场景在各集合可见
8. YOLO 格式验证：
- 提供 `scripts/validate_yolo_dataset.py` 校验图片-标签配对、坐标范围、类别范围
- 输出 `validation_report.json` 与 `validation_errors.jsonl`
9. 两阶段配额执行：
- 阶段 1：先采集 500 张，做一次分布体检与抽样质检
- 阶段 2：再补采 500 张，针对短板场景定向补齐

### 5.2 P1（效率增强）
1. 采样配额提醒（按场景/类别目标计数）。
2. 采集后自动生成 `classes.txt` 与训练目录骨架。
3. 一键调用 `scripts/analyze_dataset.py` 并保存分析报告。
4. 模糊阈值校准增强：启动采样基线并输出建议阈值（默认仅记录，不自动覆盖）。
5. 伪标签阈值校准：基于人工金标准样本计算 PR/F1 后固化阈值。
6. 重复帧增强：`SSIM` 作为可选开关，默认关闭。
7. 伪标签版本管理：按 `labels_pseudo/<version>/` 管理并写入版本 manifest。
8. 目标级衍生统计：输出 `object_stats.json`（类别计数、尺寸分布、覆盖率），不回写 `samples.jsonl` 主契约。
9. 目标尺寸分析：输出分布图与异常样本清单，用于数据健康检查。
10. 数据增强配置：复用 Ultralytics 参数（mosaic/mixup/hsv 等），提供预览脚本。

### 5.3 P2（伪标签与扩展）
1. 离线伪标签生成：
- 输入采集图片
- 使用 detector 推理产生候选框
- 按置信度、尺寸、长宽比过滤
- 输出 YOLO txt 到 `labels_pseudo/`
2. 首版只对 `monster/hero/gate` 生成伪标签。
3. 伪标签质量分层：高置信度进入复核队列，低置信度进入人工重标队列。
4. 困难样本挖掘：基于低置信度与冲突预测输出优先复核列表。
5. 标注审查工具：轻量评分与接受/拒绝流转。
6. 场景自动检测与实时可视化面板暂缓到 P2 后段评估，不进入首版交付。

## 6. 自动打标签原理
### 6.1 场景级标签（稳定）
1. 通过热键切换当前场景状态（如 `combat`, `navigate`, `loot`, `boss`, `other`）。
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
5. 说明：当前以 YOLOv8 为主（anchor-free），尺寸分析用于数据分布健康检查，不作为手工 anchor 设计前置步骤。

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
  experiment_id: auto
  save_config_snapshot: true
  image_format: jpg
  interval_sec: 0.5
  max_images: 1000
  min_free_space_gb: 2.0
  keep_filtered_samples: false
  scene_status_log_every: 50
  single_scene_warn_threshold: 100
  enable_blur_filter: true
  blur_threshold: 80.0
  blur_baseline_mode: observe
  enable_dedup_filter: true
  dedup_method: mse
  enable_ssim: false
  dedup_diff_threshold: 3.0
  default_scene: other
  scene_labels: [combat, navigate, loot, boss, other]
  hotkeys:
    start_pause: F8
    stop: F12
    snapshot: F9
    scene_combat: 1
    scene_navigate: 2
    scene_loot: 3
    scene_boss: 4
    scene_other: 0
  pseudo_label:
    enabled: false
    detector: yolo
    classes: [monster, hero, gate]
    version: v1.0
    thresholds:
      monster: 0.60
      hero: 0.65
      gate: 0.55
  split:
    enabled: true
    strategy: grouped_stratified
    group_by: [session, time_chunk]
    split_by_scene: true
    train_ratio: 0.8
    val_ratio: 0.15
    test_ratio: 0.05
    random_seed: 42
    min_samples_per_class: 50
  validation:
    enabled: true
    fail_on_error: true
  augmentation:
    enabled: false
    preset: ultralytics_default
    mosaic: 1.0
    mixup: 0.0
    hsv_h: 0.015
    hsv_s: 0.7
    hsv_v: 0.4
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
      config_snapshot.yaml
assets/images/selected/
  <session_name>/<export_id>/
    images/{train,val,test}/
    labels/{train,val,test}/
    selection_manifest.json
    validation_report.json
    validation_errors.jsonl
assets/labels_pseudo/
  <version>/
    labels/
    manifest.json
```

说明:
1. `samples.jsonl`: 每行一个样本，建议至少包含以下字段。
- `timestamp`, `scene`, `backend`, `window_state`, `resolution`
- `actual_interval_sec`, `filtered`, `filter_reason`
- `blur_score`, `similarity_to_prev`
2. `session_manifest.json`: 会话汇总（总数、过滤率、场景分布、后端信息、实验ID、环境指纹、配置快照路径）。
3. `selection_manifest.json`: 导出参数、划分策略、分布统计与结果计数。
4. `validation_report.json`: YOLO 格式校验结果汇总；`validation_errors.jsonl` 记录逐条错误。
5. 如启用伪标签，按版本目录输出并附带 `manifest.json`（模型路径、阈值、生成时间、质量统计）。

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

训练集导出与校验（建议）:
```bash
python scripts/export_yolo_dataset.py \
  --session day1_luolan \
  --split grouped_stratified \
  --train-ratio 0.8 --val-ratio 0.15 --test-ratio 0.05

python scripts/validate_yolo_dataset.py \
  --dataset assets/images/selected/day1_luolan/export_001 \
  --fail-on-error
```

## 11. 分阶段实施计划
### 阶段 A（0.5 天，首轮 500 张）
1. 完成 P0 采集主流程、热键控制、质量过滤与会话元数据。
2. 完成 `500` 张采集并输出统计报告（含过滤原因分布）。
3. 进行 10% 抽样质检（清晰度、重复率、场景分布）。
4. 输出模糊阈值建议值与重复帧参数观察报告（不自动改阈值）。
5. 完成首版数据集划分与 YOLO 格式校验，输出校验报告。

### 阶段 B（0.5 天，二轮补采 500 张）
1. 根据阶段 A 报告补齐短板场景与类别可见性。
2. 累计采集达到 `1000` 张。
3. 固化训练前目录结构与 `classes.txt`。
4. 若进入伪标签准备，先完成 100 张金标准标注用于阈值校准。
5. 落地伪标签版本管理、目标级衍生统计、尺寸分布分析。

### 阶段 C（1 天，离线伪标签）
1. 实现伪标签离线脚本（仅 `monster/hero/gate`）。
2. 建立“伪标签 -> 人工复核 -> 训练集入库”说明。
3. 输出伪标签质量统计（通过率、人工修正率）。
4. 评估困难样本挖掘与标注审查工具是否进入下一迭代。

## 12. 验收标准
1. 30 分钟采集不中断，无异常崩溃。
2. 首批累计完成 `1000` 张有效图片（过滤后）。
3. 场景分布包含 `combat/navigate/loot/boss/other` 五类，且无单类极端失衡。
4. 会话结束后可得到完整图片、`samples.jsonl`、`session_manifest.json`。
5. 过滤策略生效：重复帧比例显著下降，模糊帧可追踪。
6. 日志可追溯（包含后端、参数、起止时间）。
7. 数据集划分结果满足 `train/val/test` 比例约束，且无同组样本跨集合泄露。
8. `validate_yolo_dataset.py` 通过率达到 100%（硬错误为 0）。
9. 若启用伪标签，首版仅 `monster/hero/gate`，且输出可直接进入复核流程。
10. 产出 `selection_manifest.json` 与 `validation_report.json`，可支撑训练复现。

## 13. 风险与应对
1. WGC 不可用导致采集失败。
- 应对: 明确 `allow_fallback` 策略；调试阶段建议禁止降级，定位根因。
2. 自动伪标签噪声高。
- 应对: 按置信度分层 + 强制人工抽检。
3. 采样过密导致磁盘压力。
- 应对: 控制 `interval/max_images`，会话级限额与空间预检查。
4. 场景标签误切/漏切导致污染。
- 应对: 周期状态提示 + 单场景超阈值告警 + `other` 兜底。
5. 数据泄露导致验证指标虚高。
- 应对: 分组划分（session/time_chunk）+ 导出后泄露检查。
6. YOLO 标注格式错误导致训练失败。
- 应对: 导出后强制执行格式验证，`fail_on_error=true` 默认阻断训练。

## 14. 执行清单（暂缓细化）
本版先冻结方案与边界，不在本文展开可执行任务拆分。  
后续在进入开发落地时，单独输出“可执行任务清单”文档。
