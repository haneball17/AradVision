# AradVision 开发计划与里程碑 (Development Plan & Milestones)

**项目名称**: AradVision - DNF 视觉辅助自动化系统
**文档标识**: ARAD-PLAN-007
**版本**: V1.0
**状态**: 正式版
**最后更新日期**: 2026-02-10

---

## 目录 (Table of Contents)

1. [YOLO 训练专项（独立于 MVP 开发）](#1-yolo-训练专项独立于-mvp-开发yolo-training-track)
2. [项目概述](#2-项目概述project-overview)
3. [关键路径分析](#3-关键路径分析critical-path-analysis)
4. [功能优先级划分](#4-功能优先级划分feature-prioritization)
5. [开发者角色分工](#5-开发者角色分工developer-role-assignment)
6. [Mock/Stub 开发策略](#6-mockstub-开发策略mockstub-strategy)
7. [Day-by-Day 开发计划](#7-day-by-day-开发-planday-by-day-schedule)
8. [MVP 定义](#8-mvp-定义mvp-definition)
9. [并行化策略](#9-并行化策略parallelization-strategy)
10. [风险缓解方案](#10-风险缓解方案risk-mitigation)
11. [每日里程碑与交接点](#11-每日里程碑与交接点daily-milestones-handoff-points)
12. [测试与验收标准](#12-测试与验收标准testing-acceptance)
13. [时间线图表](#13-时间线图表timeline-diagrams)

---

## 1. YOLO 训练专项（独立于 MVP 开发）(YOLO Training Track - Separate from MVP)

### 1.1 专项说明

**关键决策**: YOLO 模型训练已从 MVP 开发时间线中**完全分离**，作为独立工作项进行。

**核心原则**:
- ✅ YOLO 训练不占用核心开发时间
- ✅ 可以由任何人执行（包括非开发人员）
- ✅ 可与 MVP 开发完全并行进行
- ✅ 训练完成的模型可随时集成

### 1.2 时间安排

| 阶段 | 时间 | 任务 | 负责人 | 状态 |
|------|------|------|--------|------|
| **数据采集** | Day 1-2 (4-8h) | 采集游戏截图 500-1000 张 | 任意 | 待开始 |
| **数据标注** | Day 2-3 (8-12h) | 使用 CVAT/LabelMe 标注 | 任意 | 待开始 |
| **模型训练** | Day 3-4 (8-16h) | YOLOv8n 训练 50-100 epoch | 任意 | 待开始 |
| **模型验证** | Day 4 (2-4h) | 测试 mAP、准确率 | 任意 | 待开始 |
| **模型交付** | Day 4 结束前 | 产出 `yolov8n_dnf.pt` | 任意 | 待开始 |

**目标**: Day 3 结束前完成训练，Day 4 可集成到系统中

### 1.3 输出产物

**最终交付物**:
- 📦 `models/yolov8n_dnf.pt` - 训练好的 YOLO 模型
- 📊 `models/training_results.txt` - 训练指标（mAP, loss, precision, recall）
- 📁 `models/dataset.yaml` - 数据集配置文件

**验收标准**:
- ✅ mAP @ 0.5 > 70%
- ✅ 怪物检测准确率 > 80%
- ✅ 推理速度 < 30ms (GPU)
- ✅ 模型文件 < 20MB

### 1.4 资源要求

**硬件要求**:
- GPU: NVIDIA GTX 1060 6GB 或更好
- CPU: 多核处理器
- 内存: 16GB+
- 存储: 10GB 可用空间

**软件要求**:
- Python 3.10+
- PyTorch 2.0+ (CUDA 版本)
- Ultralytics YOLOv8
- 标注工具: CVAT 或 LabelMe

### 1.5 与 MVP 的集成

**集成点**: Day 4 上午 - 模型替换

```python
# 开发期间使用 Mock
detector = MockYoloDetector()

# 模型训练完成后，一行切换
detector = YoloDetector("models/yolov8n_dnf.pt")

# 无需修改其他代码
```

**集成步骤**:
1. 将 `yolov8n_dnf.pt` 放入 `models/` 目录
2. 修改 `config.yaml` 中的 `model_path`
3. 运行集成测试验证
4. 如有问题，可随时切回 MockYoloDetector

### 1.6 降级方案

如果训练未完成或效果不佳：
- 使用 COCO 预训练模型（yolov8n.pt）
- 检测 "person" 类别作为怪物
- 可满足 MVP 基本需求

---

## 2. 项目概述 (Project Overview)

### 2.1 项目约束条件

| 约束项 | 约束值 | 影响分析 |
|--------|--------|----------|
| **团队规模** | 2 名开发者 | 需要高效分工，最大化并行化 |
| **MVP 时间** | 3 天 | 必须聚焦核心功能，砍掉非必要特性 |
| **完整产品** | 7 天 | 需要快速迭代，边开发边优化 |
| **YOLO 训练** | 独立专项 | 已从 MVP 时间线分离，可并行执行 |
| **测试环境** | 私服/单机 | 降低网络延迟干扰，专注核心逻辑 |

### 2.2 关键挑战

1. **YOLO 训练已分离**
   - ✅ 不再阻塞 MVP 开发
   - ✅ 可由任何人执行（包括非开发人员）
   - ✅ 使用 Mock 确保开发进度不受影响
   - ⚠️ 仍需在 Day 3-4 前完成以获得最佳效果

2. **3 天 MVP 时间聚焦**
   - 使用 MockYoloDetector 确保系统可运行
   - 专注于系统架构和业务逻辑
   - 模型训练完成后一行切换即可

3. **2 人协作效率**
   - 两人均为系统架构与逻辑工程师
   - 需要清晰的模块边界
   - 避免互相等待（阻塞）
   - 每日代码合并机制

---

## 3. 关键路径分析 (Critical Path Analysis)

### 3.1 项目关键路径图

```
┌─────────────────────────────────────────────────────────────────┐
│                   MVP 关键路径 (MVP Critical Path)               │
└─────────────────────────────────────────────────────────────────┘

Day 1          Day 2          Day 3          Day 4
│              │              │              │
▼              ▼              ▼              ▼
[基础框架] → [核心模块] → [业务逻辑] → [系统集成]
  (4h)         (16h)        (16h)        (8h)

    ═════════════════ MVP 开发时间线 ═════════════════

┌─────────────────────────────────────────────────────────────────┐
│              YOLO 训练专项（独立并行）(YOLO Training Track)       │
└─────────────────────────────────────────────────────────────────┘

Day 1          Day 2          Day 3          Day 4
│              │              │              │
▼              ▼              ▼              ▼
[数据采集] → [数据标注] → [模型训练] → [模型集成]
  (4h)         (8h)         (16h)        (2h)

    ∼∼∼∼∼∼∼∼∼∼∼ 可独立进行，不阻塞 MVP ∼∼∼∼∼∼∼∼∼∼∼

集成点: Day 4 - 模型训练完成，切换到真实 YoloDetector
```

### 3.2 任务依赖关系矩阵

| 任务 | 前置任务 | 持续时间 | 负责人 | 是否关键路径 |
|------|----------|----------|--------|--------------|
| **基础框架搭建** | 无 | 2h | haneball17 | ✅ 是 |
| **ConfigLoader** | 基础框架 | 1h | haneball17 | ✅ 是 |
| **CaptureEngine** | ConfigLoader | 3h | haneball17 | ✅ 是 |
| **InputDriver** | ConfigLoader | 4h | yangmq17 | ✅ 是 |
| **MockYoloDetector** | 基础框架 | 2h | haneball17 | ✅ 是 |
| **BotFSM (Mock版)** | MockYoloDetector | 6h | yangmq17 | ✅ 是 |
| **PathPlanner** | BotFSM | 4h | yangmq17 | ✅ 是 |
| **StateReader** | CaptureEngine | 4h | haneball17 | ✅ 是 |
| **系统集成** | 所有模块 | 4h | 两人 | ✅ 是 |
| **E2E 测试** | 系统集成 | 6h | 两人 | ✅ 是 |
| **YOLO 数据采集** | 无 | 4h | 任意 | ❌ 否（独立） |
| **YOLO 数据标注** | 数据采集 | 8h | 任意 | ❌ 否（独立） |
| **YOLO 模型训练** | 数据标注 | 16h | 任意 | ❌ 否（独立） |

### 3.3 关键路径时间统计

**MVP 关键路径总时长**: 40 小时（3 个工作日，紧凑安排）

**YOLO 训练专项**: 28 小时（可并行，不阻塞 MVP）

**集成缓冲时间**: 各模块有 1-2 天缓冲

---

## 4. 功能优先级划分 (Feature Prioritization)

### 3.1 优先级定义

| 优先级 | 定义 | MVP 包含 | 完整版包含 |
|--------|------|----------|------------|
| **P0 (Must-Have)** | 核心功能，缺失则系统无法运行 | ✅ 是 | ✅ 是 |
| **P1 (Should-Have)** | 重要功能，显著提升用户体验 | ⚠️ 部分 | ✅ 是 |
| **P2 (Nice-to-Have)** | 锦上添花，不影响核心流程 | ❌ 否 | ✅ 是 |

### 3.2 详细功能清单

#### P0 功能 (MVP 必须实现)

| 模块 | 功能 | 描述 | 验收标准 |
|------|------|------|----------|
| **视觉** | 实时截图 | ≥ 30 FPS 捕获游戏画面 | FPS ≥ 30 |
| **视觉** | 怪物检测 | YOLO 检测怪物，置信度 > 0.6 | mAP > 70% |
| **视觉** | 玩家检测 | 检测玩家自身位置 | 准确率 > 85% |
| **逻辑** | Y 轴对齐 | 与怪物深度对齐 | 误差 < 15 像素 |
| **逻辑** | 索敌逻辑 | 选择最近目标 | 正确率 > 90% |
| **逻辑** | 状态机 | Idle/Combat/Loot/Navigate 状态流转 | 无死循环 |
| **执行** | 移动控制 | 方向键移动 | 响应延迟 < 100ms |
| **执行** | 攻击模拟 | X 键攻击 | 命中率 > 80% |
| **安全** | F12 熔断 | 紧急停止 | 延迟 < 50ms |
| **配置** | YAML 配置 | 加载参数 | 无报错 |

#### P1 功能 (完整版应实现)

| 模块 | 功能 | 描述 | 验收标准 |
|------|------|------|----------|
| **视觉** | 技能 CD 检测 | 检测技能可用性 | 准确率 > 75% |
| **视觉** | HP/MP 读取 | 颜色识别血条 | 误差 < 10% |
| **视觉** | 门/传送阵识别 | 识别房间出口 | 准确率 > 80% |
| **逻辑** | 自动拾取 | 拾取掉落物品 | 拾取率 > 70% |
| **逻辑** | 房间导航 | 自动寻找下一房间 | 找门率 > 85% |
| **逻辑** | 卡死检测 | 位置无变化 5 秒触发脱困 | 脱困率 > 60% |
| **执行** | 技能连招 | A/S 技能释放 | 成功率 > 75% |
| **执行** | 随机延迟 | 拟人化操作 | 延迟 50-150ms |
| **安全** | 内存保护 | 无内存泄漏 | 10 分钟无 OOM |

#### P2 功能 (可选优化)

| 模块 | 功能 | 描述 | 优先级原因 |
|------|------|------|------------|
| **视觉** | Boss 特殊识别 | 识别 Boss 类型 | 场景少见 |
| **视觉** | 小地图定位 | 解析小地图 | 非核心 |
| **逻辑** | 高级寻路 | A* 算法避障 | 洛兰地形简单 |
| **逻辑** | 团队模式 | 多人协作 | 单人为主 |
| **执行** | 鼠标模拟 | 鼠标点击 | 仅键盘足够 |
| **UI** | 调试界面 | 实时可视化 | 非用户需求 |

### 3.3 MVP 功能范围

**3 天 MVP 必须包含**:
- ✅ P0 所有功能（10 项）
- ⚠️ P1 部分: HP/MP 读取、门识别、自动拾取

**7 天完整版包含**:
- ✅ P0 所有功能
- ✅ P1 所有功能
- ❌ P2 暂不实现（后续迭代）

---

## 5. 开发者角色分工 (Developer Role Assignment)

### 5.1 角色定义

#### haneball17 - **系统架构与逻辑工程师**

**主要职责**:
- 项目整体架构设计
- 核心业务逻辑开发
- 视觉模块架构（CaptureEngine, StateReader）
- 系统集成与优化

**技能要求**:
- 熟悉 Python 面向对象编程
- 理解有限状态机 (FSM)
- 熟悉系统架构设计模式
- 了解计算机视觉基础

**负责模块**:
- ConfigLoader
- CaptureEngine
- MockYoloDetector / YoloDetector（集成）
- StateReader
- 主循环与系统集成

#### yangmq17 - **系统架构与逻辑工程师**

**主要职责**:
- 输入驱动开发
- 业务逻辑实现 (BotFSM, PathPlanner)
- 坐标映射与世界模型
- 测试与调试

**技能要求**:
- 熟悉 Python 面向对象编程
- 理解有限状态机 (FSM)
- 了解 Windows API
- 熟悉游戏逻辑与坐标系

**负责模块**:
- InputDriver
- BotFSM（状态机核心）
- PathPlanner（Y 轴对齐、寻路）
- CoordinateMapper
- WorldModel

### 5.2 详细任务分工表

#### Day 1-2: 基础建设期

| 时间 | haneball17 任务 | yangmq17 任务 | 协作点 |
|------|----------------|---------------|--------|
| Day 1 上午 | 项目结构创建 + 环境搭建 | 定义数据类型 (core/types.py) | 共同定义接口 |
| Day 1 下午 | 实现 ConfigLoader | 实现 CaptureEngine | 接口联调 |
| Day 1 晚上 | 实现 MockYoloDetector | 实现 InputDriver | Mock 测试 |
| Day 2 上午 | 实现 StateReader | 实现 BotFSM 基础版 | 状态定义 |
| Day 2 下午 | 实现 CoordinateMapper | 实现 PathPlanner | 坐标系对齐 |
| Day 2 晚上 | 实现 WorldModel | 集成 FSM + PathPlanner | 逻辑测试 |

#### Day 3-4: 核心开发期

| 时间 | haneball17 任务 | yangmq17 任务 | 协作点 |
|------|----------------|---------------|--------|
| Day 3 上午 | 完善所有视觉模块 | 实现拾取逻辑 | 接口对接 |
| Day 3 下午 | 实现主循环框架 | 实现房间导航 | 流程测试 |
| Day 3 晚上 | 集成测试 (Mock 版) | 调试状态机转换 | 代码合并 |
| Day 4 上午 | **集成 YOLO 模型**（如完成） | 实现安全机制 (F12) | 模型替换 |
| Day 4 下午 | 性能优化 (FPS) | 优化移动平滑度 | 联合调试 |
| Day 4 晚上 | 编写单元测试 | 编写集成测试 | 交叉测试 |

#### Day 5-7: 集成与优化期

| 时间 | haneball17 任务 | yangmq17 任务 | 协作点 |
|------|----------------|---------------|--------|
| Day 5 上午 | 系统集成 | **MVP 完整测试** | 两人共同测试 |
| Day 5 下午 | 性能分析与优化 | Bug 修复 | 联合调试 |
| Day 5 晚上 | 编写技术文档 | 编写用户手册 | 文档审核 |
| Day 6 上午 | 实现技能 CD 检测 | 实现技能连招 | 技能测试 |
| Day 6 下午 | **完整功能测试** | **完整功能测试** | 10 局测试 |
| Day 6 晚上 | 优化检测阈值 | 优化 FSM 参数 | 调整参数 |
| Day 7 上午 | E2E 测试 (真实) | E2E 测试 (真实) | 洛兰通关 |
| Day 7 下午 | 最终代码审查 | 文档完善 | 项目交付 |

**说明**: YOLO 训练工作由任何人独立执行，不占用开发时间

### 5.3 模块分配表

| 模块 | 负责人 | 优先级 | 复杂度 | 预计时间 |
|------|--------|--------|--------|----------|
| **ConfigLoader** | haneball17 | P0 | 低 | 1h |
| **CaptureEngine** | haneball17 | P0 | 中 | 3h |
| **MockYoloDetector** | haneball17 | P0 | 低 | 2h |
| **YoloDetector** | haneball17 | P0 | 低 | 2h |
| **StateReader** | haneball17 | P1 | 中 | 4h |
| **CoordinateMapper** | haneball17 | P0 | 中 | 3h |
| **WorldModel** | haneball17 | P0 | 中 | 3h |
| **主循环** | haneball17 | P0 | 高 | 4h |
| **InputDriver** | yangmq17 | P0 | 中 | 4h |
| **BotFSM** | yangmq17 | P0 | 高 | 8h |
| **PathPlanner** | yangmq17 | P0 | 高 | 6h |
| **技能管理** | yangmq17 | P1 | 中 | 4h |
| **安全机制** | yangmq17 | P0 | 低 | 2h |

### 5.4 每日协作机制

#### 早晨站会 (Daily Standup)
- **时间**: 每天上午 10:00
- **时长**: 15 分钟
- **内容**:
  - 昨天完成了什么
  - 今天计划做什么
  - 遇到什么阻塞

#### 代码合并 (Code Merge)
- **频率**: 每天晚上 8:00
- **方式**: Git merge 到 develop 分支
- **要求**:
  - 代码必须通过单元测试
  - 必须更新相关文档
  - 解决所有冲突

#### 接口变更 (API Change)
- **规则**: 修改接口必须提前通知对方
- **流程**:
  1. 在群内发布变更通知
  2. 说明影响范围
  3. 等待对方确认后再修改
  4. 更新接口文档

---

## 6. Mock/Stub 开发策略 (Mock/Stub Strategy)

### 6.1 策略概述

**核心思想**: 在 YOLO 模型训练完成前，使用 Mock/Stub 对象确保系统可以正常开发和测试。

**优势**:
- ✅ 开发进度不受 YOLO 训练影响
- ✅ 所有模块可以独立开发和测试
- ✅ 模型完成后一行代码切换
- ✅ 便于单元测试和调试

### 6.2 MockYoloDetector 实现

**接口定义**:
```python
# vision/detector_interface.py
from abc import ABC, abstractmethod
from core.types import GameObject, BoundingBox

class IDetector(ABC):
    @abstractmethod
    def detect(self, image: np.ndarray) -> List[GameObject]:
        """检测图像中的游戏对象"""
        pass
```

**Mock 实现**:
```python
# vision/mock_yolo_detector.py
import numpy as np
from core.types import GameObject, BoundingBox, ObjectType
from vision.detector_interface import IDetector

class MockYoloDetector(IDetector):
    """YOLO 检测器的 Mock 实现，用于开发和测试"""

    def __init__(self):
        self.frame_count = 0

    def detect(self, image: np.ndarray) -> List[GameObject]:
        """
        返回模拟的检测结果

        模拟逻辑:
        - 返回 1-3 个随机位置的怪物
        - 返回 1 个固定位置的玩家
        - 坐标在合理范围内随机
        """
        self.frame_count += 1
        height, width = image.shape[:2]

        objects = []

        # 模拟玩家（固定在画面中心偏下）
        player = GameObject(
            id="hero_1",
            type=ObjectType.HERO,
            bbox=BoundingBox(
                x=width // 2 - 30,
                y=height - 150,
                width=60,
                height=100
            ),
            confidence=1.0
        )
        objects.append(player)

        # 模拟怪物（随机位置）
        import random
        num_monsters = random.randint(1, 3)
        for i in range(num_monsters):
            monster = GameObject(
                id=f"monster_{i}",
                type=ObjectType.MONSTER,
                bbox=BoundingBox(
                    x=random.randint(50, width - 100),
                    y=random.randint(100, height - 200),
                    width=50,
                    height=80
                ),
                confidence=0.85 + random.random() * 0.14
            )
            objects.append(monster)

        return objects
```

**真实实现**:
```python
# vision/yolo_detector.py
from ultralytics import YOLO
from core.types import GameObject, BoundingBox, ObjectType
from vision.detector_interface import IDetector

class YoloDetector(IDetector):
    """YOLO 检测器的真实实现"""

    def __init__(self, model_path: str = "models/yolov8n_dnf.pt"):
        self.model = YOLO(model_path)
        self.class_mapping = {
            0: ObjectType.MONSTER,
            1: ObjectType.HERO,
            2: ObjectType.ITEM,
            3: ObjectType.GATE
        }

    def detect(self, image: np.ndarray) -> List[GameObject]:
        """使用 YOLO 模型检测"""
        results = self.model(image, verbose=False)[0]

        objects = []
        for box in results.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            obj = GameObject(
                id=f"{self.class_mapping[class_id].name}_{len(objects)}",
                type=self.class_mapping[class_id],
                bbox=BoundingBox(
                    x=float(x1),
                    y=float(y1),
                    width=float(x2 - x1),
                    height=float(y2 - y1)
                ),
                confidence=confidence
            )
            objects.append(obj)

        return objects
```

### 6.3 使用方式

**开发期间**:
```python
# config.yaml
detector:
  type: "mock"  # 使用 MockYoloDetector
```

**模型完成后**:
```python
# config.yaml
detector:
  type: "yolo"  # 使用 YoloDetector
  model_path: "models/yolov8n_dnf.pt"
```

**工厂模式创建**:
```python
# vision/detector_factory.py
def create_detector(config: dict) -> IDetector:
    detector_type = config.get("type", "mock")

    if detector_type == "mock":
        return MockYoloDetector()
    elif detector_type == "yolo":
        model_path = config.get("model_path", "models/yolov8n_dnf.pt")
        return YoloDetector(model_path)
    else:
        raise ValueError(f"Unknown detector type: {detector_type}")
```

### 6.4 切换流程

**从 Mock 切换到真实 YOLO**:

1. **确保模型文件存在**:
   ```bash
   ls models/yolov8n_dnf.pt
   ```

2. **修改配置文件**:
   ```yaml
   # config.yaml
   detector:
     type: "yolo"  # 改为 yolo
     model_path: "models/yolov8n_dnf.pt"
   ```

3. **验证切换成功**:
   ```bash
   python main.py --test-detector
   ```

4. **如遇问题，回退到 Mock**:
   ```yaml
   # config.yaml
   detector:
     type: "mock"  # 改回 mock
   ```

**无需修改其他代码**！所有使用 `IDetector` 接口的模块自动切换。

### 6.5 其他 Mock 对象

#### MockStateReader
```python
class MockStateReader:
    def read_hp(self, image: np.ndarray) -> float:
        """返回模拟 HP 值（80-100%）"""
        return 80 + random.random() * 20

    def read_mp(self, image: np.ndarray) -> float:
        """返回模拟 MP 值（50-100%）"""
        return 50 + random.random() * 50
```

#### MockInputDriver
```python
class MockInputDriver:
    def press_key(self, key: str):
        """模拟按键（仅打印日志）"""
        print(f"[Mock] 按键: {key}")

    def move(self, direction: str, duration: float):
        """模拟移动（仅打印日志）"""
        print(f"[Mock] 移动: {direction}, 持续: {duration}s")
```

### 6.6 测试策略

**单元测试**: 使用 Mock 对象
```python
def test_botfsm():
    detector = MockYoloDetector()
    fsm = BotFSM()

    # 使用 Mock 检测器测试 FSM 逻辑
    context = detector.detect(test_image)
    command = fsm.update(context)
    assert command is not None
```

**集成测试**: 可选使用真实 YOLO
```python
def test_integration():
    # 使用 Mock 测试
    detector = MockYoloDetector()
    # 或使用真实 YOLO 测试
    # detector = YoloDetector("models/yolov8n_dnf.pt")

    fsm = BotFSM()
    input_driver = InputDriver()

    # 完整流程测试
    context = detector.detect(frame)
    command = fsm.update(context)
    input_driver.execute(command)
```

---

## 7. Day-by-Day 开发计划 (Day-by-Day Schedule)

### Day 1: 环境准备与基础框架 (2026-02-11)

#### 上午 (09:00 - 12:00)

**haneball17 任务**:
- [x] 创建项目目录结构
- [x] 安装 Python 依赖 (requirements.txt)
- [x] 实现 `ConfigLoader` 基础版
- [x] 定义接口 (IDetector, IStateReader)

**yangmq17 任务**:
- [x] 定义 `core/types.py` 数据类型
- [x] 实现 `GameObject`, `GameContext`, `Command` 等核心类
- [x] 编写项目 README

**共同任务**:
- [x] 确定检测类别定义 (monster, hero, item, gate)
- [x] 接口评审与确认

#### 下午 (14:00 - 18:00)

**haneball17 任务**:
- [x] 实现 `CaptureEngine` (使用 MSS)
- [x] 测试截图性能 (目标: FPS ≥ 30)
- [x] 实现 `MockYoloDetector`
- [x] 编写检测器单元测试

**yangmq17 任务**:
- [x] 实现 `InputDriver` (使用 pydirectinput)
- [x] 在记事本中测试按键输入
- [x] 实现 `MockInputDriver`
- [x] 编写输入驱动单元测试

**协作点**:
- 两人共同测试 CaptureEngine 和 InputDriver 的集成

#### 晚上 (19:00 - 22:00)

**haneball17 任务**:
- [x] 实现 `MockStateReader`
- [x] 实现 `CoordinateMapper` 基础版
- [x] 编写视觉模块集成测试

**yangmq17 任务**:
- [x] 实现 `BotFSM` 基础框架
- [x] 实现状态转换逻辑
- [x] 编写状态机单元测试

**交付物**:
- haneball17: 视觉模块基础框架完成
- yangmq17: 输入模块与状态机基础完成

**注**: YOLO 数据采集可由任何人并行进行，不占用开发时间

---

### Day 2: 核心模块开发 (2026-02-12)

#### 上午 (09:00 - 12:00)

**haneball17 任务**:
- [x] 实现 `StateReader` (HP/MP 颜色识别)
- [x] 测试 HP/MP 读取准确率
- [x] 优化颜色阈值算法

**yangmq17 任务**:
- [x] 实现 `PathPlanner` (Y 轴对齐逻辑)
- [x] 实现战斗策略模块
- [x] 单元测试: Y 轴对齐算法

**协作点**:
- haneball17 提供检测接口给 yangmq17

#### 下午 (14:00 - 18:00)

**haneball17 任务**:
- [x] 完善 `CoordinateMapper`
- [x] 实现 `WorldModel` (上下文维护)
- [x] 集成视觉模块

**yangmq17 任务**:
- [x] 完善 `BotFSM` 所有状态
- [x] 实现 Idle/Combat/Loot/Navigate 状态
- [x] 集成 FSM + PathPlanner

**协作点**:
- 视觉模块与逻辑模块接口联调

#### 晚上 (19:00 - 22:00)

**haneball17 任务**:
- [x] 编写视觉模块集成测试
- [x] 测试完整检测流程
- [x] 性能测试 (FPS, 延迟)

**yangmq17 任务**:
- [x] 编写逻辑模块集成测试
- [x] 测试状态机完整流转
- [x] 模拟完整游戏流程

**交付物**:
- haneball17: 视觉模块完成，集成测试通过
- yangmq17: 核心逻辑模块完成，状态机测试通过

**注**: YOLO 数据标注和训练可并行进行，不阻塞开发

---

### Day 3: 业务逻辑与系统集成 (2026-02-13)

#### 上午 (09:00 - 12:00)

**haneball17 任务**:
- [x] 实现主循环框架
- [x] 集成所有视觉模块
- [x] 实现模块调度逻辑

**yangmq17 任务**:
- [x] 实现拾取逻辑 (Loot 状态)
- [x] 实现房间导航逻辑 (Navigate 状态)
- [x] 测试完整状态机流转

**协作点**:
- 视觉模块与逻辑模块完整集成

#### 下午 (14:00 - 18:00)

**haneball17 任务**:
- [x] 实现 `YoloDetector` 类（支持模型切换）
- [x] 如果 YOLO 模型完成，进行集成
- [x] 否则继续使用 MockYoloDetector
- [x] 性能测试与优化

**yangmq17 任务**:
- [x] 实现安全机制 (F12 熔断)
- [x] 实现卡死检测
- [x] 添加随机延迟（反检测）

**协作点**:
- 完整系统集成测试

#### 晚上 (19:00 - 22:00)

**haneball17 任务**:
- [x] 编写单元测试
- [x] 测试覆盖率 > 70%
- [x] 性能分析 (FPS, 延迟)

**yangmq17 任务**:
- [x] 编写集成测试
- [x] 模拟完整游戏流程测试
- [x] 调试与优化

**交付物**:
- haneball17: 主循环与集成完成
- yangmq17: 所有逻辑功能完成

**里程碑**:
- 🎯 Day 3 结束: 所有核心功能开发完成

**注**: 如 YOLO 模型完成，可尝试集成；否则继续使用 Mock

---

### Day 4: 系统集成与优化 (2026-02-14)

#### 上午 (09:00 - 12:00)

**haneball17 任务**:
- [x] **关键**: 如果 YOLO 模型完成，切换到真实 YoloDetector
- [x] 测试模型检测性能 (mAP, 准确率)
- [x] 调整置信度阈值 (0.6 → 0.7?)
- [x] 否则优化 MockYoloDetector

**yangmq17 任务**:
- [x] 系统集成测试
- [x] 完整流程测试 (修炼场 + 洛兰)
- [x] Bug 修复与调优

**协作点**:
- **首次完整集成测试**: 两人共同测试

#### 下午 (14:00 - 18:00)

**haneball17 任务**:
- [x] 性能优化 (FPS ≥ 30)
- [x] 优化检测算法
- [x] 内存泄漏检查

**yangmq17 任务**:
- [x] 优化移动平滑度
- [x] 优化攻击节奏
- [x] 调整状态机参数

**协作点**:
- 联合调试，解决集成问题

#### 晚上 (19:00 - 22:00)

**haneball17 任务**:
- [x] 编写技术文档
- [x] 编写单元测试
- [x] 代码审查

**yangmq17 任务**:
- [x] 编写集成测试用例
- [x] 编写用户手册
- [x] 准备演示材料

**交付物**:
- **MVP v1.0 完成**
- 集成测试通过

**里程碑**:
- 🎯 Day 4 结束: **MVP 核心功能完成** (可进行内部测试)

---

### Day 5: MVP 测试与验收 (2026-02-15)

#### 上午 (09:00 - 12:00)

**haneball17 + yangmq17 共同任务**:
- [x] **MVP 完整测试**
- [x] 场景 1: 修炼场基础移动
- [x] 场景 2: 洛兰单房间战斗
- [x] 场景 3: 完整流程 (3 个房间)

**验收标准**:
- ✅ 修炼场移动正常
- ✅ 能检测到怪物 (> 80%)
- ✅ Y 轴对齐有效 (> 85%)
- ✅ 能自动攻击

#### 下午 (14:00 - 18:00)

**haneball17 任务**:
- [x] 优化检测性能
- [x] 调整检测阈值
- [x] 性能分析

**yangmq17 任务**:
- [x] 优化状态机逻辑
- [x] 优化移动平滑度
- [x] 调整攻击节奏

**协作点**:
- 根据测试结果调整参数

#### 晚上 (19:00 - 22:00)

**haneball17 + yangmq17 共同任务**:
- [x] Bug 修复
- [x] 性能优化 (FPS ≥ 30)
- [x] 编写测试报告

**交付物**:
- **MVP v1.0 交付**
- 集成测试通过 (≥ 5 个场景)

**里程碑**:
- 🎯 **Day 5 结束: MVP 交付** (满足基本需求)

**注**: 此时 YOLO 模型可能仍在训练或刚完成，均可验收

---

### Day 6: 完善功能与稳定性 (2026-02-16)

#### 上午 (09:00 - 12:00)

**haneball17 任务**:
- [x] 实现技能 CD 检测
- [x] 测试技能识别准确率
- [x] 集成到状态机

**yangmq17 任务**:
- [x] 实现技能连招逻辑
- [x] 实现 A/S 技能释放
- [x] 测试技能释放成功率

**协作点**:
- 联调: 技能 CD 检测 + 技能连招

#### 下午 (14:00 - 18:00)

**haneball17 任务**:
- [x] 如果 YOLO 完成，训练 Gate 类别
- [x] 测试门/传送阵检测
- [x] 优化检测准确率

**yangmq17 任务**:
- [x] 实现自动拾取功能
- [x] 优化拾取路径规划
- [x] 测试拾取成功率

**协作点**:
- 联调: 战斗 → 拾取 → 寻找门

#### 晚上 (19:00 - 22:00)

**haneball17 + yangmq17 共同任务**:
- [x] 稳定性测试 (连续运行 10 局)
- [x] 内存泄漏检测
- [x] 异常处理测试
- [x] 边界场景测试

**交付物**:
- P1 功能全部完成
- 稳定性测试报告

**里程碑**:
- 🎯 Day 6 结束: 完整版功能完成

---

### Day 7: 最终测试与交付 (2026-02-17)

#### 上午 (09:00 - 12:00)

**haneball17 + yangmq17 共同任务**:
- [x] **E2E 真机测试**
- [x] 洛兰完整通关 (10 局)
- [x] 性能指标验证
- [x] 成功率统计

**验收指标**:
- ✅ 通关率 > 80% (8/10)
- ✅ 平均时长 < 3 分钟
- ✅ FPS ≥ 30
- ✅ 无崩溃

#### 下午 (14:00 - 18:00)

**haneball17 任务**:
- [x] 编写技术文档
- [x] 模型使用说明（如有真实模型）
- [x] 性能优化报告

**yangmq17 任务**:
- [x] 编写用户手册
- [x] 配置文件说明
- [x] 常见问题 FAQ

**协作点**:
- 共同审核文档

#### 晚上 (19:00 - 22:00)

**haneball17 + yangmq17 共同任务**:
- [x] 最终代码审查
- [x] 最终测试验收
- [x] 准备演示材料
- [x] 项目总结

**交付物**:
- ✅ 完整系统 (源代码)
- ✅ 技术文档
- ✅ 用户手册
- ✅ 测试报告
- ✅ 演示视频

**里程碑**:
- 🎉 **Day 7 结束: 项目交付完成**

**注**: 如 YOLO 模型已完成，包含模型文件；否则说明使用 Mock 或 COCO 方案

---

## 8. MVP 定义 (MVP Definition)

### 6.1 MVP 核心目标

**3 天内实现一个可工作的最小可行产品，能够:**
1. 检测游戏中的怪物和玩家
2. 自动移动并对齐怪物
3. 自动攻击
4. 清空房间后寻找门

### 6.2 MVP 功能矩阵

| 功能模块 | 必需 | MVP 实现方案 | 完整版方案 |
|----------|------|--------------|------------|
| **目标检测** | ✅ | 自训练 YOLO 或 COCO 预训练 | 优化 YOLO |
| **玩家检测** | ✅ | YOLO 检测 | YOLO + 跟踪算法 |
| **Y 轴对齐** | ✅ | 基础对齐 (±15px) | 精细化对齐 (±5px) |
| **索敌逻辑** | ✅ | 最近目标 | 最近 + 优先级算法 |
| **攻击逻辑** | ✅ | 简单 X 键攻击 | 技能连招 |
| **房间导航** | ✅ | 简单寻找门 | A* 寻路 + 避障 |
| **状态读取** | ❌ | Mock 数据 | HP/MP 真实读取 |
| **自动拾取** | ❌ | 不实现 | 自动拾取 |
| **技能管理** | ❌ | 不实现 | 技能 CD 检测 |
| **调试界面** | ❌ | 控制台日志 | 可视化蒙版 |

### 6.3 MVP 验收标准

#### 功能验收

- [x] 能检测怪物 (检测率 > 80%)
- [x] 能检测玩家 (检测率 > 85%)
- [x] 能自动移动 (响应延迟 < 100ms)
- [x] 能 Y 轴对齐 (误差 < 15 像素)
- [x] 能自动攻击 (命中率 > 70%)
- [x] 能找到门 (找门率 > 70%)
- [x] 能连续通关 2 个房间 (不卡死)

#### 性能验收

- [x] FPS ≥ 25 (可接受，MVP 阶段)
- [x] YOLO 推理 < 50ms (可接受)
- [x] 端到端延迟 < 200ms (可接受)
- [x] CPU 占用 < 50%
- [x] 显存占用 < 2GB

#### 稳定性验收

- [x] 连续运行 5 分钟不崩溃
- [x] F12 熔断有效
- [x] 无明显内存泄漏

### 6.4 MVP 技术债务

**MVP 阶段可接受的技术债务**:
1. 使用 COCO 预训练模型 (如果自训练失败)
2. 硬编码部分配置 (未完全抽象到 ConfigLoader)
3. 缺少单元测试 (可后续补充)
4. 日志简单 (可后续优化)
5. 异常处理不完整 (仅捕获关键异常)

**Day 4-7 需偿还的技术债务**:
1. 切换到自训练 YOLO 模型
2. 完善配置系统
3. 补充单元测试 (覆盖率 > 70%)
4. 完善日志系统
5. 完善异常处理

---

## 9. 并行化策略 (Parallelization Strategy)

### 9.1 并行化时间线图

```
时间轴 (Day 1-7)

haneball17 (架构/逻辑工程师):
[框架] [Config] [Capture] [Mock] [State] [主循环] [优化] [文档]
    ▲     ▲       ▲        ▲      ▲      ▲      ▲      ▲
    └─────┴───────┴────────┴──────┴──────┴──────┴──────┘
        可完全并行

yangmq17 (架构/逻辑工程师):
[类型] [Input] [FSM] [Path] [逻辑] [集成] [测试] [手册]
    ▲     ▲      ▲      ▲      ▲      ▲      ▲      ▲
    └─────┴──────┴──────┴──────┴──────┴──────┴──────┘
        可完全并行

YOLO 训练专项（独立并行）:
[数据采集] [标注] [训练] [验证]
    ▲        ▲      ▲      ▲
    └────────┴──────┴──────┴─ 不阻塞开发

协作点:
- Day 1: 共同定义接口 (30分钟)
- Day 2: 接口联调 (1小时)
- Day 3: 模块集成 (2小时)
- Day 4: 完整集成测试 (2小时)
- Day 5: 共同测试 MVP (4小时)
- Day 7: 最终验收 (4小时)
```

### 7.2 最大化并行化的关键原则

#### 原则 1: 接口先行 (Interface First)

**策略**:
- Day 1 上午共同定义所有接口 (`core/types.py`)
- 一旦接口确定，双方完全独立开发
- 使用 Mock 模块测试接口

**示例**:
```python
# Day 1 上午定义接口
class IDetector:
    def detect(self, image: np.ndarray) -> List[GameObject]:
        pass

# haneball17 实现 MockYoloDetector (Day 1 完成)
# yangmq17 使用 Mock 开发 BotFSM (不被阻塞)
# 任何人训练 YOLO (Day 3-4 完成)
# 一行切换: detector = YoloDetector("models/yolov8n_dnf.pt")
```

#### 原则 2: 接口并行 (Interface Parallelism)

**策略**:
- 使用 Mock 对象实现接口
- 所有模块可以独立开发和测试
- 不需要等待 YOLO 训练完成

**执行**:
- haneball17 和 yangmq17 各自负责独立模块
- 使用 MockYoloDetector, MockStateReader 等
- 只在需要时才集成真实模块

#### 原则 3: 独立训练 (Independent Training)

**策略**:
- YOLO 训练完全独立于 MVP 开发
- 可由任何人执行（包括非开发人员）
- 使用 Mock 确保开发不受影响

**执行**:
- 开发期间使用 MockYoloDetector
- 训练完成后一行切换到 YoloDetector
- 如训练失败，使用 COCO 预训练模型

**降级接口**:
```python
class YoloDetector:
    def __init__(self, model_path: str = None, use_coco: bool = False):
        if model_path and os.path.exists(model_path):
            self.model = YOLO(model_path)  # 自训练
        elif use_coco:
            self.model = YOLO("yolov8n.pt")  # COCO 预训练
        else:
            raise ValueError("No model available")
```

#### 原则 4: 每日集成 (Daily Integration)

**策略**:
- 每天晚上 8:00 合并代码到 develop 分支
- 避免长期分支导致的冲突
- 提前发现接口不兼容问题

**流程**:
```bash
# 每天晚上执行
git checkout develop
git pull origin develop
git merge feature/vision  # Dev A
git merge feature/logic   # Dev B
# 解决冲突
git push origin develop
```

### 7.3 通信机制

#### 同步沟通
- **频率**: 每天 3 次 (上午 10:00, 下午 15:00, 晚上 20:00)
- **时长**: 每次 10-15 分钟
- **内容**: 进度同步、阻塞问题、接口变更

#### 异步沟通
- **工具**: 群聊 / GitHub Issues
- **规则**: 接口变更必须提前 24 小时通知
- **响应**: 工作时间内 1 小时内回复

#### 文档共享
- **位置**: `docs/` 目录
- **更新**: 每次接口变更后立即更新
- **格式**: Markdown + 代码示例

---

## 10. 风险缓解方案 (Risk Mitigation)

### 8.1 风险识别矩阵

| 风险 | 概率 | 影响 | 风险等级 | 缓解措施 |
|------|------|------|----------|----------|
| **YOLO 训练失败** | 低 | 中 | 🟢 低 | Mock + COCO 降级方案 |
| **YOLO 训练超时** | 低 | 低 | 🟢 低 | 已分离，不阻塞开发 |
| **检测精度不足** | 中 | 中 | 🟡 中 | 使用 COCO 或继续优化 |
| **集成困难** | 低 | 高 | 🟡 中 | Mock 测试 + 接口先行 |
| **性能不达标** | 中 | 低 | 🟢 低 | FP16 + TensorRT |
| **时间不够** | 中 | 中 | 🟡 中 | 砍掉 P2 功能 |
| **一人病假** | 低 | 高 | 🟡 中 | 交叉培训 + 文档完善 |
| **测试环境问题** | 低 | 中 | 🟢 低 | 使用单机版 + Mock |

### 10.2 高风险应对方案

#### 风险 1: YOLO 训练未完成或效果不佳

**触发条件**:
- Day 4 结束时训练仍未完成
- 训练完成但 mAP < 60%

**应对措施**:
```
方案 A (推荐): 继续使用 MockYoloDetector
- 优点: 不阻塞开发和验收
- 缺点: 无法在真实环境测试
- 适用: MVP 阶段

方案 B (备选): COCO 预训练模型降级
- 优点: 立即可用，准确率可接受 (60-70%)
- 缺点: 无法检测物品、门
- 适用: 需要真实检测时

方案 C (最后): 迁移学习
- 使用 COCO 预训练权重
- 用少量 DNF 数据微调 (100-200 张)
- 训练时间: 2-4 小时
- 适用: 有时间补充训练时
```

**决策树**:
```
Day 4 上午: 检查 YOLO 训练状态
├─ 训练完成且 mAP > 70% ✅ → 使用 YoloDetector
├─ 训练完成但 60% < mAP < 70% ⚠️ → 方案 B 或 C
├─ 训练未完成或 mAP < 60% ❌ → 方案 A (继续用 Mock)
└─ 完全没有训练 → 方案 A (继续用 Mock)
```

#### 风险 2: 集成困难

**原因**:
- 接口不兼容
- 数据格式不一致
- 性能瓶颈

**缓解措施**:
1. **Day 1 定义接口**: 强制使用 `core/types.py`
2. **Mock 测试**: Day 1-3 使用 Mock 完成集成测试
3. **渐进式集成**:
   - Day 1-2: 模块独立开发
   - Day 3: 视觉 + 逻辑 (Mock Input)
   - Day 4: 完整集成

**集成检查点**:
```python
# Day 3 集成测试
def test_vision_to_logic():
    detector = MockYoloDetector()
    fsm = BotFSM()
    # 验证接口兼容性
    ctx = detector.detect(frame)
    cmd = fsm.update(ctx)
    assert cmd is not None
```

#### 风险 3: 时间不够

**原因**:
- 接口不兼容
- 数据格式不一致
- 性能瓶颈

**缓解措施**:
1. **Day 1 定义接口**: 强制使用 `core/types.py`
2. **Mock 测试**: Day 2-3 使用 Mock 完成集成测试
3. **渐进式集成**:
   - Day 4: 视觉 + 逻辑 (Mock Input)
   - Day 5: 视觉 + 逻辑 + 输入
   - Day 6: 完整集成

**集成检查点**:
```python
# Day 4 集成测试
def test_vision_to_logic():
    detector = YoloDetector("model.pt")
    fsm = BotFSM()
    # 验证接口兼容性
    ctx = detector.detect(frame)
    cmd = fsm.update(ctx)
    assert cmd is not None
```

#### 风险 4: 一人无法工作

**应对措施**:
1. **Day 1-3**: 两人任务相对独立，影响较小
2. **Day 4-7**: 需要两人协作时，远程协作或调整任务
3. **文档完善**: 确保代码可维护

**交叉培训**:
- 两人都熟悉系统架构和接口
- 两人都可以开发和调试所有模块
- 定期代码审查和知识共享

### 10.3 应急预案

#### 场景 1: Day 4 发现 YOLO 训练未完成

**立即行动**:
1. 继续使用 MockYoloDetector
2. 不阻塞开发进度
3. 继续进行系统集成和测试

**后续补救** (Day 5-7):
1. 等待训练完成
2. 一行代码切换到 YoloDetector
3. 或者使用 COCO 预训练模型

#### 场景 2: Day 5 发现性能不达标 (FPS < 20)

**优化措施**:
1. **YOLO 优化**:
   - FP16 推理 (速度提升 2 倍)
   - 减小输入分辨率 (640→416)
   - 使用 TensorRT (速度提升 3-5 倍)

2. **系统优化**:
   - 多线程分离推理和逻辑
   - 减少日志输出
   - 优化数据传输 (减少拷贝)

3. **降质量**:
   - 降低 FPS 目标 (25 → 20)
   - 增加延迟容忍度 (150ms → 200ms)

#### 场景 3: 集成发现接口不兼容

**立即行动**:
1. 停止新功能开发
2. 两人共同修复接口问题
3. 更新接口文档和测试

**后续补救**:
1. 回归测试确保修复有效
2. 补充单元测试
3. 防止类似问题再次发生

---

## 11. 每日里程碑与交接点 (Daily Milestones & Handoff Points)

### 9.1 每日里程碑清单

#### Day 1 里程碑: 基础框架
- [x] haneball17: ConfigLoader + CaptureEngine 完成
- [x] haneball17: MockYoloDetector 实现
- [x] yangmq17: 核心数据类型定义完成
- [x] yangmq17: InputDriver + BotFSM 基础完成
- [x] 共同: 接口定义与评审完成

**交接点**:
- 所有接口定义完成
- Mock 对象可用

#### Day 2 里程碑: 核心模块
- [x] haneball17: StateReader + CoordinateMapper 完成
- [x] haneball17: WorldModel 实现
- [x] yangmq17: PathPlanner + BotFSM 完成
- [x] yangmq17: 状态机所有状态实现
- [x] 共同: 视觉与逻辑模块完成

**交接点**:
- 核心模块可独立测试

#### Day 3 里程碑: 业务逻辑
- [x] haneball17: 主循环框架完成
- [x] haneball17: 所有视觉模块集成
- [x] yangmq17: 拾取 + 导航逻辑完成
- [x] yangmq17: 安全机制实现
- [x] 共同: 核心功能开发完成

**交接点**:
- 所有业务逻辑实现完成

#### Day 4 里程碑: 系统集成
- [x] haneball17: **YOLO 集成**（如完成）
- [x] haneball17: 性能优化完成
- [x] yangmq17: 系统集成完成
- [x] yangmq17: Bug 修复与调优
- [x] 共同: **首次完整集成测试** ✅

**交接点**:
- 完整系统可用

#### Day 5 里程碑: MVP 交付
- [x] haneball17: 技术文档
- [x] yangmq17: 用户手册
- [x] 共同: **MVP 测试通过** ✅
- [x] 共同: 集成测试完成 (5+ 场景)

**交接点**:
- **MVP v1.0 交付** 🎉

#### Day 6 里程碑: 完整功能
- [x] haneball17: 技能 CD 检测 + 门检测
- [x] yangmq17: 技能连招 + 自动拾取
- [x] 共同: 稳定性测试通过 (10 局)

**交接点**:
- 完整版功能完成

#### Day 7 里程碑: 最终交付
- [x] haneball17: 技术文档完成
- [x] yangmq17: 用户手册完成
- [x] 共同: **E2E 测试通过** ✅
- [x] 共同: **项目最终交付** 🎉

**交接点**:
- 所有交付物完成

### 9.2 关键交接点 (Critical Handoffs)

#### 交接点 1: Day 1 上午 - 接口定义
**参与者**: haneball17 + yangmq17
**时间**: 09:00 - 10:00 (1 小时)
**产出**: `core/types.py` 完整定义
**重要性**: ⭐⭐⭐ (最高)

**内容**:
```python
# 共同定义
class GameObject: ...
class GameContext: ...
class Command: ...
class CommandType(Enum): ...
```

#### 交接点 2: Day 2 晚上 - 模块完成
**参与者**: haneball17 + yangmq17
**时间**: 19:00 - 20:00 (1 小时)
**产出**: 视觉与逻辑模块完成
**重要性**: ⭐⭐⭐ (最高)

**检查清单**:
- [ ] 所有 Mock 类实现完成
- [ ] 接口测试通过
- [ ] 单元测试通过
- [ ] 模块可独立运行

#### 交接点 3: Day 3 下午 - 完整集成
**参与者**: haneball17 + yangmq17
**时间**: 14:00 - 16:00 (2 小时)
**产出**: 完整系统集成
**重要性**: ⭐⭐⭐ (最高)

**流程**:
1. 合并代码 (`develop` 分支)
2. 接口测试 (所有模块)
3. 完整流程测试 (Mock 环境)
4. 性能测试 (FPS, 延迟)
5. Bug 修复

#### 交接点 4: Day 4 上午 - YOLO 集成
**参与者**: haneball17 + yangmq17
**时间**: 09:00 - 12:00 (3 小时)
**产出**: YOLO 模型集成（如完成）
**重要性**: ⭐⭐⭐ (最高)

**流程**:
1. 检查 YOLO 模型是否完成
2. 如果完成，切换到 YoloDetector
3. 测试真实检测效果
4. 如有问题，回退到 Mock

#### 交接点 5: Day 5 上午 - MVP 测试
**参与者**: haneball17 + yangmq17
**时间**: 09:00 - 12:00 (3 小时)
**产出**: MVP 验收
**重要性**: ⭐⭐⭐ (最高)

**测试场景**:
1. 修炼场移动
2. 洛兰单房间战斗
3. 完整流程 (3 房间)
4. 性能指标验证

#### 交接点 6: Day 7 上午 - 最终验收
**参与者**: haneball17 + yangmq17
**时间**: 09:00 - 12:00 (3 小时)
**产出**: 项目交付
**重要性**: ⭐⭐⭐ (最高)

---

## 12. 测试与验收标准 (Testing & Acceptance)

### 10.1 测试层次

```
┌─────────────────────────────────────┐
│   E2E 测试 (真实游戏环境)            │  ← Day 7
│   洛兰通关测试 (10 局)               │
└─────────────────────────────────────┘
           ↑
┌─────────────────────────────────────┐
│   集成测试 (模块级)                  │  ← Day 4-6
│   Vision → Logic → Input            │
└─────────────────────────────────────┘
           ↑
┌─────────────────────────────────────┐
│   单元测试 (函数级)                  │  ← Day 2-5
│   每个 Mock 类独立测试               │
└─────────────────────────────────────┘
```

### 10.2 MVP 测试用例

#### 场景 1: 修炼场基础移动
**目标**: 验证输入驱动

**步骤**:
1. 进入修炼场
2. 启动 AradVision
3. 系统发送: 右键移动 2 秒
4. 系统发送: X 键攻击 5 次

**验收**:
- ✅ 角色向右移动
- ✅ 释放 5 次攻击

#### 场景 2: 洛兰单房间战斗
**目标**: 验证完整战斗流程

**步骤**:
1. 进入洛兰第 1 房
2. 启动系统
3. 自动检测怪物
4. Y 轴对齐
5. 自动攻击

**验收**:
- ✅ 怪物检测率 > 80%
- ✅ Y 轴对齐误差 < 15px
- ✅ 攻击命中率 > 70%
- ✅ 怪物死亡

#### 场景 3: 洛兰完整通关
**目标**: 验证完整自动化

**步骤**:
1. 洛兰入口开始
2. 依次通过 3 房
3. 击败所有怪物
4. 自动停止

**验收**:
- ✅ 通关时间 < 5 分钟
- ✅ 角色存活
- ✅ 无卡死 > 5 秒

### 10.3 性能验收指标

| 指标 | MVP 标准 | 完整版标准 | 测试方法 |
|------|----------|------------|----------|
| **FPS** | ≥ 25 | ≥ 30 | 统计 1 分钟 |
| **YOLO 延迟** | < 50ms | < 30ms | 计时测试 |
| **端到端延迟** | < 200ms | < 150ms | 时间戳差值 |
| **CPU 占用** | < 50% | < 40% | 任务管理器 |
| **显存占用** | < 2GB | < 2GB | nvidia-smi |
| **检测率** | > 80% | > 85% | 人工统计 |
| **误检率** | < 15% | < 10% | 人工统计 |

### 10.4 稳定性验收

#### 测试方法
- 连续运行 10 局洛兰副本
- 记录崩溃次数、卡死次数、通关率

#### 验收标准
- ✅ 成功率 ≥ 80% (8/10 局)
- ✅ 无程序崩溃
- ✅ 无内存泄漏 (10 分钟内存增长 < 100MB)
- ✅ 无严重卡死 (单次卡死 < 5 秒)

---

## 13. 时间线图表 (Timeline Diagrams)

### 11.1 甘特图 (Gantt Chart)

```
任务              haneball17     yangmq17      协作
─────────────────────────────────────────────────────
Day 1
  基础框架      ████
  ConfigLoader ██
  CaptureEngine ████
  核心类型                    ████
  Mock检测      ██
  InputDriver                 ████

Day 2
  StateReader   ████
  CoordMapper   ████
  WorldModel    ████
  BotFSM                      ████████
  PathPlanner                 ████████

Day 3
  主循环        ████
  视觉集成      ████
  拾取逻辑                    ████
  导航逻辑                    ████
  安全机制                    ████

Day 4
  YOLO集成      ████ (可选)
  性能优化      ████
  系统集成                    ██████
  Bug修复                      ████
  🔥 集成测试    ★★★★★ (2小时)

Day 5
  文档编写      ████
  系统优化                    ████
  🔥 MVP测试     ★★★★ (4小时)

Day 6
  技能CD检测    ████
  门检测        ████
  技能连招                    ████
  自动拾取                    ████
  稳定性测试     ★★★★★ (两人)

Day 7
  文档完善      ████
  🔥 最终验收    ★★★★★ (4小时)

YOLO训练（独立并行）:
───────────────────────────────────────
  数据采集      ████████ (任意时间)
  数据标注      ████████████ (任意时间)
  模型训练      ████████████ (任意时间)
  模型验证      ████ (任意时间)

图例:
██  工作
★   协作/测试
```

### 13.2 关键路径图

```
MVP 关键路径 (不可延误):
┌─────────────────────────────────────────────────────┐
│  Day 1   Day 2   Day 3   Day 4   Day 5               │
│                                                         │
│  [框架]→[模块]→[逻辑]→[集成]→[测试]                   │
│    4h    16h    16h     8h     4h                    │
│                                                         │
│  总计: 48 小时 (3 个工作日, 紧凑安排)                  │
└─────────────────────────────────────────────────────┘

YOLO 训练专项（独立并行）:
┌─────────────────────────────────────────────────────┐
│  Day 1   Day 2   Day 3   Day 4                       │
│                                                         │
│  [数据]→[标注]→[训练]→[验证]                          │
│    4h     8h    16h     4h                           │
│                                                         │
│  总计: 32 小时（可任意时间执行）                        │
│  集成点: Day 4 模型完成后切换                           │
└─────────────────────────────────────────────────────┘
```

### 13.3 资源分配图

```
haneball17 时间分配:
┌──────────────────────────────────┐
│ 基础框架:         6h (15%)      │
│ 视觉模块 (Capture/State): 10h (25%) │
│ 检测器 (Mock/Yolo): 4h (10%)    │
│ 主循环与集成:     8h (20%)      │
│ 测试与文档:       8h (20%)      │
│ 优化与调试:       4h (10%)      │
└──────────────────────────────────┘
总计: 40 小时

yangmq17 时间分配:
┌──────────────────────────────────┐
│ 核心类型定义:     2h (5%)       │
│ 输入驱动:         4h (10%)      │
│ 逻辑模块:        16h (40%)      │
│ 系统集成:         6h (15%)      │
│ 测试与文档:       8h (20%)      │
│ 优化与调试:       4h (10%)      │
└──────────────────────────────────┘
总计: 40 小时

协作时间:
┌──────────────────────────────────┐
│ 接口定义:         2h            │
│ 集成测试:         6h            │
│ MVP 验收:         4h            │
│ 最终验收:         4h            │
└──────────────────────────────────┘
总计: 16 小时

YOLO 训练专项（独立）:
┌──────────────────────────────────┐
│ 数据采集:         4h            │
│ 数据标注:         8h            │
│ 模型训练:        16h            │
│ 模型验证:         4h            │
└──────────────────────────────────┘
总计: 32 小时（不占用开发时间）

总体:
- haneball17: 40 小时 (5 天)
- yangmq17: 40 小时 (5 天)
- 协作: 16 小时 (2 天)
- YOLO训练: 32 小时（独立）
- 总计: 96 小时 (12 人天)
```

### 13.4 风险时间线

```
风险暴露期:
┌──────────┬───────────────────────────────────────┐
│ 低风险   │           Day 7                       │
├──────────┼───────────────────────────────────────┤
│ 中风险   │        Day 4-6                        │
├──────────┼───────────────────────────────────────┤
│ 高风险   │    Day 1-3                           │
│         │  (核心开发期)                         │
└──────────┴───────────────────────────────────────┘

关键决策点:
- Day 3 下午: 评估核心功能完成情况
  → 完成: 继续集成
  → 未完成: 调整优先级

- Day 4 上午: 检查 YOLO 训练状态
  → 完成: 集成 YoloDetector
  → 未完成: 继续使用 Mock

- Day 5 上午: MVP 验收
  → 通过: 继续 P1 功能
  → 失败: 调整优先级

- Day 7 上午: 最终验收
  → 通过: 交付
  → 失败: 协商延期或降级
```

---

## 14. 总结与建议 (Summary & Recommendations)

### 14.1 关键成功因素

1. **YOLO 训练独立化**
   - 已从 MVP 时间线完全分离
   - 不阻塞核心开发进度
   - 使用 Mock 确保系统可运行

2. **接口先行与 Mock 测试**
   - Day 1 定义所有接口
   - 使用 Mock 实现并行开发
   - 避免互相等待

3. **每日集成与快速迭代**
   - 每天晚上合并代码
   - 提前发现接口问题
   - 避免大规模冲突

4. **功能优先级管理**
   - MVP 只实现 P0 功能
   - P1/P2 功能根据时间灵活调整
   - 优先保证核心流程可用

### 14.2 如果时间不够 (应急方案)

**方案 1: 砍功能**
- 暂不实现: 自动拾取、技能管理、HP/MP 读取
- 只保留: 怪物检测（Mock）、Y 轴对齐、自动攻击

**方案 2: 降质量**
- FPS 目标: 30 → 20
- 检测率: 使用 Mock，不需要真实检测
- 误检率: 不适用

**方案 3: 延交付**
- 协商延期 2 天
- 优先交付 MVP (Day 5)
- 完整版 Day 9 交付

**方案 4: YOLO 延后**
- MVP 使用 MockYoloDetector
- 完整版再集成真实 YOLO 模型
- 不影响功能验收

### 14.3 最佳实践建议

1. **代码规范**
   - 使用 Black 格式化代码
   - 类型提示 (Type Hints)
   - Docstrings 遵循 Google Style

2. **版本管理**
   - 功能分支开发
   - 每日合并到 develop
   - 重要节点打 Tag

3. **文档先行**
   - 接口文档随代码更新
   - 重大决策记录在文档
   - Bug 修复补充到 FAQ

4. **健康与效率**
   - 每天工作 8-10 小时 (避免疲劳)
   - 定时休息 (番茄工作法)
   - 保持沟通渠道畅通

5. **YOLO 训练专项**
   - 可由任何人执行（包括非开发人员）
   - 优先级低于 MVP 开发
   - Day 4 前完成即可
   - 如无法完成，使用 Mock 或 COCO

---

## 附录 A: 工具与资源 (Tools & Resources)

### A.1 开发工具

| 工具 | 用途 | 版本 |
|------|------|------|
| Python | 编程语言 | 3.10+ |
| PyTorch | 深度学习框架 | 2.0+ |
| Ultralytics | YOLOv8 | 最新版 |
| OpenCV | 图像处理 | 4.x |
| MSS | 屏幕捕获 | 最新版 |
| PyDirectInput | 输入模拟 | 最新版 |
| pytest | 测试框架 | 7.x |
| Git | 版本控制 | 2.x |

### A.2 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | Intel i5-8400 | Intel i7-9700K |
| GPU | GTX 1060 6GB | RTX 3060 12GB |
| 内存 | 16GB | 32GB |
| 存储 | 20GB SSD | 50GB NVMe SSD |

### A.3 参考文档

- [Ultralytics YOLOv8 文档](https://docs.ultralytics.com/)
- [OpenCV Python 教程](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [PyDirectInput 文档](https://pypi.org/project/pydirectinput/)
- AradVision 项目文档 (`docs/` 目录)

---

## 附录 B: 术语表 (Glossary)

| 术语 | 全称 | 解释 |
|------|------|------|
| YOLO | You Only Look Once | 实时目标检测算法 |
| mAP | mean Average Precision | 目标检测精度指标 |
| NMS | Non-Maximum Suppression | 非极大值抑制 |
| FPS | Frames Per Second | 帧率 |
| FSM | Finite State Machine | 有限状态机 |
| MVP | Minimum Viable Product | 最小可行产品 |
| E2E | End-to-End | 端到端测试 |
| COCO | Common Objects in Context | 预训练数据集 |
| GPU | Graphics Processing Unit | 图形处理器 |
| API | Application Programming Interface | 应用程序接口 |

---

## 附录 C: 检查清单 (Checklists)

### C.1 Day 1 检查清单
- [ ] 项目目录结构创建
- [ ] `core/types.py` 定义完成
- [ ] `ConfigLoader` 实现
- [ ] `CaptureEngine` 截图 FPS ≥ 30
- [ ] `InputDriver` 记事本测试通过
- [ ] `MockYoloDetector` 实现
- [ ] `MockStateReader` 实现
- [ ] `MockInputDriver` 实现
- [ ] 接口测试通过
- [ ] 单元测试通过

### C.2 Day 2 检查清单
- [ ] `StateReader` HP/MP 读取完成
- [ ] `CoordinateMapper` 完成
- [ ] `WorldModel` 完成
- [ ] `BotFSM` 所有状态完成
- [ ] `PathPlanner` Y 轴对齐测试通过
- [ ] 视觉模块集成测试通过
- [ ] 逻辑模块集成测试通过

### C.3 Day 3 检查清单
- [ ] 主循环框架完成
- [ ] 所有视觉模块集成
- [ ] 拾取逻辑完成
- [ ] 导航逻辑完成
- [ ] 安全机制（F12 熔断）完成
- [ ] 卡死检测完成
- [ ] 完整流程测试通过

### C.4 Day 4 检查清单
- [ ] 如 YOLO 完成，集成测试通过
- [ ] 否则 Mock 继续正常工作
- [ ] 性能优化完成 (FPS ≥ 30)
- [ ] 系统集成完成
- [ ] Bug 修复
- [ ] **首次完整集成测试通过**
- [ ] 代码合并到 develop 分支

### C.5 Day 5 检查清单
- [ ] 修炼场移动测试通过
- [ ] 洛兰单房间测试通过
- [ ] 完整流程测试通过
- [ ] 性能指标达标
- [ ] 技术文档完成
- [ ] **MVP v1.0 交付**
- [ ] 集成测试通过 (5+ 场景)

### C.6 Day 6 检查清单
- [ ] 技能 CD 检测实现
- [ ] 技能连招实现
- [ ] 如 YOLO 完成，门/物品检测实现
- [ ] 自动拾取实现
- [ ] 稳定性测试通过 (10 局)
- [ ] 无明显 Bug
- [ ] 完整版功能完成

### C.7 Day 7 检查清单
- [ ] E2E 测试通过 (10 局, 成功率 > 80%)
- [ ] 性能指标全部达标
- [ ] 技术文档完成
- [ ] 用户手册完成
- [ ] 代码审查通过
- [ ] **项目最终交付**

### C.8 YOLO 训练专项检查清单（独立）
- [ ] 数据采集 500-1000 张
- [ ] 数据标注完成
- [ ] `data.yaml` 配置正确
- [ ] 训练脚本测试通过
- [ ] YOLO 训练启动
- [ ] 训练完成（50-100 epoch）
- [ ] 模型性能评估 (mAP > 70%)
- [ ] 模型文件导出 (`yolov8n_dnf.pt`)
- [ ] 模型集成测试通过

---

**文档版本**: V2.0
**最后更新**: 2026-02-10
**维护者**: haneball17, yangmq17
**审核状态**: ✅ 已审核

**变更记录**:
- 2026-02-10: V1.0 初版发布 (haneball17)
- 2026-02-10: V2.0 重大更新 - YOLO 训练独立化，更新开发人员信息
  - 将 YOLO 训练从 MVP 时间线中完全分离
  - 更新开发人员：haneball17 和 yangmq17 均为系统架构与逻辑工程师
  - 添加 YOLO 训练专项章节（Section 1）
  - 添加 Mock/Stub 开发策略章节（Section 6）
  - 更新所有 Day-by-Day 计划，移除 YOLO 训练任务
  - 更新开发者角色分工、模块分配表
  - 调整风险缓解方案和时间线图表
