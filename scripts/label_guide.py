# LabelImg 快速标注指南

## 安装 LabelImg

```bash
pip install labelImg
```

## 启动标注工具

```bash
# 预定义类别文件
echo "monster
hero
item
gate
boss" > classes.txt

# 启动LabelImg
labelImg assets/images/raw classes.txt
```

## 标注快捷键

- `w` - 创建矩形框
- `d` - 下一张图片
- `a` - 上一张图片
- `Del` - 删除选中框
- `Ctrl+S` - 保存
- `Ctrl+D` - 复制当前标注到下一张

## 标注规范

### 类别定义

| 类别 | 说明 | 标注建议 |
|------|------|----------|
| `monster` | 普通怪物 | 紧贴角色轮廓 |
| `boss` | 领主怪物 | 紧贴角色轮廓 |
| `hero` | 玩家自身 | 紧贴角色轮廓 |
| `item` | 掉落物品 | 框住整个物品图标 |
| `gate` | 门/传送阵 | 框住整个门 |

### 标注优先级

Day 1 优先标注以下场景：
1. ✅ 怪物清晰可见的战斗场景
2. ✅ 门/传送阵清晰可见的过图场景
3. ✅ 多个怪物同时出现的场景

暂缓标注：
- ⏸️ 技能特效严重的场景（可后续补充）
- ⏸️ 怪物被遮挡超过50%的场景

### 质量检查

标注完成后，使用以下命令检查：

```bash
python scripts/analyze_dataset.py
```

确保：
- ✅ 每个类别至少标注 50+ 张
- ✅ 标注框准确贴合目标
- ✅ 无漏标、无错标

## YOLO格式转换

标注完成后，需要转换为YOLO格式：

```python
from pathlib import Path
import json

# LabelImg会生成YOLO格式的txt文件
# 确保每张图片都有对应的txt标注文件

# 检查标注完整性
missing = []
for img in Path("assets/images/raw").rglob("*.jpg"):
    txt = img.with_suffix(".txt")
    if not txt.exists():
        missing.append(img)

if missing:
    print(f"⚠️  {len(missing)} 张图片缺少标注")
else:
    print("✅ 所有图片都有标注")
```
