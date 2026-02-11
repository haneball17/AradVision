# YOLO 模型文件目录

此目录用于存放 AradVision 项目的 YOLO 训练模型。

## 文件说明

### 模型文件
- `yolov8n_dnf.pt` - DNF 专用训练模型（待训练）
- `yolov8n.pt` - YOLOv8 Nano 官方预训练模型（COCO）
- `yolov8s.pt` - YOLOv8 Small 官方预训练模型（可选）

### 训练结果
- `training_results.txt` - 训练指标（mAP, loss, precision, recall）
- `dataset.yaml` - 数据集配置文件

## 使用说明

### 1. 下载预训练模型
```bash
# 下载 YOLOv8 Nano 官方模型
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -P models/
```

### 2. 训练自定义模型
```bash
# 使用标注数据训练 DNF 专用模型
python scripts/train_yolo.py --data configs/dataset.yaml --epochs 100
```

### 3. 配置使用
在 `configs/config.yaml` 中配置：
```yaml
detector:
  type: yolo
  model_path: models/yolov8n_dnf.pt
```

## 模型性能指标

### 验收标准
- ✅ mAP @ 0.5 > 70%
- ✅ 怪物检测准确率 > 80%
- ✅ 推理速度 < 30ms (GPU)
- ✅ 模型文件 < 20MB

### 降级方案
如果训练未完成或效果不佳：
1. 使用 COCO 预训练模型 (`yolov8n.pt`)
2. 检测 "person" 类别作为怪物
3. 可满足 MVP 基本需求

## 注意事项

- ⚠️ 模型文件通常较大（10-20MB），已加入 .gitignore
- ⚠️ 训练好的模型应单独备份
- ⚠️ 模型训练详见 `docs/AradVision_YOLO训练专项指南.md`

## 相关文档

- [YOLO 训练指南](../docs/AradVision_YOLO训练专项指南.md)
- [模块接口规范](../docs/AradVision模块接口契约规范.md)
