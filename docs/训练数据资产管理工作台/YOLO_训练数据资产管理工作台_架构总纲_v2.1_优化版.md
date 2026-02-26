# YOLO 训练数据资产管理工作台
# 架构总纲 v2.2（评估与优化版）
**版本**: v2.2  
**日期**: 2026-02-26  
**角色**: 架构与逻辑工程师（yangmq17）

## 0. 文档定位
本文件用于给“采集-筛选-预标注-导出”全链路定架构边界、状态模型和实施顺序，目标是把工具从“时间线采样器”升级为“数据资产管理工作台”。

## 1. 对 v2.1 的评估结论
### 1.1 已有优势
1. 明确了从“时间驱动”转向“状态驱动”的方向。
2. 识别出数据策展（Data Curation）是核心价值点。
3. 已引入 manifest 思维，具备可追溯基础。

### 1.2 关键缺口
1. 数据契约粒度不足：样本、会话、导出、伪标签任务之间字段映射不完整。
2. 状态机缺少“幂等与回滚”规则：失败重试后状态一致性风险高。
3. 训练集划分策略未固化：存在时间泄漏/场景泄漏风险。
4. 运行态与历史态没有统一索引：难以进行跨会话统计与复盘。

## 2. 架构目标（v2.2）
1. 用统一状态模型管理样本生命周期，而非临时目录操作。
2. 导出必须可复现：任何导出可由 manifest 在新环境重建。
3. 预标注必须版本化：同一批样本允许多版本模型重复推理和对比。
4. 工具默认“主区优先”：低优先级面板支持折叠，不挤占策展主流程。

## 3. 分层架构
1. 表现层（UI Workbench）：流程导航、筛选视图、任务控制、日志与告警。
2. 应用服务层（Use Cases）：采集编排、筛选编排、预标注编排、导出编排。
3. 领域层（Domain）：样本状态机、筛选规则、导出策略、任务状态机。
4. 基础设施层（Infra）：捕获后端、文件系统、配置中心、模型推理、序列化。

## 4. 样本状态模型
```text
raw -> auto_filtered -> curated -> selected -> pseudo_labeled -> reviewed -> train_ready
```
- `raw`: 采集入库。
- `auto_filtered`: 自动质量过滤完成（模糊/重复/异常）。
- `curated`: 人工标记完成（star/reject/review）。
- `selected`: 满足导出策略。
- `pseudo_labeled`: 已绑定伪标签版本。
- `reviewed`: 人工复核通过或修订。
- `train_ready`: 通过格式与完整性校验。

## 5. 核心流程
1. 采集：会话创建 -> 帧入库 -> 自动过滤 -> 写入 `samples.jsonl`。
2. 筛选：基于过滤条件+标记规则形成“工作视图”（可保存）。
3. 预标注：按视图子集触发任务，输出版本化标签与任务 manifest。
4. 导出：按 flag/filter/selection 生成训练包并输出校验报告。

## 6. 最小契约集合
1. `samples.jsonl`：样本级事实表（时间、场景、质量、人工标记、伪标签摘要）。
2. `session_manifest.json`：会话级配置快照（后端、阈值、分辨率、环境指纹）。
3. `pseudo_task_manifest.json`：任务级状态（模型版本、阈值、输入集、失败摘要）。
4. `selection_manifest.json`：导出级可复现说明（筛选条件、拆分策略、结果计数）。

## 7. 非功能约束
1. 可复现：导出必须包含随机种子、筛选表达式、版本号。
2. 可追溯：所有状态跃迁记录 `who/when/why`。
3. 可恢复：导出与预标注采用临时目录事务提交，失败可清理或恢复。
4. 可扩展：允许切换标注后端（CVAT/Label Studio）而不改领域模型。

## 8. 迁移建议（是否先回退）
不建议先回退到“工具实现之前”。建议：
1. 保留现有分支历史，新增 `refactor/data-workbench-v2` 分支实施重构。
2. 采用“并行迁移”：旧入口保留，新增 v2 入口灰度验证。
3. 通过 `git revert` 回滚单次有问题提交，不使用 `reset --hard` 破坏共享历史。

## 9. 里程碑
1. M1：完成契约与目录结构，跑通采集->筛选->导出最小闭环。
2. M2：接入预标注任务编排与版本化输出。
3. M3：完成训练前校验、统计报表、跨会话检索。

## 10. 参考资料
1. FiftyOne Dataset Views: https://docs.voxel51.com/user_guide/using_views.html
2. FiftyOne App: https://docs.voxel51.com/user_guide/app.html
3. Label Studio Data Manager: https://labelstud.io/guide/manage_data
4. Label Studio Predictions: https://labelstud.io/guide/predictions
5. CVAT Dataset Management: https://docs.cvat.ai/docs/dataset_management/
6. CVAT Ultralytics YOLO Format: https://docs.cvat.ai/docs/dataset_management/formats/format-yolo-ultralytics/
7. Ultralytics Detect Datasets: https://docs.ultralytics.com/datasets/detect/
8. DVC Versioning Data and Models: https://doc.dvc.org/use-cases/versioning-data-and-models
9. Qt QMainWindow: https://doc.qt.io/qt-6/qmainwindow.html
10. Qt QDockWidget: https://doc.qt.io/qt-6/qdockwidget.html
