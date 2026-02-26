# YOLO 训练数据资产管理工作台
# 架构总纲 v2.1（数据策展 / 数据中心）
**版本**: v2.1  
**日期**: 2026-02-26  
**定位**: 数据资产管理工作台（采集 + 数据策展 + 预标注 + 导出与复核）  
**适用阶段**: 采集 → 筛选（策展）→ 预标注 → 复核 → 训练  

> v2.1 在 v2.0 基础上补齐：**数据策展最佳实践、状态模型、可审计导出、与伪标签闭环对齐**。  
> 本文参考了开源数据策展工具 FiftyOne 的理念：通过 **可视化、过滤、标记、迭代** 提升数据质量与模型效果。 citeturn0search11turn0search7turn0search3

---

## 1. 背景与问题陈述

v1.x 以“时间线区间抽样”为核心，适合“边采集边导出”。  
但真实工作流更常见的是：

> **先大量采集（100–5000 张）→ 再慢慢筛选（人眼 + 指标）→ 生成高质量子集 → 预标注 → 复核 → 训练。**

因此 v2.x 需要把系统从“时间驱动工具”升级为：

> **数据状态驱动的资产管理工作台**（数据策展 / Data Curation）。

---

## 2. 核心理念（v2.x）

### 2.1 从“区间”到“状态”
- v1.x：时间区间 → 抽样 → 导出  
- v2.x：样本状态 → 过滤/排序 → 标记 → 子集生成 → 预标注

### 2.2 数据策展闭环
借鉴数据中心（data-centric）的实践：通过筛选低质量样本、查找难例、管理标记与版本，持续提升训练集质量。 citeturn0search11turn0search7

---

## 3. 顶层信息架构（IA）

采用 **流程导航（Stepper）**：
```text
[1 采集] → [2 数据筛选/策展] → [3 预标注] → [4 导出与复核]
```

实现上仍可用 `QStackedWidget`，但认知结构必须是“流水线阶段”。

---

## 4. 数据模型与状态机

### 4.1 样本生命周期（Sample Lifecycle）

```text
raw
  → auto_filtered         # 自动过滤（模糊/重复/异常）
  → curated               # 人工策展已处理（manual_flag != none）
  → selected              # 进入候选训练子集（由导出规则决定）
  → pseudo_labeled        # 已生成伪标签（可选）
  → reviewed              # 人工复核通过/修正
  → train_ready           # 满足训练契约（格式校验通过）
```

### 4.2 最小新增字段（建议写入 samples.jsonl）
```json
{
  "manual_flag": "none | star | reject | review",
  "manual_updated_at": "ISO8601",
  "pseudo_version": "v1.0",
  "pseudo_obj_count": 3,
  "pseudo_conf_mean": 0.72
}
```

### 4.3 标记语义（Manual Flag）
| 状态 | 含义 | 用途 |
|---|---|---|
| none | 未处理 | 默认 |
| star | 高价值 | 优先进入训练子集 |
| reject | 丢弃 | 不导出训练 |
| review | 需复核 | 进入复核/难例队列 |

---

## 5. 模块职责（清晰边界）

### 5.1 采集模块（Data Ingestion）
**职责：**
- 捕获后端初始化、启动/暂停/停止
- 自动采样、落盘
- 自动质量过滤（模糊/重复）
- 会话级元数据：`session_manifest.json`、`samples.jsonl`

**不负责：**
- 人工筛选、标记
- 导出规则决策
- 预标注任务编排

---

### 5.2 数据筛选/策展模块（Data Curation）—— v2.x 核心
借鉴 FiftyOne 等工具的典型能力：**过滤（filter）/ 标记（tag）/ 视图（view）/ 迭代（iterate）**。 citeturn0search11turn0search7turn0search3

#### 5.2.1 默认主视图：网格（Thumbnail Grid）
- 用于快速人眼判断
- 支持多选、快捷键标记
- 缩略图叠加“质量信号”：blur/diff/scene/objs/flag

#### 5.2.2 辅助视图：时间线（Timeline）
- 仅用于分析连续变化与异常片段
- 不作为默认入口（避免“时间驱动”回归）

#### 5.2.3 指标 + 视觉组合（典型筛选策略）
- 先用指标缩小范围：清晰度阈值、差异度阈值、场景过滤
- 再用视觉标记：⭐/❌/⚠
- 最后导出：仅 ⭐ 或 ⭐+⚠

---

### 5.3 预标注模块（Pseudo-label Orchestration）
**输入不再是目录**，而是“集合视图”：
- 对 ⭐ 样本运行
- 对 ⚠ 样本运行
- 对当前筛选结果运行
- 对当前选中运行

**输出必须版本化：**
- `labels_pseudo/<version>/`
- 伪标签 manifest 记录模型路径、阈值、生成时间、覆盖样本数等

---

### 5.4 导出与复核模块（Export & Review）
导出从“区间驱动”升级为“状态驱动”。

导出模式：
- by_flag：仅 ⭐ / ⭐+⚠
- by_filter：当前筛选视图
- manual_selection：当前选中集

并强制输出：
- `selection_manifest.json`（可复现导出）
- `validation_report.json`（训练契约校验）

---

## 6. Manifest 与可复现性（Auditability）

### 6.1 session_manifest.json（会话级）
建议字段：
- capture backend、分辨率、窗口状态
- 采样间隔、过滤开关与阈值（配置快照路径）
- 场景分布、过滤原因分布
- 实验/会话 ID（可复现）

### 6.2 samples.jsonl（样本级主契约）
每行一个样本，最小字段建议：
- `timestamp` / `scene` / `backend` / `resolution`
- `filtered` / `filter_reason`
- `blur_score` / `similarity_to_prev`
- `manual_flag` / `manual_updated_at`
- 伪标签扩展字段（可选）

### 6.3 selection_manifest.json（导出级）
必须包含：
- selection_mode（by_flag/by_filter/manual_selection）
- 过滤条件快照（阈值/场景/排序）
- flag 分布统计（star/reject/review/none）
- split 策略与随机种子

---

## 7. UI 关键交互（与架构一致）

### 7.1 筛选页的“效率黄金三角”
- 左侧：过滤器（理性）
- 中间：网格缩略图（感性）
- 底部：快捷键提示（动作）

### 7.2 快捷键建议（默认）
- `1` ⭐、`2` ❌、`3` ⚠、`0` 清除
- `Ctrl+F` 搜索、`Ctrl+A` 全选、`Ctrl+E` 导出
- `Space` 快速预览（可选）

---

## 8. 伪标签闭环（P1/P2 演进建议）

### 8.1 置信度分层（建议）
- 高置信：直接进入“待复核快速通道”
- 低置信：进入“⚠ review”队列（优先人工检查）

### 8.2 难例挖掘（未来）
数据策展工具常通过“低置信/冲突/异常尺寸”等信号发现难例；可在 P2 引入“困难样本列表”。 citeturn0search11turn0search7

---

## 9. 成功标准（v2.x 验收）

1. **1000 张样本**：在筛选页通过过滤+快捷键标记，**10 分钟内完成首轮策展**（星/弃/复核）。
2. 导出流程无需创建多个中间目录；导出可通过 manifest 复现。
3. 预标注可选择输入集合（⭐、⚠、当前筛选、选中集），并输出版本化结果。
4. 训练契约校验通过（图片-标签配对、坐标范围、类别范围）。

---

## 10. 风险与应对

- **QSS 维护失控**：采用 token + 组件化 QSS 架构；全局一次性加载，避免散落 setStyleSheet。Qt 官方说明可在应用层级设置样式并级联推导。 citeturn0search4
- **数据版本混乱**：强制 `selection_manifest.json` 与伪标签版本 manifest。
- **筛选效率低**：默认网格视图 + 快捷键标记 + 指标过滤组合（而非时间线主导）。
- **伪标签噪声高**：置信度分层 + review 队列 + 抽检策略。

---

## 11. 附：与 v1.x 的核心变化摘要

| 主题 | v1.x | v2.x |
|---|---|---|
| 核心视图 | 时间线 | 网格（主）+ 时间线（辅） |
| 导出模式 | 区间驱动 | 状态驱动（flag/filter/selection） |
| 数据管理 | 目录分散 | samples.jsonl 统一状态 |
| 预标注输入 | 目录 | 集合视图（⭐/⚠/筛选/选中） |
| 可追溯 | 部分 | 全链路 manifest |

