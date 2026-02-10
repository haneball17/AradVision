# AradVision 模块分配与协作方案

**项目**: AradVision - DNF 视觉辅助自动化系统
**开发周期**: 3天MVP + 7天完整产品
**开发者**: haneball17, yangmq17
**角色**: 系统架构与逻辑工程师

---

## 一、模块分配总览

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           模块分配矩阵                                   │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  haneball17                              yangmq17                        │
│  ┌──────────────────┐                  ┌──────────────────┐             │
│  │  基础设施层       │                  │  核心数据模型     │             │
│  ├──────────────────┤                  ├──────────────────┤             │
│  │ • ConfigLoader   │                  │ • GameObject     │             │
│  │ • CaptureEngine  │                  │ • GameContext    │             │
│  │ • LogSystem      │                  │ • Command        │             │
│  └──────────────────┘                  └──────────────────┘             │
│                                                                          │
│  ┌──────────────────┐                  ┌──────────────────┐             │
│  │  感知层           │                  │  执行层           │             │
│  ├──────────────────┤                  ├──────────────────┤             │
│  │ • BaseDetector   │                  │ • InputDriver    │             │
│  │ • YoloDetector   │                  │ • KillSwitch     │             │
│  │ • MockYoloDetector│                  │ • MockInputDriver│             │
│  │ • StateReader    │                  │                  │             │
│  │ • CoordinateMapper│                 │                  │             │
│  └──────────────────┘                  └──────────────────┘             │
│                                                                          │
│  ┌──────────────────┐                  ┌──────────────────┐             │
│  │  决策层           │                  │  决策层           │             │
│  ├──────────────────┤                  ├──────────────────┤             │
│  │ • WorldModel     │                  │ • BotFSM         │             │
│  │                 │                  │ • CombatLogic    │             │
│  │                 │                  │ • PathPlanner    │             │
│  └──────────────────┘                  └──────────────────┘             │
│                                                                          │
│  ┌──────────────────┐                  ┌──────────────────┐             │
│  │  应用层           │                  │  安全与工具       │             │
│  ├──────────────────┤                  ├──────────────────┤             │
│  │ • MainLoop       │                  │ • WatchDog       │             │
│  │ • OverlaySystem  │                  │ • 异常处理       │             │
│  │                 │                  │ • 单元测试框架   │             │
│  └──────────────────┘                  └──────────────────┘             │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 二、详细模块任务分配

### haneball17 - 模块清单

| 模块名 | 文件路径 | 优先级 | 预计工时 | 依赖 |
|--------|----------|--------|----------|------|
| **ConfigLoader** | `core/config_loader.py` | P0 | 2h | 无 |
| **CaptureEngine** | `core/capture.py` | P0 | 4h | ConfigLoader |
| **BaseDetector** | `vision/base_detector.py` | P0 | 1h | core/types.py |
| **MockYoloDetector** | `vision/mock_detector.py` | P0 | 2h | BaseDetector |
| **YoloDetector** | `vision/detector.py` | P1 | 2h | BaseDetector |
| **StateReader** | `vision/state_reader.py` | P1 | 3h | CaptureEngine |
| **CoordinateMapper** | `vision/coordinate_mapper.py` | P1 | 2h | core/types.py |
| **WorldModel** | `logic/world_model.py` | P1 | 2h | core/types.py |
| **MainLoop** | `main.py` | P0 | 4h | 所有模块 |
| **OverlaySystem** | `app/overlay.py` | P2 | 3h | MainLoop |

**关键职责**:
- 视觉感知管道 (Screen → Detection)
- 系统主循环与生命周期管理
- 配置管理与日志系统

---

### yangmq17 - 模块清单

| 模块名 | 文件路径 | 优先级 | 预计工时 | 依赖 |
|--------|----------|--------|----------|------|
| **核心数据模型** | `core/types.py` | P0 | 3h | 无 |
| **InputDriver** | `input/input_driver.py` | P0 | 4h | core/types.py |
| **KillSwitch** | `input/kill_switch.py` | P0 | 2h | 无 |
| **MockInputDriver** | `input/mock_driver.py` | P0 | 1h | InputDriver |
| **BotFSM** | `logic/bot_fsm.py` | P0 | 4h | core/types.py |
| **CombatLogic** | `logic/combat.py` | P0 | 4h | BotFSM, core/types.py |
| **PathPlanner** | `logic/path_planner.py` | P1 | 3h | core/types.py |
| **WatchDog** | `app/watchdog.py` | P0 | 2h | KillSwitch |
| **异常处理** | `core/exceptions.py` | P0 | 1h | 无 |
| **单元测试框架** | `tests/conftest.py` | P1 | 2h | pytest |

**关键职责**:
- 核心数据结构与类型定义
- 输入控制与安全机制
- 业务逻辑与决策算法
- 测试基础设施

---

## 三、开发依赖关系图

```
                    Day 1 早上                    Day 1 下午
                       │                            │
           ┌───────────┴───────────┐    ┌───────────┴───────────┐
           │                       │    │                       │
    yangmq17:             haneball17:      yangmq17:            haneball17:
    core/types.py         ConfigLoader     InputDriver          CaptureEngine
    exceptions.py         LogSystem        KillSwitch           BaseDetector
                                                            MockYoloDetector
                       │                            │
                       └────────────┬───────────────┘
                                    │
                             Day 2 全天
                                    │
        yangmq17:                              haneball17:
        BotFSM (依赖types)                      StateReader (依赖Capture)
        CombatLogic (依赖FSM, types)            CoordinateMapper (依赖types)
                                                WorldModel (依赖types)
                                    │
                             Day 2 晚上
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
            yangmq17:                        haneball17:
            完成决策层                        完成感知层
            编写测试用例                      编写测试用例
                                    │
                             Day 3 早上
                                    │
                    ┌───────────────┴───────────────┐
                    │         首次集成              │
                    │   haneball17 + yangmq17       │
                    └───────────────┬───────────────┘
                                    │
                             MainLoop集成
                             Mock数据流测试
                                    │
                             Day 3 下午
                                    │
                    ┌───────────────┴───────────────┐
                    │        真实环境测试           │
                    │   (使用MockYoloDetector)      │
                    └───────────────┬───────────────┘
                                    │
                               MVP验收
```

---

## 四、接口契约

### 4.1 核心数据模型 (yangmq17 提供)

```python
# core/types.py
from dataclasses import dataclass
from typing import Tuple, List, Optional
from enum import Enum

class CommandType(Enum):
    MOVE = "move"
    ATTACK = "attack"
    SKILL = "skill"
    PICKUP = "pickup"
    STOP = "stop"

@dataclass
class BBox:
    """边界框"""
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1

    @property
    def center(self) -> Tuple[int, int]:
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

@dataclass
class GameObject:
    """游戏对象"""
    id: int
    cls_id: int
    cls_name: str
    conf: float
    bbox: BBox

    @property
    def foot_point(self) -> Tuple[int, int]:
        """落地坐标 - Y轴对齐的关键"""
        cx = self.bbox.center[0]
        fy = int(self.bbox.y2 * 0.95 + self.bbox.y1 * 0.05)
        return (cx, fy)

@dataclass
class GameContext:
    """游戏上下文 - 每帧状态快照"""
    frame_index: int
    timestamp: float
    hero: Optional[GameObject]
    monsters: List[GameObject]
    items: List[GameObject]
    doors: List[GameObject]
    hp_percent: float
    mp_percent: float
    room_cleared: bool

@dataclass
class Command:
    """动作指令"""
    action_type: CommandType
    direction: Optional[Tuple[int, int]] = None  # (dx, dy)
    key_code: Optional[str] = None
    duration: float = 0.0
```

### 4.2 检测器接口 (haneball17 提供)

```python
# vision/base_detector.py
from abc import ABC, abstractmethod
from core.types import GameObject
import numpy as np

class BaseDetector(ABC):
    """检测器抽象基类"""

    @abstractmethod
    def detect(self, frame: np.ndarray) -> List[GameObject]:
        """
        检测帧中的对象

        Args:
            frame: OpenCV图像 (BGR格式)

        Returns:
            GameObject列表
        """
        pass

    @abstractmethod
    def load_model(self, model_path: str) -> bool:
        """加载模型"""
        pass
```

### 4.3 输入驱动接口 (yangmq17 提供)

```python
# input/input_driver.py
from core.types import Command
from abc import ABC, abstractmethod

class BaseInputDriver(ABC):
    """输入驱动抽象基类"""

    @abstractmethod
    def execute(self, command: Command) -> bool:
        """
        执行指令

        Args:
            command: 要执行的指令

        Returns:
            是否执行成功
        """
        pass

    @abstractmethod
    def tap(self, key: str) -> bool:
        """短按按键"""
        pass

    @abstractmethod
    def hold(self, key: str, duration: float) -> bool:
        """长按按键"""
        pass
```

### 4.4 状态机接口 (yangmq17 提供)

```python
# logic/bot_fsm.py
from core.types import GameContext, Command
from enum import Enum

class BotState(Enum):
    IDLE = 0
    COMBAT = 1
    LOOT = 2
    NAVIGATE = 3
    RECOVERY = 4

class BotFSM:
    """有限状态机"""

    def __init__(self):
        self.current_state = BotState.IDLE
        self.state_history: List[BotState] = []

    def update(self, ctx: GameContext) -> Command:
        """
        根据上下文更新状态并返回指令

        Args:
            ctx: 当前游戏上下文

        Returns:
            要执行的指令
        """
        # 状态转换逻辑
        # 返回对应指令
        pass
```

---

## 五、Mock实现规范

### 5.1 MockYoloDetector (haneball17)

```python
# vision/mock_detector.py
from vision.base_detector import BaseDetector
from core.types import GameObject, BBox
import numpy as np
import json
from pathlib import Path

class MockYoloDetector(BaseDetector):
    """Mock YOLO检测器 - 用于开发测试"""

    def __init__(self, mock_data_path: str = None):
        self.mock_data_path = mock_data_path
        self.mock_results = {}

        if mock_data_path and Path(mock_data_path).exists():
            with open(mock_data_path, 'r') as f:
                self.mock_results = json.load(f)

    def detect(self, frame: np.ndarray) -> List[GameObject]:
        """
        返回预设的Mock数据

        如果有mock_data_file，从文件读取
        否则返回固定的测试数据
        """
        # 生成固定的测试数据
        return [
            GameObject(
                id=1,
                cls_id=0,
                cls_name="monster",
                conf=0.85,
                bbox=BBox(x1=400, y1=300, x2=500, y2=450)
            )
        ]

    def load_model(self, model_path: str) -> bool:
        """Mock实现 - 总是返回True"""
        return True
```

### 5.2 MockInputDriver (yangmq17)

```python
# input/mock_driver.py
from input.input_driver import BaseInputDriver
from core.types import Command
from typing import List

class MockInputDriver(BaseInputDriver):
    """Mock输入驱动 - 记录指令但不实际发送"""

    def __init__(self):
        self.command_history: List[Command] = []

    def execute(self, command: Command) -> bool:
        """记录指令到历史"""
        self.command_history.append(command)
        return True

    def tap(self, key: str) -> bool:
        """记录按键"""
        self.command_history.append(
            Command(action_type=CommandType.ATTACK, key_code=key)
        )
        return True

    def hold(self, key: str, duration: float) -> bool:
        """记录长按"""
        self.command_history.append(
            Command(action_type=CommandType.MOVE, key_code=key, duration=duration)
        )
        return True

    def get_history(self) -> List[Command]:
        """获取指令历史 - 用于测试验证"""
        return self.command_history

    def clear_history(self):
        """清空历史"""
        self.command_history.clear()
```

---

## 六、协作规范

### 6.1 每日工作流

```
┌─────────────────────────────────────────────────────────────────┐
│                    每日协作流程                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  09:00  ──►  各自开始今日任务                                    │
│                                                                  │
│  12:00  ──►  午餐休息                                           │
│                                                                  │
│  14:00  ──►  继续开发                                           │
│              ┌─────────────────────────────────────┐             │
│              │  遇到接口问题?                       │             │
│              │  → 立即沟通确认                      │             │
│              │  → 更新接口文档                      │             │
│              └─────────────────────────────────────┘             │
│                                                                  │
│  18:00  ──►  代码提交与Pull Request                             │
│              ┌─────────────────────────────────────┐             │
│              │  提交前检查清单:                     │             │
│              │  ✓ 单元测试通过                      │             │
│              │  ✓ 代码符合规范                      │             │
│              │  ✓ 接口文档已更新                    │             │
│              └─────────────────────────────────────┘             │
│                                                                  │
│  20:00  ──►  每日同步会议 (15-30分钟)                            │
│              ┌─────────────────────────────────────┐             │
│              │  会议内容:                           │             │
│              │  1. 演示今日成果                     │             │
│              │  2. 代码审查                         │             │
│              │  3. 确认明日计划                     │             │
│              │  4. 阻塞问题讨论                     │             │
│              └─────────────────────────────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Git分支策略

```bash
# 主分支
main (或 master)        # 稳定的可运行版本

# 开发分支
dev                     # 开发集成分支

# 个人分支
feature/haneball17-<module>     # haneball17的功能分支
feature/yangmq17-<module>       # yangmq17的功能分支

# 工作流程
1. 从dev创建个人分支
   git checkout -b feature/haneball17-capture

2. 开发完成后提交
   git add .
   git commit -m "feat: 实现CaptureEngine"

3. 推送到远程
   git push origin feature/haneball17-capture

4. 创建Pull Request到dev分支
   (yangmq17审查haneball17的代码，反之亦然)

5. 审查通过后合并到dev

6. 每天晚上将dev合并到main
```

### 6.3 代码审查清单

haneball17 审查 yangmq17 的代码时检查:

- [ ] 数据模型定义完整 (GameObject, GameContext, Command)
- [ ] 输入驱动的随机延迟实现正确
- [ ] FSM状态转换逻辑正确
- [ ] Y轴对齐算法符合需求
- [ ] 异常处理完善
- [ ] 单元测试覆盖核心逻辑

yangmq17 审查 haneball17 的代码时检查:

- [ ] 配置加载正确处理异常
- [ ] 截图性能满足要求 (<5ms)
- [ ] Mock检测器接口正确
- [ ] 坐标映射算法正确
- [ ] 主循环帧率控制准确
- [ ] 日志输出规范使用loguru

---

## 七、集成与测试计划

### Day 2 晚上 - 第一次集成

```bash
# 目标: 使用全Mock环境测试数据流

# 1. yangmq17 准备测试用例
# tests/integration/test_full_flow_mock.py

def test_full_flow_with_mocks():
    """测试完整数据流 - 全Mock"""
    # 初始化Mock组件
    detector = MockYoloDetector()
    driver = MockInputDriver()
    fsm = BotFSM()

    # 模拟游戏帧
    frame = np.zeros((600, 800, 3), dtype=np.uint8)

    # 1. 检测
    objects = detector.detect(frame)
    assert len(objects) > 0

    # 2. 构建上下文
    ctx = GameContext(
        frame_index=0,
        timestamp=time.time(),
        hero=None,
        monsters=objects,
        items=[],
        doors=[],
        hp_percent=1.0,
        mp_percent=1.0,
        room_cleared=False
    )

    # 3. 决策
    cmd = fsm.update(ctx)
    assert cmd is not None

    # 4. 执行
    driver.execute(cmd)

    # 5. 验证
    history = driver.get_history()
    assert len(history) > 0
```

### Day 3 早上 - 真实模块替换

```bash
# 1. haneball17 实现真实检测器接口
# vision/detector.py

class YoloDetector(BaseDetector):
    def __init__(self, weights_path: str):
        self.model = YOLO(weights_path)

    def detect(self, frame: np.ndarray) -> List[GameObject]:
        results = self.model(frame)
        # 转换为GameObject列表
        # ...

# 2. 一行切换: Mock → Real
# main.py

# 开发阶段
# detector = MockYoloDetector()

# 集成阶段 (取消注释)
detector = YoloDetector(weights="assets/weights/yolov8n_dnf.pt")
```

---

## 八、风险与应对

| 风险 | 负责人 | 应对方案 |
|------|--------|----------|
| 接口定义不一致 | 两人 | 每天早上10分钟同步接口变更 |
| Git冲突频发 | 两人 | 频繁合并，使用明确的模块边界 |
| 依赖关系阻塞 | haneball17 | 优先实现被依赖的模块 (types.py, ConfigLoader) |
| 测试不充分 | yangmq17 | 每个模块完成后立即编写测试 |
| 性能不达标 | haneball17 | 使用性能分析工具定位瓶颈 |

---

## 九、成功标准

### Day 1 验收

- [ ] haneball17: ConfigLoader可用
- [ ] haneball17: CaptureEngine可截图
- [ ] haneball17: MockYoloDetector实现
- [ ] yangmq17: 核心数据模型定义完成
- [ ] yangmq17: InputDriver可用
- [ ] yangmq17: KillSwitch可监听F12
- [ ] 两人: 代码可在各自环境运行

### Day 2 验收

- [ ] haneball17: StateReader可读取HP
- [ ] haneball17: CoordinateMapper可映射坐标
- [ ] yangmq17: BotFSM状态转换正确
- [ ] yangmq17: CombatLogic Y轴对齐正确
- [ ] 两人: 单元测试通过
- [ ] 两人: 集成测试通过

### Day 3 验收 (MVP)

- [ ] haneball17: MainLoop主循环运行
- [ ] yangmq17: 完整业务逻辑可用
- [ ] 两人: 系统能连接游戏窗口
- [ ] 两人: 能识别屏幕对象 (使用Mock)
- [ ] 两人: 能生成正确指令
- [ ] 两人: F12紧急停止有效
- [ ] 两人: **MVP验收通过**

---

**编制人**: Claude Code
**日期**: 2024-XX-XX
**批准**: haneball17, yangmq17
