# AradVision YOLO 训练专项指南

**项目名称**: AradVision - DNF 视觉辅助自动化系统
**文档标识**: ARAD-YOLO-008
**版本**: V1.0
**状态**: 正式版
**最后更新日期**: 2026-02-10

---

## 目录 (Table of Contents)

1. [概述](#1-概述overview)
2. [前置条件](#2-前置条件prerequisites)
3. [数据收集](#3-数据收集data-collection)
4. [数据标注](#4-数据标注data-labeling)
5. [训练流程](#5-训练流程training-process)
6. [模型评估](#6-模型评估model-evaluation)
7. [模型集成](#7-模型集成integration)
8. [降级策略](#8-降级策略fallback-strategy)
9. [与开发分离](#9-与开发分离separation-from-development)
10. [交付物](#10-交付物deliverables)

---

## 1. 概述 (Overview)

### 1.1 YOLO 训练的独立性

**重要说明**: YOLO 训练是一个完全独立的工作项,与主系统开发并行进行,互不阻塞。

```
主开发流程 (Dev B):
[框架] → [Capture] → [Input] → [FSM] → [集成]
    ↑___________独立进行,无需等待模型___________^

YOLO 训练流程 (Dev A 或任何人):
[数据采集] → [标注] → [训练] → [评估] → [交付]
    ↑___________完全独立,可并行进行___________^

交汇点:
Day 4: 交付训练好的模型文件 (.pt)
```

### 1.2 关键时间线

| 阶段 | 持续时间 | 说明 |
|------|----------|------|
| **数据采集** | 4-6 小时 | 自动截图收集 |
| **数据标注** | 8-12 小时 | 人工标注目标 |
| **模型训练** | 8-12 小时 | GPU 训练 (自动) |
| **模型评估** | 1-2 小时 | 性能测试 |
| **总计** | 1.5-2 天 | 完整流程 |

**灵活性**: 这项工作可以提前开始,也可以由任何人独立完成。

### 1.3 谁来做这项工作?

- **推荐**: Dev A (AI/视觉专家)
- **备选**: 任何有 GPU 和时间的人
- **并行**: 可以在 Day 1 就开始,与系统开发完全并行

---

## 2. 前置条件 (Prerequisites)

### 2.1 硬件要求

| 组件 | 最低配置 | 推荐配置 | 说明 |
|------|----------|----------|------|
| **GPU** | GTX 1060 6GB | RTX 3060 12GB | 必须 CUDA 兼容 |
| **CPU** | Intel i5-8400 | Intel i7-9700K | 影响数据预处理速度 |
| **内存** | 16GB | 32GB | 训练时需要大量内存 |
| **存储** | 20GB SSD | 50GB NVMe SSD | 数据集 + 模型文件 |
| **显示器** | 1920x1080 | 1920x1080 | 游戏分辨率 |

**GPU 可选方案** (无 GPU 时):
- 使用 Google Colab (免费版)
- 使用 Kaggle Notebooks (免费 GPU)
- 训练时间会延长 2-3 倍

### 2.2 软件环境

#### 2.2.1 操作系统
- Windows 10/11 (推荐,与游戏兼容)
- Ubuntu 20.04+ (可运行 Windows 游戏截图)

#### 2.2.2 Python 环境

```bash
# 创建专用虚拟环境
python -m venv yolo_training_env

# 激活环境 (Windows)
yolo_training_env\Scripts\activate

# 激活环境 (Linux/Mac)
source yolo_training_env/bin/activate
```

#### 2.2.3 安装依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装 PyTorch (CUDA 11.8 版本)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 安装 YOLOv8
pip install ultralytics

# 安装数据标注工具
pip install labelImg

# 安装其他依赖
pip install opencv-python
pip install pyyaml
pip install mss
pip install numpy
pip install pillow
```

#### 2.2.4 验证安装

```python
# test_installation.py
import torch
import ultralytics
import cv2

print(f"PyTorch 版本: {torch.__version__}")
print(f"CUDA 可用: {torch.cuda.is_available()}")
print(f"CUDA 版本: {torch.version.cuda}")
print(f"GPU 数量: {torch.cuda.device_count()}")
if torch.cuda.is_available():
    print(f"GPU 名称: {torch.cuda.get_device_name(0)}")

# 测试 YOLO
from ultralytics import YOLO
model = YOLO("yolov8n.pt")
print("YOLOv8 安装成功!")
```

运行测试:
```bash
python test_installation.py
```

预期输出:
```
PyTorch 版本: 2.0.0+cu118
CUDA 可用: True
CUDA 版本: 11.8
GPU 数量: 1
GPU 名称: NVIDIA GeForce RTX 3060
YOLOv8 安装成功!
```

---

## 3. 数据收集 (Data Collection)

### 3.1 数据收集工具

项目提供了自动截图收集脚本: `/mnt/e/code/AradVision/scripts/capture_training_data.py`

### 3.2 使用步骤

#### 步骤 1: 启动游戏

1. 启动 Dungeon & Fighter (DNF)
2. 确保窗口标题包含 "Dungeon & Fighter"
3. 分辨率设置为 1920x1080 (全屏或窗口化)

#### 步骤 2: 运行收集脚本

```bash
cd /mnt/e/code/AradVision
python scripts/capture_training_data.py
```

#### 步骤 3: 在游戏中操作

脚本会自动截图 (每 0.5 秒一张), 建议进行以下操作:

**战斗场景**:
- 进入洛兰副本
- 攻击不同类型的怪物
- 从不同角度拍摄怪物
- 拍摄怪物不同状态 (站立、攻击、死亡)

**过图场景**:
- 寻找门/传送阵
- 拍摄门的不同形态
- 拍摄开门过程

**物品场景**:
- 拍摄地面掉落物
- 不同类型的物品图标

#### 步骤 4: 停止收集

按 `F12` 键停止收集

### 3.3 收集要求

| 指标 | 最低标准 | 推荐标准 | 说明 |
|------|----------|----------|------|
| **总图片数** | 300 张 | 500-1000 张 | 越多越好 |
| **怪物图片** | 150 张 | 300-500 张 | 不同类型、角度 |
| **玩家图片** | 50 张 | 100-200 张 | 不同动作 |
| **门图片** | 30 张 | 50-100 张 | 不同类型门 |
| **物品图片** | 30 张 | 50-100 张 | 不同物品 |
| **场景多样性** | 3 个副本 | 5-10 个副本 | 洛兰、格兰等 |

### 3.4 数据分布

收集完成后,使用分析脚本检查:

```bash
python scripts/analyze_dataset.py
```

预期输出:
```
📊 数据集分析报告
============================================================
总图片数: 523
总大小: 156.42 MB

分类统计:
  normal      : 345  ████████████████████████████
  bright      : 102  ████████
  dark        : 76   ██████

常见分辨率: 1920x1080

✅ 数据量充足
```

### 3.5 数据质量检查

**自动检查** (通过分析脚本):
- ✅ 图片分辨率正确 (1920x1080)
- ✅ 亮度分布合理
- ✅ 无损坏文件

**人工检查**:
- 随机抽查 20 张图片
- 确保目标清晰可见
- 删除模糊/无用的图片

### 3.6 数据目录结构

收集后的数据会保存在:
```
assets/images/raw/
├── normal/        # 正常亮度场景
│   ├── normal_20260210_143022_000001.jpg
│   ├── normal_20260210_143022_000002.jpg
│   └── ...
├── bright/        # 亮场景
└── dark/          # 暗场景
```

---

## 4. 数据标注 (Data Labeling)

### 4.1 安装标注工具

```bash
pip install labelImg
```

### 4.2 准备类别文件

创建 `classes.txt` 文件:
```bash
cat > classes.txt << EOF
monster
hero
item
gate
boss
EOF
```

### 4.3 启动标注工具

```bash
# 方式 1: 直接启动
labelImg assets/images/raw classes.txt

# 方式 2: 指定输出格式为 YOLO
labelImg assets/images/raw classes.txt --labels yolo
```

### 4.4 标注界面说明

```
┌─────────────────────────────────────────────────────────┐
│  File  View  Help      [Open Dir]  [Change Save Dir]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│           [图片显示区域]                                 │
│                                                         │
│            ┌─────────────────┐                          │
│            │   monster框     │                          │
│            └─────────────────┘                          │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  monster  hero  item  gate  boss                        │
│   ↑ 当前类别 (点击切换)                                   │
└─────────────────────────────────────────────────────────┘
```

### 4.5 标注步骤

#### 步骤 1: 创建标注框

1. 按 `w` 键 (或点击 "Create RectBox")
2. 鼠标拖动画框,框住目标
3. 选择正确的类别
4. 按 `Ctrl+S` 保存

#### 步骤 2: 快捷键

| 快捷键 | 功能 | 说明 |
|--------|------|------|
| `w` | 创建矩形框 | Draw Box |
| `d` | 下一张图片 | Next Image |
| `a` | 上一张图片 | Prev Image |
| `Del` | 删除选中框 | Delete Box |
| `Ctrl+S` | 保存 | Save |
| `Ctrl+D` | 复制标注到下一张 | Copy to Next |
| `Ctrl+Scroll` | 缩放图片 | Zoom |
| `Space` + `Drag` | 移动图片 | Pan |

#### 步骤 3: 标注规范

**类别定义**:

| 类别 | 说明 | 标注方法 | 示例 |
|------|------|----------|------|
| `monster` | 普通怪物 | 紧贴角色轮廓 | 哥布林、猫妖 |
| `boss` | 领主怪物 | 紧贴角色轮廓 | 房间 Boss |
| `hero` | 玩家自身 | 紧贴角色轮廓 | 自己的角色 |
| `item` | 掉落物品 | 框住整个物品图标 | 金币、装备 |
| `gate` | 门/传送阵 | 框住整个门 | 房间出口 |

**标注优先级** (Day 1-2):
1. ✅ **高优先级**: monster (清晰可见的怪物)
2. ✅ **高优先级**: gate (门/传送阵)
3. ✅ **中优先级**: hero (玩家自身)
4. ⏸️ **低优先级**: item (可后续补充)
5. ⏸️ **低优先级**: boss (场景少见,可后续补充)

**标注质量要求**:
- ✅ 框要紧贴目标边缘 (误差 < 5px)
- ✅ 不遮挡目标的关键特征
- ✅ 避免漏标 (同一张图片所有目标都要标)
- ✅ 避免错标 (类别要正确)

**暂缓标注的场景**:
- ⏸️ 技能特效严重遮挡 (可后续补充)
- ⏸️ 目标被遮挡超过 50%
- ⏸️ 目标太小 (远距离)

### 4.6 标注进度跟踪

建议使用表格记录:

| 日期 | 批次 | 图片数 | 标注数 | 进度 | 备注 |
|------|------|--------|--------|------|------|
| Day 1 | 批次 1 | 100 | 100 | 20% | 怪物为主 |
| Day 1 | 批次 2 | 100 | 100 | 40% | 补充门 |
| Day 2 | 批次 3 | 150 | 150 | 70% | 全面标注 |
| Day 2 | 批次 4 | 150 | 150 | 100% | 完成 |

### 4.7 标注质量检查

**自动化检查**:

```python
# check_annotation_quality.py
from pathlib import Path

data_dir = Path("assets/images/raw")
missing_labels = []

for img_file in data_dir.rglob("*.jpg"):
    txt_file = img_file.with_suffix(".txt")
    if not txt_file.exists():
        missing_labels.append(img_file)

if missing_labels:
    print(f"⚠️  {len(missing_labels)} 张图片缺少标注:")
    for img in missing_labels[:10]:  # 只显示前 10 个
        print(f"  - {img}")
else:
    print("✅ 所有图片都有标注")
```

运行检查:
```bash
python check_annotation_quality.py
```

**人工抽查**:
- 随机抽查 20 张图片
- 检查框是否准确
- 检查类别是否正确
- 修正错误标注

### 4.8 标注格式说明

标注文件为 YOLO TXT 格式,每行一个目标:
```
<class_id> <x_center> <y_center> <width> <height>
```

- `class_id`: 类别 ID (0=monster, 1=hero, 2=item, 3=gate, 4=boss)
- `x_center`, `y_center`: 中心点坐标 (归一化到 0-1)
- `width`, `height`: 宽度和高度 (归一化到 0-1)

示例 (假设图片 1920x1080):
```
0 0.5 0.6 0.1 0.2    # monster, 中心(960, 648), 尺寸(192, 216)
1 0.3 0.5 0.08 0.18  # hero, 中心(576, 540), 尺寸(154, 194)
```

### 4.9 标注完成标准

| 指标 | MVP 标准 | 完整版标准 |
|------|----------|------------|
| **总标注数** | ≥ 300 张 | ≥ 500 张 |
| **monster** | ≥ 150 个 | ≥ 300 个 |
| **gate** | ≥ 30 个 | ≥ 50 个 |
| **hero** | ≥ 50 个 | ≥ 100 个 |
| **准确率** | ≥ 95% | ≥ 98% |
| **完整性** | 无漏标 | 无漏标 |

---

## 5. 训练流程 (Training Process)

### 5.1 数据集准备

#### 步骤 1: 创建数据集目录结构

```bash
mkdir -p datasets/dnf_yolo/images/train
mkdir -p datasets/dnf_yolo/images/val
mkdir -p datasets/dnf_yolo/labels/train
mkdir -p datasets/dnf_yolo/labels/val
```

#### 步骤 2: 划分训练集和验证集

```python
# split_dataset.py
import shutil
from pathlib import Path
import random

random.seed(42)

# 源目录
source_dir = Path("assets/images/raw")

# 目标目录
train_img_dir = Path("datasets/dnf_yolo/images/train")
val_img_dir = Path("datasets/dnf_yolo/images/train")
train_lbl_dir = Path("datasets/dnf_yolo/labels/train")
val_lbl_dir = Path("datasets/dnf_yolo/labels/val")

# 收集所有图片
all_images = []
for category_dir in source_dir.iterdir():
    if category_dir.is_dir():
        all_images.extend(list(category_dir.glob("*.jpg")))

print(f"总图片数: {len(all_images)}")

# 打乱顺序
random.shuffle(all_images)

# 划分比例 (80% 训练, 20% 验证)
split_ratio = 0.8
split_idx = int(len(all_images) * split_ratio)

train_images = all_images[:split_idx]
val_images = all_images[split_idx:]

print(f"训练集: {len(train_images)} 张")
print(f"验证集: {len(val_images)} 张")

# 复制文件
for img in train_images:
    # 复制图片
    shutil.copy(img, train_img_dir / img.name)
    # 复制标注
    txt = img.with_suffix(".txt")
    if txt.exists():
        shutil.copy(txt, train_lbl_dir / txt.name)

for img in val_images:
    # 复制图片
    shutil.copy(img, val_img_dir / img.name)
    # 复制标注
    txt = img.with_suffix(".txt")
    if txt.exists():
        shutil.copy(txt, val_lbl_dir / txt.name)

print("✅ 数据集划分完成!")
```

运行划分:
```bash
python split_dataset.py
```

### 5.2 创建配置文件

创建 `datasets/dnf_yolo/data.yaml`:

```yaml
# 数据集配置
path: /mnt/e/code/AradVision/datasets/dnf_yolo  # 数据集根目录 (绝对路径)
train: images/train  # 训练集图片 (相对路径)
val: images/val      # 验证集图片 (相对路径)

# 类别定义
names:
  0: monster
  1: hero
  2: item
  3: gate
  4: boss

# 类别数量
nc: 5
```

### 5.3 训练脚本

创建 `train_yolo.py`:

```python
"""
YOLO 训练脚本
"""

from ultralytics import YOLO
import torch
from pathlib import Path

def main():
    # 检查 CUDA 可用性
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"使用设备: {device}")

    if device == 'cuda':
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    # 加载预训练模型 (从零开始训练)
    # 可选: yolov8n.pt (最快), yolov8s.pt (平衡), yolov8m.pt (精度高)
    model = YOLO("yolov8n.pt")

    # 开始训练
    results = model.train(
        data="datasets/dnf_yolo/data.yaml",  # 数据集配置
        epochs=100,                            # 训练轮数
        imgsz=640,                            # 输入图片大小
        batch=16,                             # 批次大小 (根据显存调整)
        device=device,                        # 设备
        workers=4,                            # 数据加载线程数
        name="dnf_yolo_v1",                   # 实验名称
        patience=20,                          # 早停耐心值
        save=True,                            # 保存检查点
        plots=True,                           # 生成训练曲线
        val=True,                             # 验证
        pretrained=True,                      # 使用预训练权重
        optimizer='Adam',                     # 优化器
        lr0=0.01,                             # 初始学习率
        lrf=0.01,                             # 最终学习率
        mosaic=1.0,                           # Mosaic 数据增强
        mixup=0.0,                            # Mixup 数据增强
    )

    print("\n✅ 训练完成!")
    print(f"模型保存在: runs/detect/train/weights/best.pt")

if __name__ == "__main__":
    main()
```

### 5.4 启动训练

```bash
python train_yolo.py
```

### 5.5 训练过程监控

训练过程中,终端会实时显示:

```
Ultralytics YOLOv8.0.0 🚀 Python-3.10.0 torch-2.0.0+cu118 CUDA:0 (NVIDIA GeForce RTX 3060, 12288MB)

[34m[1mTensorBoard: [0mStart with 'tensorboard --logdir runs/detect', view at http://localhost:6006/
[34m[1mtrain: [0mScanning /mnt/e/code/AradVision/datasets/dnf_yolo/labels/train... 400 images, 0 backgrounds, 0 corrupt: 100%|██████████| 400/400 [00:00<00:00, 1243.48it/s]
[34m[1mval: [0mScanning /mnt/e/code/AradVision/datasets/dnf_yolo/labels/val... 100 images, 0 backgrounds, 0 corrupt: 100%|██████████| 100/100 [00:00<00:00, 1156.23it/s]

       Class      Images   Instances          P          R      mAP50     mAP50-95:   0%|          | 0/100 [00:00<?, ?it/s]
         all         400        1200      0.725      0.681      0.745       0.512

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
  0%|          | 0/100 [00:00<?, ?it/s]
      1/100        3.5G      1.234      2.345      1.456        400        640:  10%|█        | 10/100 [00:15<02:25,  1.61s/it]
      2/100        3.5G      1.123      2.234      1.345        400        640:  20%|██       | 20/100 [00:30<02:05,  1.55s/it]
      ...
```

**关键指标**:
- `box_loss`: 边界框损失 (越低越好)
- `cls_loss`: 分类损失 (越低越好)
- `mAP50`: 平均精度 (IoU=0.5, 越高越好)
- `mAP50-95`: 平均精度 (IoU=0.5-0.95, 越高越好)

### 5.6 训练时间估算

| 配置 | 显存 | 批次大小 | 每轮时间 | 总时间 (100 轮) |
|------|------|----------|----------|-----------------|
| GTX 1060 6GB | 6GB | 8 | ~2 分钟 | ~3-4 小时 |
| RTX 3060 12GB | 12GB | 16 | ~1 分钟 | ~1.5-2 小时 |
| RTX 3070 8GB | 8GB | 16 | ~50 秒 | ~1-1.5 小时 |
| Google Colab | - | 16 | ~1.5 分钟 | ~2.5-3 小时 |

**注意**: 实际时间可能因数据量、硬件配置而异。

### 5.7 训练优化技巧

#### 技巧 1: 使用 TensorBoard 可视化

```bash
# 启动 TensorBoard (另开一个终端)
tensorboard --logdir runs/detect

# 浏览器访问
# http://localhost:6006
```

可以看到:
- 损失曲线
- mAP 曲线
- 学习率变化
- 验证结果可视化

#### 技巧 2: 调整批次大小

如果显存不足 (OOM):
```python
# 降低批次大小
batch=8  # 或 4
```

如果显存充足:
```python
# 增加批次大小 (加快训练)
batch=32
```

#### 技巧 3: 数据增强

```python
# 在 train_yolo.py 中调整
mosaic=1.0,   # Mosaic 增强 (推荐)
mixup=0.1,    # Mixup 增强 (可尝试)
hsv_h=0.015,  # 色调增强
hsv_s=0.7,    # 饱和度增强
hsv_v=0.4,    # 明度增强
```

#### 技巧 4: 早停 (Early Stopping)

```python
patience=20,  # 20 轮无改善则停止
```

### 5.8 训练中断与恢复

如果训练中断 (断电/程序崩溃):

```python
# 从检查点恢复训练
model = YOLO("runs/detect/train/weights/last.pt")
results = model.train(resume=True)
```

### 5.9 训练完成

训练完成后,模型保存在:
```
runs/detect/train/weights/
├── best.pt      # 最佳模型 (验证集 mAP 最高)
└── last.pt      # 最后一轮模型
```

**关键输出**:
- `best.pt`: 这是我们需要的最终模型文件
- `results.csv`: 训练历史数据
- `confusion_matrix.png`: 混淆矩阵
- `F1_curve.png`: F1 分数曲线
- `PR_curve.png`: 精确率-召回率曲线

---

## 6. 模型评估 (Model Evaluation)

### 6.1 评估指标说明

| 指标 | 含义 | 目标值 | 说明 |
|------|------|--------|------|
| **mAP50** | 平均精度 (IoU=0.5) | > 0.70 | 主要指标 |
| **mAP50-95** | 平均精度 (IoU=0.5-0.95) | > 0.50 | 更严格 |
| **Precision** | 精确率 | > 0.75 | 预测为正的准确度 |
| **Recall** | 召回率 | > 0.70 | 实际为正的检出率 |
| **FPS** | 推理速度 | > 30 | 每秒处理帧数 |

### 6.2 运行评估

```python
# evaluate_model.py
from ultralytics import YOLO

# 加载最佳模型
model = YOLO("runs/detect/train/weights/best.pt")

# 在验证集上评估
metrics = model.val()

print("\n📊 模型评估结果:")
print(f"mAP50: {metrics.box.map50:.4f}")
print(f"mAP50-95: {metrics.box.map:.4f}")
print(f"Precision: {metrics.box.mp:.4f}")
print(f"Recall: {metrics.box.mr:.4f}")
```

运行评估:
```bash
python evaluate_model.py
```

### 6.3 性能测试

测试推理速度:

```python
# test_inference_speed.py
import time
import cv2
from ultralytics import YOLO

# 加载模型
model = YOLO("runs/detect/train/weights/best.pt")

# 加载测试图片
img = cv2.imread("assets/images/raw/normal/test_image.jpg")

# 预热 (GPU 初始化)
for _ in range(10):
    model(img)

# 测试推理速度
times = []
for _ in range(100):
    start = time.perf_counter()
    results = model(img)
    end = time.perf_counter()
    times.append(end - start)

avg_time = sum(times) / len(times)
fps = 1.0 / avg_time

print(f"\n⚡ 推理性能:")
print(f"平均时间: {avg_time*1000:.2f} ms")
print(f"FPS: {fps:.2f}")
```

### 6.4 可视化预测结果

```python
# visualize_predictions.py
from ultralytics import YOLO
import cv2
from pathlib import Path

# 加载模型
model = YOLO("runs/detect/train/weights/best.pt")

# 测试图片
test_images = list(Path("assets/images/raw/normal").glob("*.jpg"))[:10]

for img_path in test_images:
    # 推理
    results = model(img_path)

    # 可视化
    annotated = results[0].plot()

    # 保存结果
    output_path = Path("outputs/predictions") / img_path.name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), annotated)

    print(f"✅ 保存: {output_path}")
```

### 6.5 类别别评估

分析每个类别的性能:

```python
# evaluate_per_class.py
from ultralytics import YOLO

model = YOLO("runs/detect/train/weights/best.pt")

# 验证
metrics = model.val()

# 打印每个类别的 mAP
print("\n📊 各类别性能:")
for i, name in enumerate(model.names):
    map50 = metrics.box.maps[i] if hasattr(metrics.box, 'maps') else 0
    print(f"{name:10s}: mAP50 = {map50:.4f}")
```

### 6.6 评估决策树

```
评估结果
├─ mAP50 > 0.70 ✅
│  └─ 继续测试,准备交付
├─ 0.60 < mAP50 < 0.70 ⚠️
│  ├─ 方案 1: 数据增强,重新训练 (2-4 小时)
│  └─ 方案 2: 接受,用于 MVP
└─ mAP50 < 0.60 ❌
   ├─ 方案 1: 增加数据量,重新训练 (1-2 天)
   ├─ 方案 2: 迁移学习 (2-4 小时)
   └─ 方案 3: 使用 COCO 预训练 (立即)
```

### 6.7 评估报告模板

```markdown
# YOLO 模型评估报告

**模型**: dnf_yolo_v1
**训练时间**: 2026-02-10
**训练设备**: RTX 3060 12GB

## 性能指标

| 指标 | 值 | 目标 | 状态 |
|------|-----|------|------|
| mAP50 | 0.723 | > 0.70 | ✅ |
| mAP50-95 | 0.512 | > 0.50 | ✅ |
| Precision | 0.756 | > 0.75 | ✅ |
| Recall | 0.712 | > 0.70 | ✅ |
| FPS | 45.2 | > 30 | ✅ |

## 各类别性能

| 类别 | mAP50 | Precision | Recall |
|------|-------|-----------|--------|
| monster | 0.785 | 0.812 | 0.761 |
| hero | 0.752 | 0.789 | 0.723 |
| gate | 0.681 | 0.701 | 0.665 |
| item | 0.612 | 0.645 | 0.598 |
| boss | 0.585 | 0.623 | 0.567 |

## 结论

✅ 模型性能达标,可用于 MVP

## 改进建议

- item 类别准确率偏低,建议增加样本
- boss 类别样本少,可后续补充
```

---

## 7. 模型集成 (Integration)

### 7.1 模型文件交付

**交付物**: `runs/detect/train/weights/best.pt`

将模型文件复制到项目资源目录:

```bash
mkdir -p /mnt/e/code/AradVision/assets/models
cp runs/detect/train/weights/best.pt /mnt/e/code/AradVision/assets/models/dnf_v1.pt
```

### 7.2 在主系统中使用

主系统会通过 `YoloDetector` 类加载模型:

```python
# core/vision/detector.py
from ultralytics import YOLO
from pathlib import Path

class YoloDetector:
    """YOLO 目标检测器"""

    def __init__(self, model_path: str = "assets/models/dnf_v1.pt"):
        """
        初始化检测器

        Args:
            model_path: 模型文件路径
        """
        self.model_path = Path(model_path)
        self.model = YOLO(str(self.model_path))

        # 类别映射
        self.class_names = self.model.names

    def detect(self, image):
        """
        检测图像中的目标

        Args:
            image: OpenCV 图像 (BGR)

        Returns:
            检测结果列表
        """
        results = self.model(image)
        return results

# 使用示例
detector = YoloDetector()
results = detector.detect(frame)
```

### 7.3 接口测试

在主系统中测试模型加载:

```python
# test_model_integration.py
from core.vision.detector import YoloDetector
import cv2

# 加载模型
detector = YoloDetector("assets/models/dnf_v1.pt")

# 测试图片
test_img = cv2.imread("test_screenshot.jpg")

# 检测
results = detector.detect(test_img)

# 打印结果
for r in results:
    for box in r.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        cls_name = detector.class_names[cls_id]
        print(f"检测到: {cls_name} (置信度: {conf:.2f})")
```

### 7.4 配置文件更新

更新主系统配置文件 `configs/vision.yaml`:

```yaml
# 视觉模块配置
vision:
  # YOLO 模型路径
  model_path: "assets/models/dnf_v1.pt"

  # 检测参数
  detection:
    conf_threshold: 0.6    # 置信度阈值
    iou_threshold: 0.45    # NMS IoU 阈值
    max_detections: 100    # 最大检测数

  # 推理优化
  inference:
    half: true             # FP16 推理 (更快)
    device: "cuda"         # 设备 (cuda/cpu)
    batch_size: 1          # 批次大小
```

### 7.5 集成检查清单

- [ ] 模型文件已复制到 `assets/models/`
- [ ] `YoloDetector` 类已实现
- [ ] 配置文件已更新
- [ ] 接口测试通过
- [ ] 推理速度满足要求 (< 30ms)
- [ ] 检测准确率满足要求 (> 70%)

---

## 8. 降级策略 (Fallback Strategy)

### 8.1 为什么需要降级策略?

**风险**: YOLO 训练可能失败或时间不够

**原因**:
- 数据量不足
- 标注质量差
- 训练时间超时
- 硬件故障

### 8.2 COCO 预训练模型降级

#### 方案概述

使用 COCO 数据集预训练的 YOLOv8 模型,直接用于检测 "person" 类别 (覆盖怪物和玩家)。

#### 优点
- ✅ 立即可用,无需训练
- ✅ 准确率可接受 (60-70%)
- ✅ 速度与自训练模型相同

#### 缺点
- ❌ 无法检测物品、门
- ❌ 对 DNF 特定目标可能不准确
- ❌ 类别映射不准确 (person ≈ monster)

#### 实施步骤

**步骤 1**: 下载 COCO 预训练模型

```python
from ultralytics import YOLO

# 下载并加载 COCO 预训练模型
model = YOLO("yolov8n.pt")  # 自动下载

# 保存到项目目录
model.save("assets/models/dnf_coco_fallback.pt")
```

**步骤 2**: 类别映射

```python
# core/vision/detector.py
class YoloDetector:
    # COCO 类别映射
    COCO_CLASS_MAPPING = {
        "person": "monster",  # 人物 → 怪物
        # 其他类别不使用
    }

    def __init__(self, use_coco_fallback=False):
        if use_coco_fallback:
            self.model = YOLO("assets/models/dnf_coco_fallback.pt")
            self.class_mapping = self.COCO_CLASS_MAPPING
        else:
            self.model = YOLO("assets/models/dnf_v1.pt")
            self.class_mapping = None
```

**步骤 3**: 使用降级方案

```python
# 使用 COCO 降级
detector = YoloDetector(use_coco_fallback=True)
results = detector.detect(frame)
```

### 8.3 迁移学习降级

#### 方案概述

使用 COCO 预训练权重,用少量 DNF 数据微调 (100-200 张)。

#### 优点
- ✅ 训练时间短 (2-4 小时)
- ✅ 准确率比纯 COCO 高
- ✅ 可以检测自定义类别

#### 缺点
- ⚠️ 仍需少量标注数据
- ⚠️ 准确率可能不如完整训练

#### 实施步骤

```python
# train_finetune.py
from ultralytics import YOLO

# 加载 COCO 预训练权重
model = YOLO("yolov8n.pt")

# 微调 (少量数据,少轮次)
results = model.train(
    data="datasets/dnf_yolo/data.yaml",
    epochs=20,          # 只训练 20 轮
    imgsz=640,
    batch=16,
    device="cuda",
    name="dnf_finetune_v1",
    pretrained=True,    # 使用预训练权重
    freeze=10,          # 冻结前 10 层
)

print("✅ 微调完成!")
```

### 8.4 降级决策树

```
Day 3 上午: 检查训练结果
├─ mAP50 > 0.70 ✅
│  └─ 继续使用自训练模型
│
├─ 0.60 < mAP50 < 0.70 ⚠️
│  ├─ 有时间 (距 Day 4 还有 > 12 小时)
│  │  └─ 方案 A: 数据增强 + 重新训练
│  └─ 时间紧迫
│     └─ 方案 B: 接受当前模型
│
└─ mAP50 < 0.60 ❌
   ├─ 有 2-4 小时
   │  └─ 方案 C: 迁移学习微调
   └─ 时间极紧
      └─ 方案 D: COCO 预训练降级
```

### 8.5 降级方案对比

| 方案 | 准确率 | 时间 | 数据需求 | 推荐场景 |
|------|--------|------|----------|----------|
| **自训练模型** | 70-80% | 1-2 天 | 500+ 张 | 标准 (首选) |
| **迁移学习** | 65-75% | 2-4 小时 | 100-200 张 | 训练部分失败 |
| **COCO 降级** | 60-70% | 立即 | 0 张 | 训练完全失败 |

### 8.6 切换降级方案

在主系统中切换模型:

```python
# configs/vision.yaml
vision:
  # 模型选择
  model_type: "coco_fallback"  # "custom" 或 "coco_fallback"

  # 模型路径
  models:
    custom: "assets/models/dnf_v1.pt"
    coco_fallback: "assets/models/dnf_coco_fallback.pt"
```

```python
# core/vision/detector.py
import yaml

class YoloDetector:
    def __init__(self, config_path="configs/vision.yaml"):
        with open(config_path) as f:
            config = yaml.safe_load(f)

        model_type = config["vision"]["model_type"]
        model_path = config["vision"]["models"][model_type]

        self.model = YOLO(model_path)
```

---

## 9. 与开发分离 (Separation from Development)

### 9.1 完全独立的理由

**关键概念**: YOLO 训练是一个独立的 "黑盒",输入是数据,输出是模型文件。

```
YOLO 训练流程 (独立):

输入:
- 游戏截图 (500-1000 张)
- 标注文件 (.txt)

处理 (训练):
- 数据预处理
- 模型训练 (8-12 小时,自动)
- 模型评估

输出:
- 模型文件 (.pt)

↓ 交付

主开发流程:
- 使用模型文件
- 无需关心训练细节
```

### 9.2 并行开发时间线

```
Day 1-2: 数据阶段
├─ Dev A (或任何人): 数据采集 + 标注
└─ Dev B: 系统框架开发 (使用 Mock 数据)

Day 3: 训练阶段
├─ Dev A (或任何人): 启动训练 + 等待
└─ Dev B: 业务逻辑开发 (继续使用 Mock)

Day 4: 集成阶段
├─ Dev A: 交付模型文件
└─ Dev B: 集成真实模型,替换 Mock
```

### 9.3 接口解耦

**关键**: 主系统通过标准接口使用 YOLO,不依赖具体实现。

```python
# core/vision/base_detector.py
from abc import ABC, abstractmethod

class BaseDetector(ABC):
    """检测器基类"""

    @abstractmethod
    def detect(self, image):
        """
        检测目标

        Args:
            image: OpenCV 图像

        Returns:
            List[GameObject]: 检测到的目标列表
        """
        pass

# core/vision/yolo_detector.py
class YoloDetector(BaseDetector):
    """YOLO 实现"""
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def detect(self, image):
        results = self.model(image)
        # 转换为 GameObject 列表
        return self._convert_to_game_objects(results)

# core/vision/mock_detector.py
class MockDetector(BaseDetector):
    """Mock 实现 (开发阶段使用)"""
    def detect(self, image):
        # 返回模拟数据
        return [
            GameObject(cls_id=0, bbox=(100, 200, 300, 400)),
            GameObject(cls_id=1, bbox=(500, 300, 600, 500)),
        ]
```

**主系统使用**:
```python
# logic/bot_fsm.py
from core.vision.base_detector import BaseDetector

class BotFSM:
    def __init__(self, detector: BaseDetector):
        # 不关心具体实现
        self.detector = detector

    def update(self, frame):
        # 调用接口
        objects = self.detector.detect(frame)
        # 处理逻辑...
```

**切换实现**:
```python
# 开发阶段: 使用 Mock
detector = MockDetector()
bot = BotFSM(detector)

# 训练完成: 切换真实 YOLO
detector = YoloDetector("assets/models/dnf_v1.pt")
bot = BotFSM(detector)
```

### 9.4 任何人都能做

**YOLO 训练不要求是 Dev A**:

- **数据采集**: 任何人都可以运行脚本
- **数据标注**: 任何人都可以学习标注 (1 小时上手)
- **模型训练**: 完全自动化,无需 AI 经验
- **模型评估**: 运行评估脚本,查看指标

**前提**:
- 有 GPU (或使用云 GPU)
- 有时间 (1-2 天)
- 按照本文档操作

### 9.5 交接机制

如果训练由非 Dev A 的人完成:

**交付物清单**:
- [ ] 模型文件: `assets/models/dnf_v1.pt`
- [ ] 训练报告: `docs/yolo_training_report.md`
- [ ] 评估报告: `docs/yolo_evaluation_report.md`
- [ ] 使用说明: 5 分钟快速上手

**快速交接**:
```markdown
# YOLO 模型交接

## 模型信息
- 文件: `assets/models/dnf_v1.pt`
- 大小: 6.2 MB
- mAP50: 0.723

## 使用方法
```python
from core.vision.detector import YoloDetector

detector = YoloDetector("assets/models/dnf_v1.pt")
results = detector.detect(frame)
```

## 性能
- 推理速度: 22ms (45 FPS)
- 置信度阈值: 0.6
- 检测类别: monster, hero, gate, item, boss
```

---

## 10. 交付物 (Deliverables)

### 10.1 核心交付物

| 项目 | 路径 | 说明 | 必需 |
|------|------|------|------|
| **模型文件** | `assets/models/dnf_v1.pt` | 训练好的模型 | ✅ 是 |
| **训练脚本** | `train_yolo.py` | 可复现训练 | ✅ 是 |
| **数据集配置** | `datasets/dnf_yolo/data.yaml` | 数据集定义 | ✅ 是 |
| **训练报告** | `docs/yolo_training_report.md` | 训练过程记录 | ✅ 是 |
| **评估报告** | `docs/yolo_evaluation_report.md` | 性能评估 | ✅ 是 |

### 10.2 可选交付物

| 项目 | 路径 | 说明 |
|------|------|------|
| **原始数据** | `assets/images/raw/` | 原始截图 |
| **标注数据** | `datasets/dnf_yolo/` | 标注文件 |
| **训练日志** | `runs/detect/train/` | 详细训练日志 |
| **可视化结果** | `outputs/predictions/` | 预测可视化 |

### 10.3 训练报告模板

```markdown
# YOLO 模型训练报告

**项目**: AradVision DNF YOLO 模型
**版本**: v1.0
**训练日期**: 2026-02-10
**训练人**: [姓名]

## 1. 数据集

### 1.1 数据统计

| 指标 | 值 |
|------|-----|
| 总图片数 | 523 |
| 训练集 | 418 |
| 验证集 | 105 |
| 类别数 | 5 |

### 1.2 数据分布

| 类别 | 训练集 | 验证集 | 总计 |
|------|--------|--------|------|
| monster | 245 | 62 | 307 |
| hero | 82 | 20 | 102 |
| gate | 45 | 12 | 57 |
| item | 38 | 9 | 47 |
| boss | 8 | 2 | 10 |

## 2. 训练配置

### 2.1 模型

- **模型**: YOLOv8n
- **预训练**: COCO (迁移学习)
- **输入尺寸**: 640x640
- **批次大小**: 16

### 2.2 训练参数

| 参数 | 值 |
|------|-----|
| Epochs | 100 |
| 学习率 | 0.01 |
| 优化器 | Adam |
| 早停 | 20 轮 |

### 2.3 数据增强

- Mosaic: 1.0
- Mixup: 0.0
- HSV 增强: 默认

## 3. 训练过程

### 3.1 硬件

- **GPU**: NVIDIA RTX 3060 12GB
- **CPU**: Intel i7-9700K
- **内存**: 32GB
- **训练时间**: 1 小时 45 分钟

### 3.2 训练曲线

[插入 loss 曲线图]

### 3.3 最佳结果

- **Epoch**: 78
- **mAP50**: 0.723
- **mAP50-95**: 0.512

## 4. 模型性能

### 4.1 整体指标

| 指标 | 值 | 目标 | 状态 |
|------|-----|------|------|
| mAP50 | 0.723 | > 0.70 | ✅ |
| mAP50-95 | 0.512 | > 0.50 | ✅ |
| Precision | 0.756 | > 0.75 | ✅ |
| Recall | 0.712 | > 0.70 | ✅ |

### 4.2 各类别性能

| 类别 | mAP50 | Precision | Recall |
|------|-------|-----------|--------|
| monster | 0.785 | 0.812 | 0.761 |
| hero | 0.752 | 0.789 | 0.723 |
| gate | 0.681 | 0.701 | 0.665 |
| item | 0.612 | 0.645 | 0.598 |
| boss | 0.585 | 0.623 | 0.567 |

### 4.3 推理性能

| 指标 | 值 | 单位 |
|------|-----|------|
| 推理时间 | 22 | ms |
| FPS | 45 | - |
| 显存占用 | 1.2 | GB |

## 5. 结论

✅ 模型性能达标,可用于 AradVision 主系统

## 6. 改进建议

1. 增加 item 类别样本 (当前准确率偏低)
2. 补充 boss 类别样本 (当前样本少)
3. 可考虑增加训练轮次至 150
```

### 10.4 评估报告模板

```markdown
# YOLO 模型评估报告

**模型**: dnf_v1.pt
**评估日期**: 2026-02-10
**评估人**: [姓名]

## 1. 评估环境

- **测试集**: 验证集 (105 张)
- **硬件**: RTX 3060 12GB
- **推理模式**: FP16

## 2. 性能指标

### 2.1 整体性能

| 指标 | 值 | 说明 |
|------|-----|------|
| mAP50 | 0.723 | 主要指标,达标 |
| mAP50-95 | 0.512 | 严格指标,达标 |
| Precision | 0.756 | 精确率,达标 |
| Recall | 0.712 | 召回率,达标 |

### 2.2 推理性能

| 指标 | 值 | 目标 | 状态 |
|------|-----|------|------|
| 推理时间 | 22 ms | < 30 ms | ✅ |
| FPS | 45 | > 30 | ✅ |
| 显存占用 | 1.2 GB | < 2 GB | ✅ |

## 3. 各类别分析

### 3.1 性能排名

1. **monster**: mAP50 = 0.785 (优秀)
2. **hero**: mAP50 = 0.752 (良好)
3. **gate**: mAP50 = 0.681 (可接受)
4. **item**: mAP50 = 0.612 (需改进)
5. **boss**: mAP50 = 0.585 (需改进)

### 3.2 问题分析

#### item 类别准确率偏低

**原因**:
- 样本量少 (仅 47 个)
- 物品尺寸小,易漏检
- 背景相似,区分困难

**改进建议**:
- 增加样本至 100+
- 调整 NMS 阈值
- 考虑单独训练小目标检测

#### boss 类别准确率偏低

**原因**:
- 样本极少 (仅 10 个)
- boss 外观差异大

**改进建议**:
- 补充各类型 boss 样本
- 数据增强

## 4. 可视化结果

[插入预测结果图片]

## 5. 对比分析

### 5.1 vs COCO 预训练

| 模型 | mAP50 | FPS |
|------|-------|-----|
| dnf_v1.pt (自训练) | 0.723 | 45 |
| yolov8n.pt (COCO) | 0.650 | 48 |

**结论**: 自训练模型性能提升 11%

### 5.2 vs 迁移学习

| 模型 | mAP50 | 训练时间 |
|------|-------|----------|
| dnf_v1.pt (完整训练) | 0.723 | 1.75h |
| dnf_finetune.pt (微调) | 0.685 | 0.5h |

**结论**: 完整训练性能提升 5.5%,但时间多 3.5 倍

## 6. 集成建议

### 6.1 置信度阈值

根据验证结果,推荐阈值:

| 类别 | 推荐阈值 | 说明 |
|------|----------|------|
| monster | 0.60 | 高置信度 |
| hero | 0.65 | 较高置信度 |
| gate | 0.55 | 中等置信度 |
| item | 0.50 | 较低置信度 (避免漏检) |
| boss | 0.50 | 较低置信度 (样本少) |

**统一阈值**: 0.60 (平衡)

### 6.2 后处理

- 使用 NMS (IoU=0.45)
- 最大检测数: 100

## 7. 结论与建议

### 7.1 总体评价

✅ **模型性能良好,可用于 MVP**

- 主要指标 (mAP50) 达标
- 推理速度满足实时要求
- monster/hero/gate 类别性能良好

### 7.2 使用建议

1. **MVP 阶段**: 直接使用当前模型
2. **完整版**: 优化 item/boss 类别 (补充数据后重训)
3. **监控**: 在实际使用中收集错误案例,用于迭代

### 7.3 降级方案

如果性能不满足:
- 方案 1: 调整置信度阈值
- 方案 2: 使用 COCO 预训练 (备用)
- 方案 3: 迁移学习微调 (2-4 小时)

## 8. 附录

### 8.1 混淆矩阵

[插入混淆矩阵图]

### 8.2 PR 曲线

[插入精确率-召回率曲线]

### 8.3 错误案例分析

| 案例 | 错误类型 | 原因 | 改进 |
|------|----------|------|------|
| 1 | 漏检 | 怪物被遮挡 | 增加遮挡样本 |
| 2 | 误检 | 背景相似 | 数据增强 |
| 3 | 类别错误 | monster vs boss | 补充 boss 样本 |
```

### 10.5 文件打包

交付时,打包以下文件:

```bash
# 创建交付包
mkdir -p yolo_model_delivery_v1.0

# 复制文件
cp assets/models/dnf_v1.pt yolo_model_delivery_v1.0/
cp train_yolo.py yolo_model_delivery_v1.0/
cp -r datasets/dnf_yolo/data.yaml yolo_model_delivery_v1.0/
cp docs/yolo_training_report.md yolo_model_delivery_v1.0/
cp docs/yolo_evaluation_report.md yolo_model_delivery_v1.0/

# 创建 README
cat > yolo_model_delivery_v1.0/README.md << 'EOF'
# AradVision YOLO 模型交付包 v1.0

## 快速开始

### 1. 安装依赖

```bash
pip install ultralytics torch opencv-python
```

### 2. 测试模型

```python
from ultralytics import YOLO

# 加载模型
model = YOLO("dnf_v1.pt")

# 推理
results = model("test_image.jpg")

# 显示结果
results[0].show()
```

### 3. 集成到 AradVision

```bash
# 复制模型到项目
cp dnf_v1.pt /mnt/e/code/AradVision/assets/models/
```

## 文件说明

- `dnf_v1.pt`: 训练好的模型 (主要交付物)
- `data.yaml`: 数据集配置
- `train_yolo.py`: 训练脚本 (可复现)
- `yolo_training_report.md`: 训练报告
- `yolo_evaluation_report.md`: 评估报告

## 性能

- mAP50: 0.723
- FPS: 45
- 推理时间: 22ms

## 联系方式

如有问题,请联系: [训练人姓名]
EOF

# 打包
tar -czf yolo_model_delivery_v1.0.tar.gz yolo_model_delivery_v1.0/
```

---

## 附录 A: 常见问题 (FAQ)

### Q1: 训练需要多长时间?

**A**:
- 数据采集: 4-6 小时
- 数据标注: 8-12 小时
- 模型训练: 8-12 小时 (GPU)
- 总计: 1.5-2 天

### Q2: 没有 GPU 怎么办?

**A**: 有三个选择:
1. 使用 Google Colab (免费 GPU)
2. 使用 Kaggle Notebooks (免费 GPU)
3. 使用云 GPU (AWS/GCP,按需付费)

### Q3: 最少需要多少张图片?

**A**:
- **MVP**: 300 张 (可接受,性能一般)
- **推荐**: 500 张 (性能良好)
- **理想**: 1000 张 (性能优秀)

### Q4: 标注需要什么工具?

**A**: 推荐使用 **LabelImg**:
```bash
pip install labelImg
```

### Q5: 训练失败了怎么办?

**A**: 使用降级方案:
1. 检查错误日志
2. 如果是显存不足,降低 batch size
3. 如果是数据问题,检查标注
4. 实在不行,使用 COCO 预训练模型

### Q6: 模型准确率不达标怎么办?

**A**: 按优先级:
1. 调整置信度阈值 (快速)
2. 数据增强 + 重训 (2-4 小时)
3. 增加数据量 + 重训 (1-2 天)
4. 使用 COCO 降级 (立即)

### Q7: 可以由非 Dev A 的人做吗?

**A**: **完全可以!**
- 数据采集: 运行脚本即可
- 数据标注: 1 小时学会
- 模型训练: 全自动
- 只要有 GPU 和时间

### Q8: 如何快速验证模型可用?

**A**: 运行快速测试:
```python
from ultralytics import YOLO

model = YOLO("dnf_v1.pt")
results = model("test.jpg")
results[0].show()
```

### Q9: 模型文件多大?

**A**:
- YOLOv8n: ~6 MB
- YOLOv8s: ~14 MB
- YOLOv8m: ~42 MB

推荐使用 **YOLOv8n** (最小最快)。

### Q10: 训练完成后如何交付?

**A**: 只需交付:
1. **模型文件**: `dnf_v1.pt` (必需)
2. **训练报告**: 简要说明 (可选)
3. **评估报告**: 性能指标 (可选)

将模型文件复制到主系统:
```bash
cp dnf_v1.pt /mnt/e/code/AradVision/assets/models/
```

---

## 附录 B: 参考资源

### B.1 官方文档

- [Ultralytics YOLOv8 文档](https://docs.ultralytics.com/)
- [PyTorch 文档](https://pytorch.org/docs/stable/index.html)

### B.2 教程

- [YOLOv8 自定义数据训练](https://docs.ultralytics.com/yolov8/tutorials/train_custom_det/)
- [LabelImg 使用指南](https://github.com/heartexlabs/labelImg)

### B.3 项目资源

- 项目代码: `/mnt/e/code/AradVision`
- 数据收集脚本: `/mnt/e/code/AradVision/scripts/capture_training_data.py`
- 标注指南: `/mnt/e/code/AradVision/scripts/label_guide.py`

---

**文档版本**: V1.0
**最后更新**: 2026-02-10
**维护者**: haneball17
**审核状态**: ✅ 已审核

**变更记录**:
- 2026-02-10: 初版发布 (haneball17)
