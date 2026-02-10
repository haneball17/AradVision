
# 编码规范与风格指南 (Coding Standards & Style Guide)

 **项目名称** ：AradVision - DNF 视觉辅助自动化系统

 **文档标识** ：ARAD-STD-001

 **版本** ：V1.0

 **状态** ：执行中 (Enforced)

 **适用范围** ：所有 Python 代码及配置文件

---

## 1. 核心原则 (Core Principles)

1. **可读性优先 (Readability First)** ：代码是写给人看的，其次才是给机器运行的。
2. **类型安全 (Type Safety)** ：虽然 Python 是动态语言，但本项目**强制要求**使用 Type Hints（类型提示），以便于 IDE 静态分析和减少运行时错误。
3. **性能敏感 (Performance Aware)** ：在 `vision` 和 `input` 模块中，避免不必要的内存拷贝和阻塞操作，保证 FPS 稳定。
4. **配置分离 (Config Separation)** ：严禁在代码中硬编码魔法数字（Magic Numbers），所有阈值、坐标、按键定义必须提取到 `config.yaml`。

---

## 2. 命名规范 (Naming Conventions)

遵循 **PEP 8** 标准，具体细则如下：

| **类型**       | **风格**  | **示例**                                | **说明**                                     |
| -------------------- | --------------- | --------------------------------------------- | -------------------------------------------------- |
| **包/模块**    | `snake_case`  | `vision_core.py`,`input_driver.py`        | 简短全小写，下划线分隔                             |
| **类 (Class)** | `PascalCase`  | `YoloDetector`,`GameBot`                  | 首字母大写，名词短语                               |
| **函数/方法**  | `snake_case`  | `detect_objects()`,`calculate_distance()` | 动词+名词，描述动作                                |
| **变量**       | `snake_case`  | `enemy_list`,`current_hp`                 | 描述性强，避免使用 `a`,`b`,`x`(数学公式除外) |
| **常量**       | `UPPER_CASE`  | `MAX_RETRIES`,`DEFAULT_FPS`               | 全大写，下划线分隔                                 |
| **私有成员**   | `_snake_case` | `_load_model()`,`_hwnd`                   | 单下划线前缀，仅限类内部使用                       |

**特定领域术语缩写：**

* `img` / `frame`: OpenCV 图像矩阵
* `bbox`: Bounding Box (x1, y1, x2, y2)
* `conf`: Confidence (置信度)
* `ctx`: Context (上下文对象)
* `hwnd`: Window Handle (窗口句柄)

---

## 3. 代码格式与排版 (Formatting)

### 3.1 缩进与行宽

* **缩进** ：统一使用  **4个空格** ，严禁使用 Tab。
* **行宽** ：限制在 **100字符** 以内（比 PEP 8 的 79 字符稍宽，适应现代屏幕）。

### 3.2 导入顺序 (Imports)

**Python**

```
# 1. 标准库
import os
import time
import threading

# 2. 第三方库 (CV, ML, System)
import cv2
import numpy as np
import win32gui
from ultralytics import YOLO

# 3. 本地模块
from core.utils import load_config
from data.models import GameObject
```

### 3.3 类型提示 (Type Hinting) **[强制]**

所有函数定义必须包含参数类型和返回类型。

 **错误示例 ❌** ：

**Python**

```
def find_monster(img):
    # ...
    return results
```

 **正确示例 ✅** ：

**Python**

```
from typing import List, Optional
import numpy as np

def find_monster(frame: np.ndarray) -> List[GameObject]:
    # ...
    return results
```

---

## 4. 注释与文档 (Comments & Documentation)

### 4.1 文档字符串 (Docstrings)

使用 **Google Style** 风格的 Docstring，描述函数的作用、参数和返回值。

**Python**

```
def align_y_axis(self, target_y: int, tolerance: int = 15) -> bool:
    """
    判断当前角色是否与目标在 Y 轴上对齐。

    Args:
        target_y (int): 目标的 Y 轴落地坐标。
        tolerance (int): 允许的像素误差范围。

    Returns:
        bool: 如果在误差范围内返回 True，否则 False。
    """
    delta = abs(self.player_y - target_y)
    return delta <= tolerance
```

### 4.2 行内注释

* 只解释 **为什么 (Why)** ，不解释 **是什么 (What)** 。
* 对于复杂的算法（如 Y 轴修正公式），必须加注释说明原理。

**Python**

```
# 错误：增加计数器
count += 1 

# 正确：跳过前 5 帧以等待模型预热
if frame_idx < 5:
    continue
```

---

## 5. 项目结构规范 (Directory Structure)

必须严格保持以下结构，避免文件乱放。

**Plaintext**

```
AradVision/
├── assets/                 # 静态资源 (图片模板, .pt 模型)
├── configs/                # 配置文件 (.yaml)
├── core/                   # 核心架构代码
│   ├── capture.py          # 截图实现
│   ├── input.py            # 输入实现
│   └── types.py            # 数据类定义 (GameObject, Context)
├── logic/                  # 业务逻辑
│   ├── bot_fsm.py          # 状态机
│   └── strategies.py       # 具体策略 (过图, 战斗)
├── vision/                 # 视觉算法
│   ├── detector.py         # YOLO 封装
│   └── ocr.py              # 文字识别
├── main.py                 # 入口文件
└── tests/                  # 单元测试
```

---

## 6. 异常处理与日志 (Error Handling & Logging)

### 6.1 日志记录

* **严禁使用 `print()`** 用于调试信息。
* 使用 `loguru` 库进行分级记录。

**Python**

```
from loguru import logger

logger.debug("正在加载模型...")        # 开发调试用
logger.info("副本通关成功，耗时 45s")   # 关键流程节点
logger.warning("目标丢失，尝试重搜索")  # 非致命错误
logger.error("截图失败: 句柄无效")      # 致命错误
```

### 6.2 异常捕获

不要捕获所有异常，除非是在主循环的最外层。

**Python**

```
# 错误 ❌
try:
    do_something()
except:
    pass

# 正确 ✅
try:
    window_handle = find_window("DNF")
except WindowNotFoundError:
    logger.error("未找到游戏窗口，请先启动游戏。")
    sys.exit(1)
```

---

## 7. 安全与反检测规范 (Safety & Anti-Cheat)

针对 DNF 的特殊性，编码时需遵守以下铁律：

1. **随机化 (Randomization)** ：

* 任何 `time.sleep()` 的参数不能是固定的整数。
* 使用 `random.uniform(min, max)` 生成浮动值。
* *规范* ：定义 `wait_random(0.1, 0.2)` 辅助函数。

1. **输入模拟 (Input Simulation)** ：

* 严禁使用 `pyautogui` 的瞬移鼠标功能。
* 按键必须有“按下 -> 等待 -> 弹起”的过程，不能直接发脉冲信号。

1. **熔断机制 (Kill Switch)** ：

* 在 `main.py` 中必须启动独立线程监听 `F12`。
* 该逻辑优先级最高，必须能打断任何 `while` 循环。

---

## 8. 版本控制规范 (Git Workflow)

* **提交信息 (Commit Message)** ：
* `feat: 添加 YOLOv8 推理模块`
* `fix: 修复 Y 轴对齐判定过严的 bug`
* `docs: 更新安装文档`
* `refactor: 重构 InputDriver 类`
* **忽略文件 (.gitignore)** ：
* 忽略 `__pycache__/`
* 忽略 `*.pt` (模型文件通常较大，建议单独管理或用 LFS)
* 忽略 `logs/` (运行时日志)
* 忽略 `my_config.yaml` (包含个人配置的文件)

---

 **批准人** ：haneball17

 **日期** ：2026-02-10
