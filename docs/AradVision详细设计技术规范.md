
# 详细设计技术规范 (Technical Design Document)

 **项目名称** ：AradVision - DNF 视觉辅助自动化系统

 **文档标识** ：ARAD-VIS-005

 **版本** ：V1.0

 **状态** ：执行中 (Active)

 **最后更新** ：2026-02-10

---

## 1. 系统架构概览 (System Context)

本系统采用 **单进程多模块** 架构，主循环（Main Loop）以 30Hz 的频率运行。系统由三个核心包（Package）组成：

1. `vision`: 负责图像采集与推理。
2. `logic`: 负责状态管理与路径规划。
3. `input`: 负责底层硬件信号模拟。

---

## 2. 数据模型与类型定义 (Data Models)

为了保证模块间解耦，我们首先定义核心数据结构（Data Class）。

### 2.1 游戏对象 (GameObject)

用于描述屏幕上识别到的任何实体。

**Python**

```
from dataclasses import dataclass
from typing import Tuple

@dataclass
class GameObject:
    id: int                     # 对象的唯一追踪ID (可选，用于多帧追踪)
    cls_id: int                 # 类别ID (0: Monster, 1: Hero, 2: Item, 3: Gate)
    cls_name: str               # 类别名称 ('goblin', 'item_gold')
    conf: float                 # 置信度 (0.0 - 1.0)
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
  
    @property
    def center(self) -> Tuple[int, int]:
        """返回几何中心 (cx, cy)"""
        return ((self.bbox[0] + self.bbox[2]) // 2, (self.bbox[1] + self.bbox[3]) // 2)

    @property
    def foot_point(self) -> Tuple[int, int]:
        """
        [关键逻辑] 返回落地坐标 (fx, fy)。
        逻辑：取 BBox 底部中心，并向上修正 5% (避免判定点过低)。
        """
        cx = (self.bbox[0] + self.bbox[2]) // 2
        fy = int(self.bbox[3] * 0.95 + self.bbox[1] * 0.05) 
        return (cx, fy)
```

### 2.2 游戏上下文 (GameContext)

每一帧流转的全局状态快照。

**Python**

```
@dataclass
class GameContext:
    frame_index: int            # 当前帧号
    timestamp: float            # 当前时间戳
    hero: GameObject | None     # 玩家自身对象
    monsters: list[GameObject]  # 怪物列表
    items: list[GameObject]     # 物品列表
    doors: list[GameObject]     # 门列表
    hp_percent: float           # 血量百分比 (0.0 - 1.0)
    room_cleared: bool          # 当前房间是否清空
```

---

## 3. 核心模块详细设计 (Module Specifications)

### 3.1 视觉模块 (`vision`)

#### 类：`ScreenCapture`

* **职责** ：高性能屏幕截取。
* **依赖** ：`mss`, `pywin32`
* **接口** ：
* `__init__(window_title: str)`: 初始化时查找句柄，计算 Client Area（去除标题栏）。
* `grab() -> np.ndarray`: 返回 BGR 格式的 numpy 数组。如果窗口最小化或遮挡，抛出 `CaptureError`。

#### 类：`YoloDetector`

* **职责** ：目标检测。
* **依赖** ：`ultralytics.YOLO`
* **配置** ：`model_path`, `conf_thres=0.6`, `iou_thres=0.45`
* **接口** ：
* `detect(frame: np.ndarray) -> List[GameObject]`:
  1. 执行 `self.model(frame, verbose=False)`。
  2. 解析 `result.boxes`。
  3. 过滤掉置信度低于阈值的对象。
  4. 将 Tensor 转换为 `GameObject` 实例。

### 3.2 逻辑模块 (`logic`)

#### 类：`BotFSM` (有限状态机)

* **职责** ：决策每一帧该做什么。
* **状态枚举** ：
  **Python**

```
  class State(Enum):
      IDLE = 0        # 待机/加载中
      COMBAT = 1      # 战斗（索敌、移动、攻击）
      LOOT = 2        # 拾取物品
      NAVIGATE = 3    # 寻找下一房间
      RECOVERY = 4    # 异常恢复（卡死/血量低）
```

* **核心方法 `update(ctx: GameContext) -> Command`** ：
* **逻辑流** ：
  1.  **检查生存** ：If `ctx.hp < 0.3` -> Return `USE_POTION`。
  1.  **状态转换** ：
  * If `len(ctx.monsters) > 0` -> State = `COMBAT`.
  * Elif `len(ctx.items) > 0` -> State = `LOOT`.
  * Else -> State = `Maps`.
    1.  **执行子逻辑** ：调用 `CombatLogic` 或 `MoveLogic`。

#### 算法：2.5D 对齐与索敌 (Combat Logic)

这是本项目的核心业务逻辑。

**Python**

```
def decide_combat_action(hero: GameObject, monster: GameObject) -> Command:
    # 阈值常量
    Y_ALIGN_TOLERANCE = 15  # Y轴允许误差像素
    ATTACK_RANGE_X = 120    # X轴攻击距离像素

    dx = monster.foot_point[0] - hero.foot_point[0]
    dy = monster.foot_point[1] - hero.foot_point[1]

    # 1. 优先 Y 轴对齐 (错位攻击机制)
    if abs(dy) > Y_ALIGN_TOLERANCE:
        direction = 'DOWN' if dy > 0 else 'UP'
        return Command(type='MOVE', dir=direction, duration=0.1)

    # 2. Y 轴对齐后，X 轴逼近
    if abs(dx) > ATTACK_RANGE_X:
        direction = 'RIGHT' if dx > 0 else 'LEFT'
        # 同时按住跑动键 (双击或长按)
        return Command(type='MOVE_RUN', dir=direction, duration=0.1)

    # 3. 距离合适，保持朝向并攻击
    # 确保朝向正确
    face_dir = 'RIGHT' if dx > 0 else 'LEFT'
    # 简单的攻击循环：XXX + 技能
    return Command(type='ATTACK_COMBO', face=face_dir)
```

### 3.3 输入模块 (`input`)

#### 类：`InputAdapter`

* **职责** ：屏蔽底层驱动差异，提供语义化接口。
* **实现细节** ：
* 使用 `SendInput` (Win32 API) 而非高层库。
* 维护 `SCANCODE_MAPPING` 表（如 `DIK_UP = 0xC8`）。
* **接口** ：
* `tap(key: str)`: 按下 -> `random_sleep(0.05, 0.1)` -> 弹起。
* `hold(key: str, duration: float)`: 按下 -> sleep(duration) -> 弹起。
* `move_mouse(x, y)`: (可选，部分UI交互需要)。

---

## 4. 错误处理与安全机制 (Error Handling)

### 4.1 异常捕获策略

主循环必须包裹在 `try...except` 块中，防止单帧推理失败导致程序崩溃。

**Python**

```
try:
    # Main Loop
    ctx = vision.capture_and_detect()
    cmd = logic.think(ctx)
    input.execute(cmd)
except CaptureError:
    logger.warning("截图失败，等待重试...")
    time.sleep(1)
except DeviceLostError:
    logger.error("游戏窗口丢失，暂停脚本")
    pause_script()
except Exception as e:
    logger.exception(f"未处理的运行时错误: {e}")
```

### 4.2 熔断机制 (Watchdog)

* **实现** ：启动一个 `Daemon Thread` 监听键盘。
* **逻辑** ：
  **Python**

```
  def check_kill_switch():
      while True:
          if keyboard.is_pressed('F12'):
              os._exit(0)  # 强制杀进程，不要用 break
          time.sleep(0.1)
```

### 4.3 防卡死 (Unstuck)

* **检测** ：`Logic` 模块维护一个 `position_history` 队列（长度 30，即 1 秒）。
* **判定** ：如果标准差 `std(position_history) < 5px` 且当前指令是 `MOVE`。
* **对策** ：触发 `RandomEscape` 动作（如：按住下+跳跃，或者后跳）。

---

## 5. 配置文件规范 (`config.yaml`)

**YAML**

```
system:
  fps_limit: 30
  debug_window: true  # 是否显示 CV 调试画面
  log_level: "INFO"

game:
  window_title: "Dungeon & Fighter"
  class_names: ["monster", "hero", "item", "gate"]

vision:
  model_path: "./assets/weights/dnf_v1.pt"
  conf_threshold: 0.65
  y_align_tolerance: 15

keys:
  attack: "x"
  skill_1: "a"
  skill_2: "s"
  potion: "1"
  buff: "space"
```

---

## 6. 开发与测试计划

1. **Stage 1 (Mock)** : 不打开游戏，使用截图文件夹作为输入，测试 `YoloDetector` 和 `BotFSM` 的逻辑输出是否符合预期。
2. **Stage 2 (Input Test)** : 打开游戏修炼场，运行 `InputAdapter` 测试脚本，确认角色能跑能打。
3. **Stage 3 (Integration)** : 开启全流程，在“洛兰”副本进行实地测试。

---

 **批准人** ：haneball17

 **日期** ：2026-02-10
