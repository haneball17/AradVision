# AradVision 模块接口契约规范
# Module Interface Contract Specification

**项目名称**: AradVision - DNF 视觉辅助自动化系统
**文档标识**: ARAD-VIS-006
**版本**: V1.0
**状态**: 正式版
**最后更新日期**: 2026-02-10
**目标读者**: 多开发团队协作人员

---

## 文档说明

本文档定义了 AradVision 系统中所有模块的**精确接口契约**，包括:
- 完整的 API 签名（使用 Python Type Hints）
- 输入/输出数据结构定义
- 异常处理约定
- 性能契约（最大执行时间）
- 线程安全保证
- 配置参数说明

**重要性**: 这些接口契约是多团队协作的基础，任何模块实现都必须严格遵守本规范。

---

## 目录

1. [核心数据模型](#1-核心数据模型)
2. [基础设施层接口](#2-基础设施层接口)
3. [感知层接口](#3-感知层接口)
4. [决策层接口](#4-决策层接口)
5. [应用层接口](#5-应用层接口)
6. [全局异常定义](#6-全局异常定义)
7. [性能契约汇总](#7-性能契约汇总)

---

## 1. 核心数据模型

所有模块共享的数据结构定义，位于 `src/core/types.py`

### 1.1 GameObject - 游戏对象

```python
from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np

@dataclass
class GameObject:
    """
    屏幕上识别到的任何实体

    线程安全: 是（不可变数据类）
    """
    id: int                       # 对象的唯一追踪ID
    cls_id: int                   # 类别ID (0:Monster, 1:Hero, 2:Item, 3:Gate)
    cls_name: str                 # 类别名称 ('goblin', 'item_gold')
    conf: float                   # 置信度 (0.0 - 1.0)
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2) 边界框
    frame_idx: int                # 首次被检测到的帧索引

    @property
    def center(self) -> Tuple[int, int]:
        """返回几何中心 (cx, cy)"""
        return ((self.bbox[0] + self.bbox[2]) // 2,
                (self.bbox[1] + self.bbox[3]) // 2)

    @property
    def foot_point(self) -> Tuple[int, int]:
        """
        返回落地坐标 (fx, fy)
        逻辑：取 BBox 底部中心，并向上修正 5%

        Returns:
            Tuple[int, int]: 落地坐标 (fx, fy)
        """
        cx = (self.bbox[0] + self.bbox[2]) // 2
        fy = int(self.bbox[3] * 0.95 + self.bbox[1] * 0.05)
        return (cx, fy)

    @property
    def width(self) -> int:
        """对象宽度（像素）"""
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> int:
        """对象高度（像素）"""
        return self.bbox[3] - self.bbox[1]

    def distance_to(self, other: 'GameObject') -> float:
        """计算到另一个对象的欧几里得距离"""
        x1, y1 = self.foot_point
        x2, y2 = other.foot_point
        return np.sqrt((x1-x2)**2 + (y1-y2)**2)
```

### 1.2 GameContext - 游戏上下文

```python
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
import time

class BotState(Enum):
    """机器人状态枚举"""
    IDLE = 0         # 待机/加载中
    COMBAT = 1       # 战斗中
    LOOT = 2         # 拾取物品
    NAVIGATE = 3     # 寻找下一房间
    RECOVERY = 4     # 异常恢复
    PAUSED = 5       # 暂停状态

@dataclass
class GameContext:
    """
    每一帧的全局状态快照

    线程安全: 是（不可变数据类，每帧创建新实例）

    性能约束:
        - 构造时间: < 1ms
        - 序列化大小: < 10KB
    """
    frame_index: int                # 当前帧索引
    timestamp: float                # 当前时间戳 (time.time())
    bot_state: BotState             # 当前机器人状态

    # 检测结果
    hero: Optional[GameObject]      # 玩家自身对象
    monsters: List[GameObject]      # 怪物列表（按距离排序）
    items: List[GameObject]         # 物品列表（按价值排序）
    doors: List[GameObject]         # 门/传送门列表

    # UI 状态读取
    hp_percent: float               # 血量百分比 (0.0 - 1.0)
    mp_percent: float               # 蓝量百分比 (0.0 - 1.0)
    skill_cds: dict[str, float]     # 技能CD字典 {'A': 0.0, 'S': 2.5}

    # 环境状态
    room_cleared: bool              # 当前房间是否清空
    is_in_combat: bool              # 是否处于战斗状态
    current_room_id: Optional[int]  # 当前房间ID

    def get_nearest_monster(self) -> Optional[GameObject]:
        """获取最近的怪物"""
        if not self.monsters:
            return None
        return self.monsters[0]

    def should_use_potion(self) -> bool:
        """判断是否应该使用药水"""
        return self.hp_percent < 0.3

    def is_low_mana(self) -> bool:
        """判断是否蓝量不足"""
        return self.mp_percent < 0.2
```

### 1.3 Command - 动作指令

```python
from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum

class CommandType(Enum):
    """指令类型枚举"""
    # 移动相关
    MOVE = "move"                   # 单次移动（上下左右）
    MOVE_RUN = "move_run"           # 跑动（长按方向键）
    JUMP = "jump"                   # 跳跃
    DASH = "dash"                   # 冲刺/后跳

    # 攻击相关
    ATTACK = "attack"               # 普通攻击
    ATTACK_COMBO = "attack_combo"   # 连招攻击
    SKILL = "skill"                 # 释放技能

    # 物品相关
    PICKUP = "pickup"               # 拾取物品
    USE_POTION = "use_potion"       # 使用药水
    USE_BUFF = "use_buff"           # 使用buff技能

    # 系统相关
    WAIT = "wait"                   # 等待
    NONE = "none"                   # 空操作

@dataclass
class Command:
    """
    动作指令数据结构

    线程安全: 是（不可变数据类）

    性能约束:
        - 序列化时间: < 0.1ms
        - 传输延迟: < 5ms
    """
    cmd_type: CommandType           # 指令类型
    direction: Optional[Tuple[int, int]] = None  # (dx, dy) 方向向量
    key_code: Optional[str] = None  # 按键代码 ('a', 's', 'x', etc.)
    duration: float = 0.0           # 持续时间（秒）
    target_pos: Optional[Tuple[int, int]] = None  # 目标屏幕坐标

    # 随机化参数（防检测）
    add_jitter: bool = True         # 是否添加随机抖动

    def __post_init__(self):
        """后处理：验证参数合法性"""
        if self.duration < 0:
            raise ValueError(f"Duration cannot be negative: {self.duration}")
        if self.cmd_type == CommandType.SKILL and not self.key_code:
            raise ValueError("SKILL command requires key_code")

    @staticmethod
    def move_up(duration: float = 0.1) -> 'Command':
        """创建向上移动指令"""
        return Command(
            cmd_type=CommandType.MOVE,
            direction=(0, -1),
            duration=duration
        )

    @staticmethod
    def move_down(duration: float = 0.1) -> 'Command':
        """创建向下移动指令"""
        return Command(
            cmd_type=CommandType.MOVE,
            direction=(0, 1),
            duration=duration
        )

    @staticmethod
    def move_left(duration: float = 0.1) -> 'Command':
        """创建向左移动指令"""
        return Command(
            cmd_type=CommandType.MOVE,
            direction=(-1, 0),
            duration=duration
        )

    @staticmethod
    def move_right(duration: float = 0.1) -> 'Command':
        """创建向右移动指令"""
        return Command(
            cmd_type=CommandType.MOVE,
            direction=(1, 0),
            duration=duration
        )

    @staticmethod
    def attack(face_right: bool) -> 'Command':
        """创建攻击指令"""
        return Command(
            cmd_type=CommandType.ATTACK,
            direction=(1 if face_right else -1, 0),
            key_code='x'
        )

    @staticmethod
    def skill(key: str) -> 'Command':
        """创建技能指令"""
        return Command(
            cmd_type=CommandType.SKILL,
            key_code=key
        )

    @staticmethod
    def wait(duration: float) -> 'Command':
        """创建等待指令"""
        return Command(
            cmd_type=CommandType.WAIT,
            duration=duration
        )
```

---

## 2. 基础设施层接口

### 2.1 CaptureEngine - 屏幕捕获引擎

**模块路径**: `src/infrastructure/capture.py`

**职责**: 高性能屏幕截取，支持多显示器和窗口裁剪

**依赖**: `mss`, `pywin32`

**线程安全**: 是（独立线程运行）

#### 接口定义

```python
import numpy as np
from typing import Optional, Tuple
import threading
import queue

class CaptureEngine:
    """
    屏幕捕获引擎

    性能契约:
        - grab() 调用延迟: < 5ms (1080p)
        - 帧率稳定性: > 95% 帧在预算时间内完成

    线程安全:
        - 内部使用锁保护窗口句柄
        - 提供线程安全的 grab() 方法

    异常契约:
        - CaptureError: 窗口最小化或被遮挡
        - DeviceLostError: 游戏窗口完全丢失（关闭/崩溃）
    """

    def __init__(
        self,
        window_title: str = "Dungeon & Fighter",
        target_fps: int = 30,
        use_d3d: bool = True
    ):
        """
        初始化捕获引擎

        Args:
            window_title: 游戏窗口标题（用于查找句柄）
            target_fps: 目标捕获帧率
            use_d3d: 是否使用D3D加速（仅Windows）

        Raises:
            WindowNotFoundError: 找不到指定窗口
            InitializationError: 初始化失败
        """
        pass

    def grab(self) -> np.ndarray:
        """
        捕获当前帧

        Returns:
            np.ndarray: BGR格式的图像数组，shape=(H, W, 3)

        Raises:
            CaptureError: 捕获失败（窗口最小化/遮挡）
            DeviceLostError: 窗口句柄失效

        Performance:
            Max execution time: 5ms (1080p), 10ms (4K)
        """
        pass

    def get_window_rect(self) -> Tuple[int, int, int, int]:
        """
        获取窗口边界矩形

        Returns:
            Tuple[int, int, int, int]: (left, top, width, height)

        Raises:
            DeviceLostError: 窗口句柄失效
        """
        pass

    def get_client_area_size(self) -> Tuple[int, int]:
        """
        获取客户区大小（去除标题栏和边框）

        Returns:
            Tuple[int, int]: (width, height)
        """
        pass

    def start_async_capture(self, frame_queue: queue.Queue):
        """
        启动异步捕获线程

        Args:
            frame_queue: 用于传递帧的线程安全队列
                       格式: (timestamp: float, frame: np.ndarray)

        Thread Safety:
            - 此方法启动新的daemon线程
            - frame_queue 必须是线程安全的
        """
        pass

    def stop(self):
        """
        停止捕获引擎

        线程安全: 可以从任何线程调用
        """
        pass

    @property
    def is_ready(self) -> bool:
        """检查捕获引擎是否就绪"""
        pass
```

#### 配置参数

```yaml
# config.yaml
capture:
  window_title: "Dungeon & Fighter"
  target_fps: 30
  use_d3d: true
  # 高级选项
  capture_cursor: false
  monitor_index: 1  # 多显示器时选择
  retry_interval: 1.0  # 捕获失败重试间隔（秒）
```

---

### 2.2 InputDriver - 输入驱动

**模块路径**: `src/infrastructure/input.py`

**职责**: 底层硬件信号模拟，封装 Win32 API

**依赖**: `pydirectinput`, `ctypes`

**线程安全**: 是（使用内部锁序列化操作）

#### 接口定义

```python
from typing import Optional, Dict
import time

class InputDriver:
    """
    输入驱动器

    性能契约:
        - tap() 执行时间: < 50ms (包含随机延迟)
        - hold() 执行时间: duration ± 20ms

    线程安全:
        - 所有方法都是线程安全的
        - 内部使用锁保证操作原子性

    异常契约:
        - InputError: 输入模拟失败
        - InvalidKeyError: 无效的按键代码
    """

    # DirectInput 扫描码映射
    SCANCODE_MAP: Dict[str, int] = {
        'a': 0x1E, 'b': 0x30, 'c': 0x2E, 'd': 0x20, 'e': 0x12,
        'f': 0x21, 'g': 0x22, 'h': 0x23, 'i': 0x17, 'j': 0x24,
        'k': 0x25, 'l': 0x26, 'm': 0x32, 'n': 0x31, 'o': 0x18,
        'p': 0x19, 'q': 0x10, 'r': 0x13, 's': 0x1F, 't': 0x14,
        'u': 0x16, 'v': 0x2F, 'w': 0x11, 'x': 0x2D, 'y': 0x15,
        'z': 0x2C,
        '1': 0x02, '2': 0x03, '3': 0x04, '4': 0x05, '5': 0x06,
        'space': 0x39, 'up': 0xC8, 'down': 0xD0, 'left': 0xCB,
        'right': 0xCD, 'enter': 0x1C, 'escape': 0x01,
    }

    def __init__(
        self,
        enable_jitter: bool = True,
        jitter_mean: float = 0.1,
        jitter_std: float = 0.02
    ):
        """
        初始化输入驱动

        Args:
            enable_jitter: 是否启用随机延迟（反检测）
            jitter_mean: 按键延迟均值（秒）
            jitter_std: 按键延迟标准差（秒）
        """
        pass

    def execute(self, cmd: Command) -> bool:
        """
        执行动作指令

        Args:
            cmd: 要执行的命令

        Returns:
            bool: 是否执行成功

        Raises:
            InputError: 执行失败
            InvalidKeyError: 无效的按键代码

        Performance:
            Max execution time: 100ms (包含随机延迟)

        Thread Safety:
            完全线程安全，支持多线程并发调用
        """
        pass

    def tap(self, key: str, duration: Optional[float] = None) -> bool:
        """
        单次按键（按下->等待->弹起）

        Args:
            key: 按键代码（如 'a', 'space', 'up'）
            duration: 按住时长（秒），None则使用随机值

        Returns:
            bool: 是否成功

        Performance:
            - 快速点击: 50-80ms
            - 长按: duration + 20ms
        """
        pass

    def hold(self, key: str, duration: float) -> bool:
        """
        长按按键

        Args:
            key: 按键代码
            duration: 持续时间（秒）

        Returns:
            bool: 是否成功

        Performance:
            实际时长 = duration ± 20ms
        """
        pass

    def press(self, key: str) -> bool:
        """
        仅按下（不弹起）

        Args:
            key: 按键代码

        Returns:
            bool: 是否成功
        """
        pass

    def release(self, key: str) -> bool:
        """
        仅弹起（假设之前已按下）

        Args:
            key: 按键代码

        Returns:
            bool: 是否成功
        """
        pass

    def move_mouse(self, x: int, y: int, relative: bool = True) -> bool:
        """
        移动鼠标（用于UI交互）

        Args:
            x: X坐标
            y: Y坐标
            relative: 是否相对移动

        Returns:
            bool: 是否成功

        Performance:
            < 10ms
        """
        pass

    def emergency_stop(self):
        """
        紧急停止：释放所有按下的键

        Thread Safety:
            线程安全，可从任何线程调用
        """
        pass
```

#### 配置参数

```yaml
# config.yaml
input:
  # 反检测参数
  enable_jitter: true
  jitter_mean: 0.1      # 按键延迟均值（秒）
  jitter_std: 0.02      # 按键延迟标准差

  # 鼠标设置
  mouse_enabled: false  # 是否启用鼠标控制
  mouse_speed: 1.0      # 鼠标移动速度倍率

  # 高级选项
  use_direct_input: true  # 使用DirectInput而非SendInput
  force_release_on_stop: true  # 停止时强制释放所有键
```

---

### 2.3 ConfigLoader - 配置加载器

**模块路径**: `src/infrastructure/config.py`

**职责**: 加载和管理配置文件

**依赖**: `yaml`, `pathlib`

**线程安全**: 是（单例模式，读多写少）

#### 接口定义

```python
from typing import Any, Dict, Optional
from pathlib import Path
import threading

class ConfigLoader:
    """
    配置加载器（单例模式）

    性能契约:
        - get() 调用时间: < 1ms
        - reload() 执行时间: < 100ms

    线程安全:
        - 完全线程安全
        - 读操作无锁（使用不可变数据）
        - 写操作使用写锁

    异常契约:
        - ConfigError: 配置文件不存在或格式错误
    """
    _instance: Optional['ConfigLoader'] = None
    _lock = threading.Lock()

    def __new__(cls, config_path: str = "config.yaml"):
        """单例模式"""
        pass

    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径

        Raises:
            ConfigError: 配置文件加载失败
        """
        pass

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号路径）

        Args:
            key: 配置键，如 'vision.conf_threshold'
            default: 默认值

        Returns:
            Any: 配置值

        Example:
            >>> config.get('vision.conf_threshold')
            0.65
            >>> config.get('keys.attack')
            'x'
        """
        pass

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取整个配置节

        Args:
            section: 配置节名称

        Returns:
            Dict[str, Any]: 配置字典
        """
        pass

    def set(self, key: str, value: Any) -> None:
        """
        运行时修改配置值

        Args:
            key: 配置键
            value: 新值

        Thread Safety:
            线程安全，使用写锁
        """
        pass

    def reload(self) -> None:
        """
        重新加载配置文件

        Raises:
            ConfigError: 重载失败
        """
        pass

    def save(self, path: Optional[str] = None) -> None:
        """
        保存当前配置到文件

        Args:
            path: 保存路径，None则覆盖原文件
        """
        pass

    @property
    def vision(self) -> Dict[str, Any]:
        """快捷访问：视觉配置"""
        pass

    @property
    def game(self) -> Dict[str, Any]:
        """快捷访问：游戏配置"""
        pass

    @property
    def keys(self) -> Dict[str, Any]:
        """快捷访问：按键配置"""
        pass
```

---

## 3. 感知层接口

### 3.1 ObjectDetector - 目标检测器

**模块路径**: `src/perception/detector.py`

**职责**: 使用 YOLO 模型进行目标检测

**依赖**: `ultralytics`, `torch`, `numpy`

**线程安全**: 是（推理线程独立）

#### 接口定义

```python
import numpy as np
from typing import List, Optional
import torch

class ObjectDetector:
    """
    YOLO 目标检测器

    性能契约:
        - detect() 推理时间: < 30ms (GPU), < 100ms (CPU)
        - 初始化时间: < 3s

    线程安全:
        - detect() 方法是线程安全的
        - 模型加载后不可变

    异常契约:
        - ModelLoadError: 模型加载失败
        - InferenceError: 推理失败（OOM/CUDA错误）
    """

    def __init__(
        self,
        model_path: str,
        conf_threshold: float = 0.65,
        iou_threshold: float = 0.45,
        device: Optional[str] = None,
        half_precision: bool = True
    ):
        """
        初始化检测器

        Args:
            model_path: 模型权重文件路径 (.pt)
            conf_threshold: 置信度阈值 (0.0 - 1.0)
            iou_threshold: IOU阈值 (0.0 - 1.0)
            device: 推理设备 ('cuda:0', 'cpu', None=auto)
            half_precision: 是否使用FP16半精度

        Raises:
            ModelLoadError: 模型文件不存在或加载失败
            DeviceError: 指定设备不可用
        """
        pass

    def detect(self, frame: np.ndarray) -> List[GameObject]:
        """
        执行目标检测

        Args:
            frame: BGR格式的图像数组，shape=(H, W, 3)

        Returns:
            List[GameObject]: 检测到的对象列表，按置信度降序排序

        Raises:
            InferenceError: 推理失败
            InvalidInputError: 输入图像格式错误

        Performance:
            - 1080p GPU: < 30ms
            - 1080p CPU: < 100ms

        Thread Safety:
            多线程安全（模型推理是只读操作）
        """
        pass

    def detect_async(
        self,
        frame: np.ndarray,
        callback: callable
    ) -> None:
        """
        异步检测（在后台线程执行）

        Args:
            frame: 输入图像
            callback: 完成回调函数
                     signature: callback(result: List[GameObject])

        Thread Safety:
            启动新的推理线程
        """
        pass

    def filter_by_class(
        self,
        objects: List[GameObject],
        class_names: List[str]
    ) -> List[GameObject]:
        """
        按类别过滤对象

        Args:
            objects: 对象列表
            class_names: 类别名称列表，如 ['monster', 'hero']

        Returns:
            List[GameObject]: 过滤后的列表
        """
        pass

    def sort_by_distance(
        self,
        objects: List[GameObject],
        reference: GameObject
    ) -> List[GameObject]:
        """
        按距离排序对象

        Args:
            objects: 对象列表
            reference: 参考对象（通常是英雄）

        Returns:
            List[GameObject]: 排序后的列表（近到远）
        """
        pass

    @property
    def class_names(self) -> List[str]:
        """获取模型支持的所有类别名称"""
        pass

    @property
    def device(self) -> torch.device:
        """获取当前推理设备"""
        pass
```

#### 配置参数

```yaml
# config.yaml
vision:
  model_path: "./assets/weights/dnf_v1.pt"
  conf_threshold: 0.65
  iou_threshold: 0.45
  device: "cuda:0"  # 或 "cpu"
  half_precision: true

  # 推理优化
  img_size: 640      # 推理输入尺寸
  augment: false     # 是否启用测试时增强
  agnostic_nms: false  # 类别无关NMS
```

---

### 3.2 StateReader - 状态读取器

**模块路径**: `src/perception/state_reader.py`

**职责**: 从 UI 区域提取游戏状态（HP/MP/技能CD）

**依赖**: `opencv-python`, `numpy`

**线程安全**: 是（无状态操作）

#### 接口定义

```python
import numpy as np
from typing import Dict, Optional, Tuple

class StateReader:
    """
    UI 状态读取器

    性能契约:
        - read_hp() 执行时间: < 5ms
        - read_all() 执行时间: < 20ms

    线程安全:
        完全线程安全（无状态操作）

    异常契约:
        - StateReadError: 状态读取失败
    """

    def __init__(
        self,
        hp_region: Tuple[int, int, int, int],
        mp_region: Tuple[int, int, int, int],
        skill_regions: Dict[str, Tuple[int, int, int, int]],
        hp_color_range: Tuple[Tuple[int, int, int], Tuple[int, int, int]],
        mp_color_range: Tuple[Tuple[int, int, int], Tuple[int, int, int]]
    ):
        """
        初始化状态读取器

        Args:
            hp_region: HP条区域 (x1, y1, x2, y2)
            mp_region: MP条区域 (x1, y1, x2, y2)
            skill_regions: 技能图标区域 {'A': (x1,y1,x2,y2), 'S': ...}
            hp_color_range: HP颜色范围 (HSV下界, HSV上界)
            mp_color_range: MP颜色范围 (HSV下界, HSV上界)
        """
        pass

    def read_hp(self, frame: np.ndarray) -> float:
        """
        读取HP百分比

        Args:
            frame: 游戏画面帧

        Returns:
            float: HP百分比 (0.0 - 1.0)

        Performance:
            Max time: 5ms
        """
        pass

    def read_mp(self, frame: np.ndarray) -> float:
        """
        读取MP百分比

        Args:
            frame: 游戏画面帧

        Returns:
            float: MP百分比 (0.0 - 1.0)
        """
        pass

    def read_skill_cds(
        self,
        frame: np.ndarray,
        skill_keys: List[str]
    ) -> Dict[str, float]:
        """
        读取技能CD状态

        Args:
            frame: 游戏画面帧
            skill_keys: 技能按键列表，如 ['a', 's', 'd']

        Returns:
            Dict[str, float]: CD字典 {'a': 0.0, 's': 2.5}
                            0.0表示就绪，>0表示剩余秒数

        Performance:
            Max time: 15ms
        """
        pass

    def read_all(self, frame: np.ndarray) -> Dict[str, any]:
        """
        读取所有状态

        Args:
            frame: 游戏画面帧

        Returns:
            Dict:
                'hp_percent': float,
                'mp_percent': float,
                'skill_cds': Dict[str, float]

        Performance:
            Max time: 20ms
        """
        pass

    def is_skill_ready(self, frame: np.ndarray, skill_key: str) -> bool:
        """
        检查技能是否就绪

        Args:
            frame: 游戏画面帧
            skill_key: 技能按键

        Returns:
            bool: True=就绪, False=CD中
        """
        pass

    def update_regions(
        self,
        hp_region: Optional[Tuple[int, int, int, int]] = None,
        mp_region: Optional[Tuple[int, int, int, int]] = None
    ):
        """
        更新ROI区域（分辨率改变时调用）

        Args:
            hp_region: 新的HP区域
            mp_region: 新的MP区域
        """
        pass
```

#### 配置参数

```yaml
# config.yaml
state_reader:
  # UI区域（基于1920x1080，其他分辨率会自动缩放）
  hp_region: [100, 950, 400, 970]     # (x1, y1, x2, y2)
  mp_region: [100, 975, 400, 995]

  # 技能图标区域
  skill_regions:
    a: [450, 950, 490, 990]
    s: [500, 950, 540, 990]
    d: [550, 950, 590, 990]
    f: [600, 950, 640, 990]

  # 颜色范围（HSV格式）
  hp_color_hsv:
    lower: [0, 150, 150]     # 红色下界
    upper: [10, 255, 255]    # 红色上界

  mp_color_hsv:
    lower: [100, 150, 150]   # 蓝色下界
    upper: [130, 255, 255]   # 蓝色上界

  # CD检测
  cd_gray_threshold: 128    # 灰度阈值（技能CD时会变灰）
```

---

### 3.3 CoordinateMapper - 坐标映射器

**模块路径**: `src/perception/coord_mapper.py`

**职责**: 屏幕坐标到游戏世界坐标的转换（2.5D透视修正）

**依赖**: `numpy`

**线程安全**: 是（无状态操作）

#### 接口定义

```python
import numpy as np
from typing import Tuple

class CoordinateMapper:
    """
    坐标映射器（2.5D透视修正）

    DNF是2.5D游戏，Y轴代表深度，需要透视修正。

    性能契约:
        - 所有操作: < 1ms

    线程安全:
        完全线程安全

    异常契约:
        无（纯数学计算，不会失败）
    """

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        horizon_y: int = 540,  # 地平线Y坐标（屏幕中心）
        depth_scale: float = 0.0015  # 深度缩放因子
    ):
        """
        初始化映射器

        Args:
            screen_width: 屏幕宽度
            screen_height: 屏幕高度
            horizon_y: 地平线Y坐标（消失点）
            depth_scale: 深度缩放因子（像素到游戏单位）
        """
        pass

    def screen_to_world(
        self,
        screen_pos: Tuple[int, int]
    ) -> Tuple[float, float]:
        """
        屏幕坐标 -> 游戏世界坐标

        Args:
            screen_pos: 屏幕坐标 (x, y)

        Returns:
            Tuple[float, float]: 游戏坐标 (world_x, world_y)
                                world_y代表深度（0=前景，∞=背景）

        Example:
            >>> mapper.screen_to_world((960, 800))
            (0.0, 50.0)  # 中心偏下
        """
        pass

    def world_to_screen(
        self,
        world_pos: Tuple[float, float]
    ) -> Tuple[int, int]:
        """
        游戏世界坐标 -> 屏幕坐标

        Args:
            world_pos: 游戏坐标 (world_x, world_y)

        Returns:
            Tuple[int, int]: 屏幕坐标 (x, y)
        """
        pass

    def calculate_depth(self, screen_y: int) -> float:
        """
        计算Y坐标对应的深度

        Args:
            screen_y: 屏幕Y坐标

        Returns:
            float: 深度值（像素）

        Logic:
            depth = (screen_y - horizon_y) * depth_scale
        """
        pass

    def align_y_position(
        self,
        obj1: GameObject,
        obj2: GameObject
    ) -> float:
        """
        计算两个对象的Y轴对齐误差

        Args:
            obj1: 对象1
            obj2: 对象2

        Returns:
            float: Y轴误差（像素），0表示完美对齐
        """
        pass

    def is_aligned(
        self,
        obj1: GameObject,
        obj2: GameObject,
        tolerance: float = 15.0
    ) -> bool:
        """
        判断两个对象是否Y轴对齐

        Args:
            obj1: 对象1
            obj2: 对象2
            tolerance: 容差（像素）

        Returns:
            bool: 是否对齐
        """
        pass

    def resize(self, new_width: int, new_height: int):
        """
        调整映射器（分辨率改变时调用）

        Args:
            new_width: 新宽度
            new_height: 新高度
        """
        pass
```

---

## 4. 决策层接口

### 4.1 WorldModel - 世界模型

**模块路径**: `src/logic/world_model.py`

**职责**: 维护游戏状态的历史信息和上下文

**依赖**: `dataclasses`, `collections`

**线程安全**: 是（使用锁保护状态）

#### 接口定义

```python
from typing import List, Optional, Deque
from collections import deque
import threading

class WorldModel:
    """
    世界模型（维护历史状态）

    性能契约:
        - update() 调用时间: < 2ms
        - 历史记录最多保留1000帧（约33秒）

    线程安全:
        完全线程安全（使用RLock）

    异常契约:
        无
    """

    def __init__(self, history_len: int = 30):
        """
        初始化世界模型

        Args:
            history_len: 保留的历史帧数
        """
        pass

    def update(self, ctx: GameContext) -> None:
        """
        更新世界模型

        Args:
            ctx: 当前帧的上下文

        Thread Safety:
            线程安全
        """
        pass

    def get_hero_position_history(
        self,
        window: int = 30
    ) -> List[Tuple[int, int]]:
        """
        获取英雄位置历史（用于检测卡死）

        Args:
            window: 时间窗口（帧数）

        Returns:
            List[Tuple[int, int]]: 历史位置列表 [(x1,y1), (x2,y2), ...]
        """
        pass

    def is_hero_stuck(self) -> bool:
        """
        检测英雄是否卡住

        Returns:
            bool: True=卡住，False=正常

        Logic:
            - 计算最近30帧位置的标准差
            - 如果 std < 5px 且状态为移动，则判定为卡住
        """
        pass

    def predict_next_position(
        self,
        hero: GameObject
    ) -> Tuple[int, int]:
        """
        预测下一帧位置（惯性预测）

        Args:
            hero: 当前英雄对象

        Returns:
            Tuple[int, int]: 预测位置 (x, y)

        Logic:
            基于最近10帧的速度向量进行线性外推
        """
        pass

    def get_monster_count_trend(self) -> str:
        """
        获取怪物数量趋势

        Returns:
            str: 'increasing', 'decreasing', 'stable'
        """
        pass

    def get_combat_duration(self) -> float:
        """
        获取当前战斗持续时间（秒）

        Returns:
            float: 战斗时长，0表示未在战斗
        """
        pass

    def get_room_clear_time(self) -> Optional[float]:
        """
        获取房间清空耗时（秒）

        Returns:
            Optional[float]: 清空时间，None表示未清空
        """
        pass

    def reset(self):
        """
        重置世界模型（进入新房间时调用）
        """
        pass
```

---

### 4.2 BotFSM - 有限状态机

**模块路径**: `src/logic/bot_fsm.py`

**职责**: 核心决策逻辑，状态机管理

**依赖**: `enum`, `dataclasses`

**线程安全**: 是（状态更新使用锁）

#### 接口定义

```python
from enum import Enum
import time

class BotFSM:
    """
    机器人有限状态机

    性能契约:
        - update() 调用时间: < 10ms
        - 状态转换延迟: < 1ms

    线程安全:
        完全线程安全

    异常契约:
        无（所有异常在内部处理）
    """

    def __init__(self, config: Dict[str, any]):
        """
        初始化状态机

        Args:
            config: 配置字典（包含技能键、阈值等）
        """
        pass

    def update(self, ctx: GameContext) -> Command:
        """
        更新状态机并生成动作指令

        Args:
            ctx: 当前游戏上下文

        Returns:
            Command: 要执行的动作指令

        Performance:
            Max time: 10ms

        Flow:
            1. 检查生存状态（HP<30% -> 喝药）
            2. 根据上下文更新状态
            3. 调用对应状态的处理逻辑
            4. 返回动作指令
        """
        pass

    def transition_to(self, new_state: BotState) -> None:
        """
        状态转换

        Args:
            new_state: 新状态

        Thread Safety:
            线程安全
        """
        pass

    @property
    def current_state(self) -> BotState:
        """获取当前状态"""
        pass

    def get_state_durations(self) -> Dict[BotState, float]:
        """
        获取各状态停留时长统计

        Returns:
            Dict[BotState, float]: {State: 总停留秒数}
        """
        pass

    # 状态处理方法（内部使用）
    def _handle_idle(self, ctx: GameContext) -> Command:
        """处理待机状态"""
        pass

    def _handle_combat(self, ctx: GameContext) -> Command:
        """处理战斗状态"""
        pass

    def _handle_loot(self, ctx: GameContext) -> Command:
        """处理拾取状态"""
        pass

    def _handle_navigate(self, ctx: GameContext) -> Command:
        """处理导航状态"""
        pass

    def _handle_recovery(self, ctx: GameContext) -> Command:
        """处理异常恢复状态"""
        pass
```

#### 配置参数

```yaml
# config.yaml
fsm:
  # 状态转换阈值
  combat_monster_threshold: 1    # 检测到N个怪物进入战斗
  loot_item_threshold: 1         # 检测到N个物品进入拾取
  navigate_door_timeout: 5.0     # N秒找不到门进入导航模式

  # 战斗参数
  y_align_tolerance: 15          # Y轴对齐容差（像素）
  attack_range_x: 120            # X轴攻击距离（像素）
  target_switch_distance: 200    # 切换目标的距离阈值

  # 拾取参数
  pickup_distance: 100           # 拾取距离（像素）
  pickup_timeout: 3.0            # 单个物品拾取超时

  # 恢复参数
  hp_potion_threshold: 0.3       # HP低于此值喝药
  mp_potion_threshold: 0.2       # MP低于此值喝药
  stuck_detection_window: 30     # 卡死检测窗口（帧）
  stuck_position_variance: 5     # 卡死位置方差阈值
```

---

### 4.3 CombatLogic - 战斗逻辑

**模块路径**: `src/logic/combat.py`

**职责**: 2.5D对齐、索敌、技能释放

**依赖**: 无（纯逻辑）

**线程安全**: 是（无状态操作）

#### 接口定义

```python
from typing import Optional, List

class CombatLogic:
    """
    战斗逻辑模块

    性能契约:
        - decide_action() 调用时间: < 5ms

    线程安全:
        完全线程安全（无状态）

    异常契约:
        无
    """

    def __init__(self, config: Dict[str, any]):
        """
        初始化战斗逻辑

        Args:
            config: 配置字典
        """
        pass

    def decide_action(
        self,
        hero: GameObject,
        monsters: List[GameObject],
        skill_cds: Dict[str, float]
    ) -> Command:
        """
        决定战斗动作

        Args:
            hero: 英雄对象
            monsters: 怪物列表（已排序）
            skill_cds: 技能CD字典

        Returns:
            Command: 动作指令

        Flow:
            1. 选择目标（最近的怪物）
            2. 检查Y轴对齐
            3. 检查X轴距离
            4. 决定移动或攻击
        """
        pass

    def select_target(
        self,
        hero: GameObject,
        monsters: List[GameObject]
    ) -> Optional[GameObject]:
        """
        选择攻击目标

        Args:
            hero: 英雄
            monsters: 怪物列表

        Returns:
            Optional[GameObject]: 目标怪物，None表示无目标

        Strategy:
            - 优先选择最近的怪物
            - 如果有多个怪物距离相近，选择血量低的
        """
        pass

    def should_y_align(
        self,
        hero: GameObject,
        target: GameObject,
        tolerance: float = 15.0
    ) -> bool:
        """
        判断是否需要Y轴对齐

        Args:
            hero: 英雄
            target: 目标
            tolerance: 容差

        Returns:
            bool: True=需要对齐, False=已对齐
        """
        pass

    def calculate_move_command(
        self,
        hero: GameObject,
        target: GameObject,
        is_y_align: bool
    ) -> Command:
        """
        计算移动指令

        Args:
            hero: 英雄
            target: 目标
            is_y_align: 是否是Y轴对齐移动

        Returns:
            Command: 移动指令
        """
        pass

    def calculate_attack_command(
        self,
        hero: GameObject,
        target: GameObject,
        skill_cds: Dict[str, float]
    ) -> Command:
        """
        计算攻击指令

        Args:
            hero: 英雄
            target: 目标
            skill_cds: 技能CD

        Returns:
            Command: 攻击/技能指令

        Strategy:
            - 优先使用CD就绪的高伤害技能
            - 否则使用普通攻击
        """
        pass

    def is_in_attack_range(
        self,
        hero: GameObject,
        target: GameObject,
        attack_range: float = 120.0
    ) -> bool:
        """
        判断是否在攻击范围内

        Args:
            hero: 英雄
            target: 目标
            attack_range: 攻击距离

        Returns:
            bool: True=在范围内
        """
        pass
```

---

### 4.4 PathPlanner - 路径规划器

**模块路径**: `src/logic/path_planner.py`

**职责**: 局部路径规划、避障

**依赖**: `numpy`

**线程安全**: 是（无状态操作）

#### 接口定义

```python
from typing import List, Tuple, Optional
import numpy as np

class PathPlanner:
    """
    局部路径规划器

    性能契约:
        - plan_path() 调用时间: < 10ms

    线程安全:
        完全线程安全

    异常契约:
        无
    """

    def __init__(
        self,
        grid_size: int = 20,
        obstacle_margin: int = 50
    ):
        """
        初始化路径规划器

        Args:
            grid_size: 网格大小（像素）
            obstacle_margin: 障碍物膨胀半径（像素）
        """
        pass

    def plan_path(
        self,
        start: Tuple[int, int],
        goal: Tuple[int, int],
        obstacles: List[GameObject]
    ) -> List[Tuple[int, int]]:
        """
        规划从起点到终点的路径

        Args:
            start: 起点坐标 (x, y)
            goal: 终点坐标 (x, y)
            obstacles: 障碍物列表

        Returns:
            List[Tuple[int, int]]: 路径点列表 [(x1,y1), (x2,y2), ...]
                                如果直接可达，返回 [goal]

        Algorithm:
            - 简化版A*算法
            - 或者直接向量法（如果无障碍）
        """
        pass

    def get_next_waypoint(
        self,
        current: Tuple[int, int],
        path: List[Tuple[int, int]]
    ) -> Tuple[int, int]:
        """
        获取下一个路径点

        Args:
            current: 当前位置
            path: 路径列表

        Returns:
            Tuple[int, int]: 下一个目标点
        """
        pass

    def is_blocked(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        obstacles: List[GameObject]
    ) -> bool:
        """
        检测两点间是否有障碍

        Args:
            start: 起点
            end: 终点
            obstacles: 障碍物列表

        Returns:
            bool: True=有障碍, False=无障碍
        """
        pass

    def find_unstuck_direction(
        self,
        hero: GameObject,
        obstacles: List[GameObject]
    ) -> Tuple[int, int]:
        """
        寻找脱困方向（卡死时使用）

        Args:
            hero: 英雄
            obstacles: 障碍物

        Returns:
            Tuple[int, int]: 方向向量 (dx, dy)

        Strategy:
            - 尝试后跳、下+跳跃等脱困动作
        """
        pass
```

---

## 5. 应用层接口

### 5.1 MainLoop - 主循环

**模块路径**: `src/app/main_loop.py`

**职责**: 控制程序生命周期和帧率

**依赖**: 所有其他模块

**线程安全**: 主线程运行

#### 接口定义

```python
import threading
import time
from typing import Optional

class MainLoop:
    """
    主循环控制器

    性能契约:
        - 帧率稳定性: > 95% 帧在预算时间内
        - 帧间隔误差: < 5ms

    线程安全:
        - start(), stop() 线程安全
        - run() 必须在主线程调用

    异常契约:
        - RuntimeError: 重复启动/停止
    """

    def __init__(
        self,
        capture_engine: CaptureEngine,
        detector: ObjectDetector,
        state_reader: StateReader,
        fsm: BotFSM,
        input_driver: InputDriver,
        target_fps: int = 30
    ):
        """
        初始化主循环

        Args:
            capture_engine: 捕获引擎
            detector: 检测器
            state_reader: 状态读取器
            fsm: 状态机
            input_driver: 输入驱动
            target_fps: 目标帧率
        """
        pass

    def start(self):
        """
        启动主循环

        Raises:
            RuntimeError: 已经在运行
        """
        pass

    def stop(self):
        """
        停止主循环

        Thread Safety:
            线程安全，可从任何线程调用
        """
        pass

    def pause(self):
        """
        暂停主循环（保持运行但不执行逻辑）
        """
        pass

    def resume(self):
        """
        恢复主循环
        """
        pass

    def run(self):
        """
        主循环体

        Loop:
            1. 捕获帧
            2. 检测对象
            3. 读取状态
            4. 构建上下文
            5. 状态机决策
            6. 执行动作
            7. 帧率控制

        Exception Handling:
            - 单帧异常不会终止循环
            - 记录错误日志并继续
        """
        pass

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        pass

    @property
    def is_paused(self) -> bool:
        """是否已暂停"""
        pass

    @property
    def fps(self) -> float:
        """当前实际FPS"""
        pass

    @property
    def frame_count(self) -> int:
        """总帧数"""
        pass
```

#### 配置参数

```yaml
# config.yaml
system:
  fps_limit: 30
  frame_timeout: 50  # 单帧最大执行时间（毫秒）

  # 调试选项
  debug_window: true
  show_detection: true
  show_path: false

  # 日志
  log_level: "INFO"
  log_to_file: true
  log_path: "./logs/aradvision.log"
```

---

### 5.2 OverlaySystem - 调试蒙版

**模块路径**: `src/app/overlay.py`

**职责**: 在游戏窗口上绘制调试信息

**依赖**: `opencv-python`, ` PIL`

**线程安全**: 是（独立线程渲染）

#### 接口定义

```python
import numpy as np
from typing import List, Dict

class OverlaySystem:
    """
    调试蒙版系统

    性能契约:
        - 渲染时间: < 10ms
        - 不影响主循环性能

    线程安全:
        完全线程安全

    异常契约:
        无（渲染失败静默处理）
    """

    def __init__(
        self,
        window_title: str = "AradVision Debug",
        enabled: bool = True
    ):
        """
        初始化蒙版系统

        Args:
            window_title: 窗口标题
            enabled: 是否启用
        """
        pass

    def update(
        self,
        frame: np.ndarray,
        ctx: GameContext,
        cmd: Command
    ):
        """
        更新蒙版显示

        Args:
            frame: 当前帧
            ctx: 游戏上下文
            cmd: 当前指令

        Thread Safety:
            线程安全，内部使用双缓冲
        """
        pass

    def draw_objects(
        self,
        frame: np.ndarray,
        objects: List[GameObject],
        color: Tuple[int, int, int] = (0, 255, 0)
    ) -> np.ndarray:
        """
        绘制检测框

        Args:
            frame: 原始帧
            objects: 对象列表
            color: BGR颜色

        Returns:
            np.ndarray: 绘制后的帧
        """
        pass

    def draw_path(
        self,
        frame: np.ndarray,
        path: List[Tuple[int, int]]
    ) -> np.ndarray:
        """
        绘制路径

        Args:
            frame: 原始帧
            path: 路径点列表

        Returns:
            np.ndarray: 绘制后的帧
        """
        pass

    def draw_state(
        self,
        frame: np.ndarray,
        ctx: GameContext,
        cmd: Command
    ) -> np.ndarray:
        """
        绘制状态文本

        Args:
            frame: 原始帧
            ctx: 游戏上下文
            cmd: 当前指令

        Returns:
            np.ndarray: 绘制后的帧
        """
        pass

    def toggle(self):
        """
        切换显示/隐藏

        Thread Safety:
            线程安全
        """
        pass

    @property
    def is_enabled(self) -> bool:
        """是否已启用"""
        pass
```

---

### 5.3 Watchdog - 看门狗

**模块路径**: `src/app/watchdog.py`

**职责**: 紧急停止监控

**依赖**: `keyboard`, `threading`

**线程安全**: 是（独立线程）

#### 接口定义

```python
import threading

class Watchdog:
    """
    紧急停止看门狗

    性能契约:
        - 检测延迟: < 100ms
        - 停止延迟: < 50ms

    线程安全:
        完全线程安全

    异常契约:
        无（必须确保100%可靠）
    """

    # 默认热键
    DEFAULT_KILL_KEY = 'F12'
    DEFAULT_PAUSE_KEY = 'F11'

    def __init__(
        self,
        kill_key: str = DEFAULT_KILL_KEY,
        pause_key: str = DEFAULT_PAUSE_KEY,
        main_loop: Optional[MainLoop] = None
    ):
        """
        初始化看门狗

        Args:
            kill_key: 紧急停止键（默认F12）
            pause_key: 暂停键（默认F11）
            main_loop: 主循环引用（用于暂停）
        """
        pass

    def start(self):
        """
        启动监控线程

        Thread Safety:
            只能调用一次
        """
        pass

    def stop(self):
        """
        停止监控线程
        """
        pass

    def trigger_emergency_stop(self):
        """
        触发紧急停止

        Action:
            1. 调用 InputDriver.emergency_stop()
            2. 调用 os._exit(0) 强制退出
        """
        pass

    def trigger_pause(self):
        """
        触发暂停/恢复
        """
        pass

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        pass
```

---

## 6. 全局异常定义

**模块路径**: `src/core/exceptions.py`

所有模块可能抛出的异常类型定义。

```python
class AradVisionError(Exception):
    """基础异常类"""
    pass

# ========== 基础设施层异常 ==========

class WindowNotFoundError(AradVisionError):
    """找不到游戏窗口"""
    pass

class CaptureError(AradVisionError):
    """屏幕捕获失败"""
    pass

class DeviceLostError(AradVisionError):
    """游戏窗口丢失（关闭/崩溃）"""
    pass

class InitializationError(AradVisionError):
    """初始化失败"""
    pass

class InputError(AradVisionError):
    """输入模拟失败"""
    pass

class InvalidKeyError(AradVisionError):
    """无效的按键代码"""
    pass

class ConfigError(AradVisionError):
    """配置错误"""
    pass

# ========== 感知层异常 ==========

class ModelLoadError(AradVisionError):
    """模型加载失败"""
    pass

class InferenceError(AradVisionError):
    """推理失败（OOM/CUDA错误）"""
    pass

class DeviceError(AradVisionError):
    """设备错误（CUDA不可用）"""
    pass

class InvalidInputError(AradVisionError):
    """输入数据格式错误"""
    pass

class StateReadError(AradVisionError):
    """状态读取失败"""
    pass

# ========== 决策层异常 ==========

class LogicError(AradVisionError):
    """逻辑错误"""
    pass

class PathPlanningError(AradVisionError):
    """路径规划失败"""
    pass

# ========== 应用层异常 ==========

class RuntimeError(AradVisionError):
    """运行时错误"""
    pass
```

### 异常处理规范

所有模块必须遵循以下异常处理规范：

```python
# 1. 始终在文档字符串中声明可能抛出的异常
def some_function() -> None:
    """
    功能说明

    Raises:
        CaptureError: 捕获失败
        DeviceLostError: 设备丢失
    """
    pass

# 2. 使用具体的异常类型，而非通用的 Exception
# 好的做法:
raise ModelLoadError(f"Model file not found: {model_path}")

# 坏的做法:
raise Exception("Model not found")

# 3. 在文档中说明异常的处理方式
"""
异常处理策略:
    - CaptureError: 等待1秒后重试
    - DeviceLostError: 暂停脚本并提示用户
    - 其他异常: 记录日志并跳过当前帧
"""
```

---

## 7. 性能契约汇总

### 7.1 模块执行时间预算

基于 30 FPS 目标（单帧预算: 33ms）

| 模块 | 方法 | 最大时间 | 优先级 |
|------|------|----------|--------|
| CaptureEngine | grab() | 5ms | 最高 |
| ObjectDetector | detect() | 20ms | 高 |
| StateReader | read_all() | 5ms | 中 |
| WorldModel | update() | 2ms | 中 |
| BotFSM | update() | 10ms | 高 |
| CombatLogic | decide_action() | 5ms | 中 |
| PathPlanner | plan_path() | 10ms | 低 |
| InputDriver | execute() | 30ms | 中 |
| **总计** | - | **~32ms** | - |

### 7.2 性能监控规范

所有模块必须实现性能监控：

```python
import time
from typing import Callable

def measure_time(func: Callable) -> Callable:
    """性能测量装饰器"""
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000  # ms

        # 记录性能数据
        PerformanceMonitor.record(func.__name__, elapsed)

        # 超时警告
        if elapsed > PERFORMANCE_BUDGETS.get(func.__name__, float('inf')):
            logger.warning(f"{func.__name__} exceeded budget: {elapsed:.2f}ms")

        return result
    return wrapper

# 使用示例
@measure_time
def detect(self, frame: np.ndarray) -> List[GameObject]:
    # ... 检测逻辑
    pass
```

### 7.3 线程安全保证汇总

| 模块 | 线程安全 | 实现方式 |
|------|----------|----------|
| CaptureEngine | 是 | 独立线程 + 锁 |
| InputDriver | 是 | 内部锁序列化 |
| ConfigLoader | 是 | 单例 + 读锁写锁 |
| ObjectDetector | 是 | 模型只读 |
| StateReader | 是 | 无状态操作 |
| CoordinateMapper | 是 | 无状态操作 |
| WorldModel | 是 | RLock保护 |
| BotFSM | 是 | 状态更新用锁 |
| CombatLogic | 是 | 无状态操作 |
| PathPlanner | 是 | 无状态操作 |
| OverlaySystem | 是 | 双缓冲 |
| Watchdog | 是 | 独立线程 |

---

## 8. 配置文件完整规范

### 8.1 config.yaml 完整示例

```yaml
# ========== 系统配置 ==========
system:
  fps_limit: 30
  frame_timeout: 50  # 毫秒
  debug_window: true
  show_detection: true
  show_path: false
  log_level: "INFO"
  log_to_file: true
  log_path: "./logs/aradvision.log"

# ========== 游戏配置 ==========
game:
  window_title: "Dungeon & Fighter"
  class_names: ["monster", "hero", "item", "gate"]

# ========== 视觉配置 ==========
vision:
  # 模型
  model_path: "./assets/weights/dnf_v1.pt"
  conf_threshold: 0.65
  iou_threshold: 0.45
  device: "cuda:0"
  half_precision: true
  img_size: 640

  # 坐标映射
  horizon_y: 540
  depth_scale: 0.0015

# ========== 捕获配置 ==========
capture:
  window_title: "Dungeon & Fighter"
  target_fps: 30
  use_d3d: true
  capture_cursor: false
  monitor_index: 1
  retry_interval: 1.0

# ========== 状态读取配置 ==========
state_reader:
  hp_region: [100, 950, 400, 970]
  mp_region: [100, 975, 400, 995]
  skill_regions:
    a: [450, 950, 490, 990]
    s: [500, 950, 540, 990]
    d: [550, 950, 590, 990]
    f: [600, 950, 640, 990]

  hp_color_hsv:
    lower: [0, 150, 150]
    upper: [10, 255, 255]

  mp_color_hsv:
    lower: [100, 150, 150]
    upper: [130, 255, 255]

  cd_gray_threshold: 128

# ========== 输入配置 ==========
input:
  enable_jitter: true
  jitter_mean: 0.1
  jitter_std: 0.02
  mouse_enabled: false
  mouse_speed: 1.0
  use_direct_input: true
  force_release_on_stop: true

# ========== 按键配置 ==========
keys:
  # 移动
  up: "up"
  down: "down"
  left: "left"
  right: "right"
  jump: "space"

  # 攻击
  attack: "x"

  # 技能
  skill_1: "a"
  skill_2: "s"
  skill_3: "d"
  skill_4: "f"
  buff: "space"

  # 物品
  potion: "1"

  # 系统热键
  kill_key: "F12"
  pause_key: "F11"

# ========== 状态机配置 ==========
fsm:
  # 状态转换阈值
  combat_monster_threshold: 1
  loot_item_threshold: 1
  navigate_door_timeout: 5.0

  # 战斗参数
  y_align_tolerance: 15
  attack_range_x: 120
  target_switch_distance: 200

  # 拾取参数
  pickup_distance: 100
  pickup_timeout: 3.0

  # 恢复参数
  hp_potion_threshold: 0.3
  mp_potion_threshold: 0.2
  stuck_detection_window: 30
  stuck_position_variance: 5

# ========== 看门狗配置 ==========
watchdog:
  enabled: true
  kill_key: "F12"
  pause_key: "F11"
  check_interval: 0.1  # 秒
```

---

## 9. 模块间通信协议

### 9.1 数据流向

```
┌─────────────┐
│ MainLoop    │
│ (协调器)     │
└──────┬──────┘
       │
       ├─→ CaptureEngine ─→ np.ndarray (帧)
       │
       ├─→ ObjectDetector ─→ List[GameObject]
       │
       ├─→ StateReader ─→ {hp, mp, skill_cds}
       │
       ├─→ GameContext (组装)
       │
       ├─→ BotFSM ─→ Command
       │
       └─→ InputDriver ─→ 硬件信号
```

### 9.2 异步通信（可选优化）

如果使用多线程，模块间通过队列通信：

```python
# 捕获线程 -> 检测线程
capture_queue: Queue[Tuple[float, np.ndarray]]

# 检测线程 -> 决策线程
detection_queue: Queue[DetectionResult]

# 决策线程 -> 执行线程
command_queue: Queue[Command]
```

---

## 10. 开发协作规范

### 10.1 接口实现检查清单

实现新模块时，必须确保：

- [ ] 所有公共方法都有完整的类型注解
- [ ] 所有方法都有 docstring 说明
- [ ] 在 docstring 中声明 `Raises` 部分
- [ ] 在 docstring 中声明 `Performance` 部分
- [ ] 实现性能监控装饰器
- [ ] 通过单元测试（覆盖率 > 80%）
- [ ] 通过集成测试
- [ ] 更新本文档

### 10.2 接口变更流程

如果需要修改接口：

1. 在团队会议讨论并批准
2. 更新本文档
3. 创建向后兼容的过渡期（至少1个版本）
4. 通知所有依赖该接口的模块
5. 更新所有实现
6. 更新测试用例

### 10.3 版本控制

- 接口变更必须增加主版本号（V1.0 → V2.0）
- 内部优化增加次版本号（V1.0 → V1.1）
- 文档修正使用补丁号（V1.0 → V1.0.1）

---

## 11. 附录

### 11.1 类型注速查表

```python
# 基本类型
int, float, str, bool

# 容器类型
List[T], Dict[K, V], Tuple[T1, T2], Set[T]

# 可选类型
Optional[T]  # 等价于 Union[T, None]

# 联合类型
Union[T1, T2]  # T1 或 T2

# 可调用类型
Callable[[Arg1Type, Arg2Type], ReturnType]

# 数据类
@dataclass
class MyClass:
    field: Type = default_value

# 枚举
class MyEnum(Enum):
    VALUE1 = 1
    VALUE2 = 2
```

### 11.2 性能分析工具推荐

```bash
# CPU性能分析
pip install py-spy

# 使用方法
py-spy record --output profile.svg -- python main.py

# 内存分析
pip install memory_profiler

# 使用方法
python -m memory_profiler main.py
```

---

## 文档变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| V1.0 | 2026-02-10 | 初始版本 | Claude (haneball17) |

---

**批准人**: haneball17
**最后更新**: 2026-02-10
**状态**: 正式生效

---

## 联系方式

如有接口相关问题，请联系：
- 项目负责人: haneball17
- 技术支持: [待补充]

---

**本文档是多团队协作的契约，所有开发者必须严格遵守。**
