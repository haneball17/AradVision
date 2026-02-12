# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AradVision** is a Computer Vision-based automation system for the game "Dungeon Fighter" (DNF). It uses visual recognition and AI decision-making to automate gameplay through screen capture and input simulation (non-invasive approach - no memory injection).

**Status**: Planning/Design phase - only documentation exists, implementation not started.

## Technology Stack

- **Language**: Python 3.10+
- **Vision**: Ultralytics YOLOv8 (object detection)
- **Image Processing**: OpenCV (cv2)
- **Screen Capture**: MSS (Multiple Screen Shots)
- **Input Control**: PyDirectInput / Win32 API (DirectX scan codes required)
- **Configuration**: PyYAML
- **Logging**: loguru (NO print() statements allowed)
- **Acceleration**: CUDA 11.x + TensorRT (for GPU inference)

## Architecture

The system uses a **Layered Architecture** with **Event-Driven** design. Data flows unidirectionally:

```
Infrastructure Layer → Perception Layer → Decision Layer → Application Layer
```

### Layer Responsibilities

- **Infrastructure Layer**: `CaptureEngine` (screen capture), `InputDriver` (hardware input), `ConfigLoader`
- **Perception Layer**: `ObjectDetector` (YOLO), `StateReader` (UI analysis), `CoordinateMapper` (2.5D mapping)
- **Decision Layer**: `WorldModel` (context), `BotFSM` (state machine), `PathPlanner`
- **Application Layer**: `MainLoop`, `OverlaySystem` (debug), `WatchDog` (F12 emergency stop)

### Data Flow (Per Frame)

1. **Input**: `CaptureEngine` grabs frame → RawFrame (1920x1080 BGR)
2. **Perception**: `ObjectDetector` + `StateReader` → ContextData (monsters, position, HP)
3. **Decision**: `BotFSM` + `PathPlanner` → ActionCommand (MOVE, ATTACK, SKILL, PICKUP)
4. **Execution**: `InputDriver` with random delays → hardware signals

### Core Game Logic: 2.5D Alignment

DNF combat uses a "Y-axis alignment" mechanic - you must align with monsters on the Y-axis (depth) before attacking. This is critical for all combat logic.

```
1. Y-align first (move UP/DOWN until within tolerance)
2. X-approach (move LEFT/RIGHT within attack range)
3. Attack combo (face target, execute skills)
```

## Project Structure

```
AradVision/
├── assets/                 # Static resources (model .pt files, image templates)
├── configs/                # YAML configuration files
├── core/                   # Core architecture
│   ├── capture.py          # Screen capture implementation
│   ├── input.py            # Input driver implementation
│   └── types.py            # Data class definitions (GameObject, Context)
├── logic/                  # Business logic
│   ├── bot_fsm.py          # Finite state machine
│   └── strategies.py       # Specific strategies (dungeon, combat)
├── vision/                 # Vision algorithms
│   ├── detector.py         # YOLO wrapper
│   └── ocr.py              # Text recognition (if needed)
├── main.py                 # Entry point
└── tests/                  # Unit tests
```

## Mandatory Coding Standards

### Type Hints [REQUIRED]
All functions MUST have parameter and return types:

```python
from typing import List, Optional
import numpy as np

def find_monster(frame: np.ndarray) -> List[GameObject]:
    # ...
    return results
```

### Naming Conventions
- Modules: `snake_case` (e.g., `vision_core.py`)
- Classes: `PascalCase` (e.g., `YoloDetector`)
- Functions/variables: `snake_case` (e.g., `detect_objects()`)
- Constants: `UPPER_CASE` (e.g., `MAX_RETRIES`)
- Private members: `_snake_case` (e.g., `_load_model()`)

### Domain-specific abbreviations:
- `img` / `frame`: OpenCV image matrix
- `bbox`: Bounding Box (x1, y1, x2, y2)
- `conf`: Confidence score
- `ctx`: Context object
- `hwnd`: Window Handle

### Documentation
- Use **Google-style docstrings** for all functions
- Comments explain "why", not "what"
- For complex algorithms (especially Y-axis correction), explain the principle

```python
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

### Logging
**NEVER use `print()`**. Use `loguru`:

```python
from loguru import logger

logger.debug("Model loading...")              # Development
logger.info("Dungeon cleared in 45s")         # Key milestones
logger.warning("Target lost, re-searching")   # Non-fatal errors
logger.error("Capture failed: invalid hwnd")   # Fatal errors
```

### Configuration
**NO magic numbers in code**. All thresholds, coordinates, key bindings must be in `config.yaml`.

## Critical Safety & Anti-Cheat Requirements

### 1. Randomization [MANDATORY]
All timing must use random distributions to avoid detection:

```python
import random
import time

# NO: time.sleep(0.1)
# YES: time.sleep(random.uniform(0.08, 0.12))
```

### 2. Input Simulation
- Use `SendInput` (Win32 API) with DirectX scan codes - DNF blocks high-level virtual keys
- Input must be: press → wait (random) → release (no pulse signals)
- NO `pyautogui` instant mouse teleportation

### 3. Kill Switch [CRITICAL]
The F12 emergency stop must be implemented as a daemon thread that can interrupt ANY loop:

```python
def check_kill_switch():
    while True:
        if keyboard.is_pressed('F12'):
            os._exit(0)  # Force kill, NOT break
        time.sleep(0.1)
```

### 4. No Memory Injection
**ABSOLUTELY FORBIDDEN**: `WriteProcessMemory`, `ReadProcessMemory`, or any DLL injection. This is a vision-only system.

## Performance Requirements

- Target FPS: ≥30
- End-to-end latency: <150ms
- Model inference: <30ms per frame
- CPU usage: ≤40%
- GPU memory: ≤2GB

Use FP16 (half-precision) inference for YOLOv8 to reduce memory and increase speed.

## Development Stages

1. **Mock Stage**: Test detection and FSM logic with screenshot folders (no game running)
2. **Input Test Stage**: Test `InputAdapter` in training room (character can move and attack)
3. **Integration Stage**: Full flow in "Loren" dungeon (beginner dungeon)
4. **Production**: Optimized for actual use

## Core Data Models

```python
@dataclass
class GameObject:
    id: int                    # Unique tracking ID (optional)
    cls_id: int                # Class ID (0: Monster, 1: Hero, 2: Item, 3: Gate)
    cls_name: str              # Class name
    conf: float                # Confidence (0.0-1.0)
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)

    @property
    def center(self) -> Tuple[int, int]:
        """Geometric center (cx, cy)"""
        return ((self.bbox[0] + self.bbox[2]) // 2, (self.bbox[1] + self.bbox[3]) // 2)

    @property
    def foot_point(self) -> Tuple[int, int]:
        """Ground position (fx, fy) - CRITICAL for Y-axis alignment"""
        cx = (self.bbox[0] + self.bbox[2]) // 2
        fy = int(self.bbox[3] * 0.95 + self.bbox[1] * 0.05)
        return (cx, fy)

@dataclass
class GameContext:
    frame_index: int
    timestamp: float
    hero: GameObject | None
    monsters: list[GameObject]
    items: list[GameObject]
    doors: list[GameObject]
    hp_percent: float
    room_cleared: bool
```

## Bot FSM States

```python
class State(Enum):
    IDLE = 0        # Idle/loading
    COMBAT = 1      # Combat (target, move, attack)
    LOOT = 2        # Pick up items
    NAVIGATE = 3    # Navigate to next room
    RECOVERY = 4    # Exception recovery (stuck/low HP)
```

## Import Order

```python
# 1. Standard library
import os
import time
import threading

# 2. Third-party libraries (CV, ML, System)
import cv2
import numpy as np
import win32gui
from ultralytics import YOLO

# 3. Local modules
from core.utils import load_config
from data.models import GameObject
```

## Git Commit Message Format

- `feat: Add YOLOv8 inference module`
- `fix: Fix Y-axis alignment tolerance too strict`
- `docs: Update installation documentation`
- `refactor: Refactor InputDriver class`

---

## Development Workflow [MANDATORY]

### After Code Changes

**Every time project code is modified**, follow this workflow:

#### 0. Code Validation [MANDATORY]
**在提交代码之前，必须进行语法和引用检查**：

```bash
# 检查 Python 文件语法
python3 -m py_compile <modified_file>.py

# 检查多个文件
find . -name "*.py" -path "./<module>/*" -exec python3 -m py_compile {} \;

# 或使用 pylint/flake8 进行更深入的检查（可选）
pylint <modified_file>.py
flake8 <modified_file>.py
```

**验证要求**：
- ✅ 所有修改的 `.py` 文件必须通过 `py_compile` 检查
- ✅ 如果存在导入错误（如 `NameError: name 'Signal' is not defined`），必须修复后才能提交
- ✅ 确保信号类使用 `pyqtSignal` 而非 `Signal`
- ✅ 确保类型提示正确，避免循环引用

#### 1. Summarize Work
- Create/update work summary document
- Document what was done and why
- List files modified and changes made
- Record any bugs fixed

#### 2. Git Commit
- **ALWAYS commit** after code changes
- Use proper commit message format (see above)
- Include `Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>`
- Verify commit was successful

#### 3. Push to Remote
- **ALWAYS push** after successful commit
- Use `git push` to sync with remote
- Verify push completed without errors

### Workflow Template

```bash
# Step 0: Code Validation (MANDATORY)
python3 -m py_compile <modified_files>

# Step 1: Check status
git status

# Step 2: Add files
git add <modified_files>

# Step 3: Commit with proper message
git commit -m "<type>: <description>

# Step 4: Push to remote
git push
```

### Commit Type Guidelines

| Type | When to Use | Example |
|-------|--------------|----------|
| `feat` | New feature | `feat: Add skill list drag-drop sorting` |
| `fix` | Bug fix | `fix: Repair missing QHBoxLayout import` |
| `docs` | Documentation only | `docs: Update testing guide` |
| `refactor` | Code refactoring | `refactor: Simplify config loader` |
| `test` | Adding tests | `test: Add coordinate mapper tests` |
| `style` | Code style changes | `style: Fix indentation in main.py` |

### Prohibited Actions

- ❌ **NEVER leave uncommitted changes** when ending session
- ❌ **NEVER push without committing first**
- ❌ **NEVER use generic commit messages** (e.g., "update", "fix bug")
- ❌ **NEVER commit unrelated changes together** (group by feature/fix)

### Session End Checklist

Before ending any development session, ensure:

- [ ] All modified files passed `py_compile` syntax check
- [ ] All code changes committed
- [ ] All commits pushed to remote
- [ ] Work summary documented
- [ ] Working tree clean (`git status` shows nothing)
- [ ] Remote branch up to date (`git status` shows "up to date")
