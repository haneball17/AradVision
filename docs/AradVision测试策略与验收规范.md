# 测试策略与验收规范 (Test Strategy & Acceptance Criteria)

 **项目名称** : AradVision - DNF 视觉辅助自动化系统

 **文档标识** : ARAD-VIS-006

 **版本** : V1.0

 **状态** : 正式版

 **最后更新** : 2026-02-10

---

## 1. 引言 (Introduction)

### 1.1 编写目的

本文档旨在定义 AradVision 项目的**测试策略**、**测试标准**与**验收规范**，确保系统在视觉感知、决策逻辑和输入控制三个核心层面达到预期的质量和性能指标。

本文档将作为开发团队进行单元测试、集成测试和系统验收的主要依据。

### 1.2 测试理念：Mock-First Approach

本项目的测试采用 **Mock-First（模拟优先）** 策略，即：

* **先测试核心逻辑，后接入真实环境**：在没有游戏运行的情况下，使用预采集的截图数据和模拟输入验证系统的决策逻辑。
* **降低测试成本**：避免每次修改代码都需要启动游戏客户端，大幅提升开发迭代效率。
* **提高测试覆盖率**：通过构造各种边界情况和异常场景（如怪物遮挡、光照变化），确保系统的鲁棒性。

### 1.3 测试层次

项目采用**三层金字塔测试模型**：

```
        /\
       /  \      端到端测试 (E2E)
      /____\     占比 10%
     /      \
    /        \   集成测试 (Integration)
   /__________\  占比 30%
  /            \
 /   单元测试    \ (Unit Tests)
/________________\ 占比 60%
```

* **单元测试 (Unit Tests)**：针对单个类或函数的测试，确保输入输出符合预期。
* **集成测试 (Integration Tests)**：验证模块间的交互（如视觉模块输出 -> 决策模块输入）。
* **端到端测试 (E2E Tests)**：在真实游戏环境中运行，验证完整流程。

---

## 2. 单元测试标准 (Unit Test Standards)

### 2.1 测试框架选型

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| **测试框架** | **pytest** | 功能强大，支持 fixture、parametrize 等高级特性 |
| **Mock 工具** | **unittest.mock** | Python 标准库，用于模拟外部依赖 |
| **覆盖率工具** | **pytest-cov** | 生成覆盖率报告，目标覆盖率 ≥ 80% |
| **断言库** | **pytest-assert** | 提供更友好的错误提示 |

### 2.2 测试目录结构

```
tests/
├── unit/                      # 单元测试
│   ├── test_vision/
│   │   ├── test_detector.py   # YOLO 检测器测试
│   │   ├── test_capture.py    # 屏幕捕获测试
│   │   └── test_coordinate_mapper.py  # 坐标映射测试
│   ├── test_logic/
│   │   ├── test_bot_fsm.py    # 状态机测试
│   │   ├── test_combat_logic.py  # 战斗逻辑测试
│   │   └── test_path_planner.py   # 路径规划测试
│   └── test_input/
│       ├── test_input_adapter.py   # 输入适配器测试
│       └── test_random_delayer.py  # 随机延迟测试
├── integration/               # 集成测试
│   ├── test_vision_to_logic_pipeline.py
│   └── test_logic_to_input_pipeline.py
├── e2e/                       # 端到端测试
│   └── test_dungeon_run.py    # 完整副本流程测试
├── fixtures/                  # 测试数据
│   ├── images/                # 预采集截图
│   │   ├── monster_single.png
│   │   ├── monster_group.png
│   │   ├── boss_room.png
│   │   └── gate_open.png
│   └── mock_data/             # 模拟数据
│       ├── detection_results.json
│       └── game_contexts.json
└── conftest.py                # pytest 配置与共享 fixtures
```

### 2.3 核心模块单元测试规范

#### 2.3.1 视觉模块 (`vision`)

**测试目标**：确保图像处理的正确性和鲁棒性。

**测试用例清单**：

| 测试用例 ID | 测试场景 | 输入 | 预期输出 | 优先级 |
|------------|---------|------|---------|--------|
| V-001 | 正常单怪物检测 | 包含单个怪物的截图 | 检测到 1 个 Monster 类别，置信度 > 0.7 | P0 |
| V-002 | 多怪物群检测 | 包含 5 个怪物的截图 | 检测到 5 个 Monster，NMS 不重叠 | P0 |
| V-003 | 怪物部分遮挡 | 怪物被树桩遮挡 50% | 仍能检测到，置信度 > 0.5 | P1 |
| V-004 | 低光照环境 | 暗色副本截图 | 检测率不低于 70% | P1 |
| V-005 | 无目标场景 | 纯地面截图 | 返回空列表，不抛异常 | P0 |
| V-006 | 坐标映射准确性 | 已知坐标的测试图 | foot_point 误差 < 5 像素 | P0 |
| V-007 | YOLO 推理超时 | 极大分辨率图像 | 在 100ms 内返回或抛 TimeoutError | P1 |

**示例代码**：

```python
# tests/unit/test_vision/test_detector.py
import pytest
import numpy as np
from pathlib import Path
from vision.detector import YoloDetector

class TestYoloDetector:
    @pytest.fixture
    def detector(self):
        return YoloDetector(model_path="assets/weights/test_model.pt")

    @pytest.fixture
    def sample_image(self):
        """加载测试用的游戏截图"""
        img_path = Path("tests/fixtures/images/monster_single.png")
        return cv2.imread(str(img_path))

    def test_detect_single_monster(self, detector, sample_image):
        """V-001: 测试单怪物检测"""
        results = detector.detect(sample_image)

        assert len(results.monsters) == 1
        assert results.monsters[0].conf > 0.7
        assert results.monsters[0].cls_name == "monster"

    @pytest.mark.parametrize("conf_threshold", [0.5, 0.7, 0.9])
    def test_confidence_filtering(self, detector, sample_image, conf_threshold):
        """V-XXX: 测试不同置信度阈值"""
        detector.conf_threshold = conf_threshold
        results = detector.detect(sample_image)

        for monster in results.monsters:
            assert monster.conf >= conf_threshold

    def test_no_target_returns_empty_list(self, detector):
        """V-005: 测试无目标场景"""
        empty_image = np.zeros((600, 800, 3), dtype=np.uint8)
        results = detector.detect(empty_image)

        assert len(results.monsters) == 0
        assert len(results.items) == 0
```

#### 2.3.2 逻辑模块 (`logic`)

**测试目标**：确保决策逻辑的正确性和状态机流转的合理性。

**测试用例清单**：

| 测试用例 ID | 测试场景 | 模拟输入 | 预期输出 | 优先级 |
|------------|---------|---------|---------|--------|
| L-001 | Y 轴未对齐触发移动 | dy = 50 像素 | Command: MOVE_DOWN | P0 |
| L-002 | Y 轴对齐后 X 轴逼近 | dy = 5, dx = 200 | Command: MOVE_RIGHT | P0 |
| L-003 | 进入攻击范围 | dy = 5, dx = 80 | Command: ATTACK_COMBO | P0 |
| L-004 | 血量低于 30% 触发吃药 | hp = 25% | Command: USE_POTION | P0 |
| L-005 | 目标丢失 5 帧 | monsters = [] x 5 | State: IDLE/SEARCH | P1 |
| L-006 | 房间清空后寻找门 | monsters = [], doors = 1 | State: NAVIGATE | P0 |
| L-007 | 卡死检测触发 | position_stuck 5s | Command: RANDOM_ESCAPE | P1 |

**示例代码**：

```python
# tests/unit/test_logic/test_combat_logic.py
import pytest
from dataclasses import dataclass
from logic.strategies import CombatLogic, Command
from core.models import GameObject

@dataclass
class MockGameObject:
    """模拟游戏对象"""
    foot_point: tuple
    bbox: tuple = (0, 0, 100, 100)

class TestCombatLogic:
    @pytest.fixture
    def combat_logic(self):
        return CombatLogic(y_align_tolerance=15, attack_range_x=120)

    def test_y_axis_misalignment_triggers_move(self, combat_logic):
        """L-001: Y 轴未对齐时应优先移动"""
        hero = MockGameObject(foot_point=(100, 100))
        monster = MockGameObject(foot_point=(100, 150))  # dy = 50

        cmd = combat_logic.decide_action(hero, monster)

        assert cmd.action_type == "MOVE"
        assert cmd.direction == "DOWN"

    def test_in_range_triggers_attack(self, combat_logic):
        """L-003: 进入攻击范围应触发攻击"""
        hero = MockGameObject(foot_point=(100, 100))
        monster = MockGameObject(foot_point=(180, 105))  # dx = 80, dy = 5

        cmd = combat_logic.decide_action(hero, monster)

        assert cmd.action_type == "ATTACK_COMBO"

    @pytest.mark.parametrize("dy,dx,expected_action", [
        (50, 0, "MOVE_DOWN"),      # Y 轴差距大
        (5, 200, "MOVE_RIGHT"),    # X 轴差距大
        (5, 80, "ATTACK_COMBO"),   # 在攻击范围
    ])
    def test_combat_decision_matrix(self, combat_logic, dy, dx, expected_action):
        """参数化测试不同的战斗场景"""
        hero = MockGameObject(foot_point=(100, 100))
        monster = MockGameObject(foot_point=(100 + dx, 100 + dy))

        cmd = combat_logic.decide_action(hero, monster)

        assert cmd.action_type == expected_action
```

#### 2.3.3 输入模块 (`input`)

**测试目标**：确保输入模拟的正确性和安全性。

**测试用例清单**：

| 测试用例 ID | 测试场景 | 输入 | 预期输出 | 优先级 |
|------------|---------|------|---------|--------|
| I-001 | 单次按键 | tap("X") | 调用 SendInput 1 次按下 + 1 次弹起 | P0 |
| I-002 | 长按按键 | hold("X", 0.5) | 按下后等待 0.5s 再弹起 | P0 |
| I-003 | 随机延迟范围 | tap("X") | 延迟在 50ms-150ms 之间 | P0 |
| I-004 | F12 熔断触发 | 按下 F12 | 立即调用 os._exit(0) | P0 |
| I-005 | 无效按键处理 | tap("INVALID") | 抛出 ValueError | P1 |

**示例代码**：

```python
# tests/unit/test_input/test_input_adapter.py
import pytest
from unittest.mock import patch, MagicMock
from input.adapter import InputAdapter

class TestInputAdapter:
    @pytest.fixture
    def adapter(self):
        return InputAdapter()

    @patch('input.adapter.win32api.SendInput')
    def test_tap_key_sends_press_and_release(self, mock_send, adapter):
        """I-001: 单次按键应发送按下和弹起"""
        adapter.tap("X")

        assert mock_send.call_count == 2

    @patch('input.adapter.time.sleep')
    @patch('input.adapter.win32api.SendInput')
    def test_hold_key_waits_duration(self, mock_send, mock_sleep, adapter):
        """I-002: 长按应等待指定时长"""
        adapter.hold("X", duration=0.5)

        mock_sleep.assert_called_with(0.5)

    @patch('input.adapter.time.sleep')
    @patch('input.adapter.random.uniform')
    def test_random_delay_in_range(self, mock_random, mock_sleep, adapter):
        """I-003: 随机延迟应在 50-150ms 范围内"""
        mock_random.return_value = 0.1

        adapter.tap("X")

        mock_random.assert_called_with(0.05, 0.15)
```

### 2.4 测试覆盖率要求

| 模块 | 最低覆盖率 | 目标覆盖率 |
|------|-----------|-----------|
| `vision/` | 70% | 85% |
| `logic/` | 85% | 95% |
| `input/` | 80% | 90% |
| **整体** | **75%** | **85%** |

---

## 3. 模拟数据设计 (Mock Data Design)

### 3.1 测试图像集

为了支持 Mock-First 测试，需要采集具有代表性的游戏截图。

**图像采集标准**：

| 场景类别 | 文件命名示例 | 采集要求 | 数量 |
|---------|-------------|---------|------|
| **单怪物** | `monster_single_001.png` | 不同种类的怪物，清晰无遮挡 | 20 张 |
| **怪物群** | `monster_group_001.png` | 3-5 个怪物，有重叠 | 15 张 |
| **Boss 房** | `boss_room_001.png` | 包含 Boss 血条特效 | 10 张 |
| **门/传送阵** | `gate_open.png`, `gate_closed.png` | 开启和关闭状态 | 各 5 张 |
| **掉落物品** | `item_gold_001.png` | 金币、装备、材料 | 各 10 张 |
| **小地图** | `minimap_boss.png` | 包含白色箭头和 BOSS 标记 | 5 张 |
| **边界场景** | `monster_occluded.png` | 怪物被墙壁/树遮挡 | 10 张 |
| **光照变化** | `dark_room.png`, `bright_room.png` | 不同光照环境 | 各 5 张 |

**采集工具脚本**：

```python
# scripts/capture_test_images.py
"""
测试图像采集工具
按热键 F5 截图并自动保存到 tests/fixtures/images/
"""
import cv2
import time
import win32gui
from pathlib import Path

class ImageCaptureTool:
    def __init__(self, output_dir="tests/fixtures/images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.count = 0

    def capture(self, window_title="Dungeon & Fighter"):
        hwnd = win32gui.FindWindow(None, window_title)
        # ... 截图逻辑 ...

        filename = self.output_dir / f"scene_{self.count:03d}.png"
        cv2.imwrite(str(filename), frame)
        print(f"已保存: {filename}")
        self.count += 1

if __name__ == "__main__":
    tool = ImageCaptureTool()
    print("按 F5 截图，ESC 退出")
    # ... 监听热键逻辑 ...
```

### 3.2 模拟数据集

**JSON 格式示例** (`tests/fixtures/mock_data/detection_results.json`)：

```json
{
  "scene_single_monster": {
    "monsters": [
      {
        "cls_id": 0,
        "cls_name": "goblin",
        "conf": 0.85,
        "bbox": [100, 200, 180, 320]
      }
    ],
    "hero": {
      "cls_id": 1,
      "cls_name": "player",
      "conf": 0.95,
      "bbox": [400, 300, 480, 420]
    },
    "items": [],
    "doors": []
  },
  "scene_boss_room": {
    "monsters": [
      {
        "cls_id": 0,
        "cls_name": "boss_giant",
        "conf": 0.92,
        "bbox": [500, 150, 700, 400]
      }
    ],
    "hero": {
      "cls_id": 1,
      "cls_name": "player",
      "conf": 0.93,
      "bbox": [200, 300, 280, 420]
    },
    "items": [
      {"cls_id": 2, "cls_name": "item_epic", "conf": 0.88, "bbox": [550, 380, 580, 410]}
    ],
    "doors": []
  }
}
```

### 3.3 pytest Fixture 配置

**共享 Fixture 定义** (`tests/conftest.py`)：

```python
import pytest
import numpy as np
import json
from pathlib import Path
from vision.detector import YoloDetector
from logic.bot_fsm import BotFSM

@pytest.fixture
def sample_detection_result():
    """加载预设的检测结果"""
    path = Path("tests/fixtures/mock_data/detection_results.json")
    with open(path) as f:
        return json.load(f)

@pytest.fixture
def mock_vision_output():
    """模拟视觉模块输出"""
    class MockVision:
        def detect(self, frame):
            # 返回固定的 DetectionResult
            pass
    return MockVision()

@pytest.fixture
def mock_input_executor():
    """模拟输入执行器，记录所有指令"""
    class MockInput:
        def __init__(self):
            self.commands = []

        def execute(self, cmd):
            self.commands.append(cmd)
    return MockInput()

@pytest.fixture
def temp_config_file(tmp_path):
    """创建临时配置文件"""
    config = {
        "vision": {"conf_threshold": 0.7},
        "logic": {"y_align_tolerance": 15}
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config, f)
    return config_file
```

---

## 4. 集成测试策略 (Integration Test Strategy)

### 4.1 集成测试层级

```
┌─────────────────────────────────────────┐
│         End-to-End (Real Game)          │
└─────────────────────────────────────────┘
                    ↑
┌─────────────────────────────────────────┐
│   Vision → Logic → Input (Mocked)       │
└─────────────────────────────────────────┘
                    ↑
┌─────────────────────────────────────────┐
│   Vision → Logic (Output Check Only)    │
└─────────────────────────────────────────┘
                    ↑
┌─────────────────────────────────────────┐
│         Unit Tests (Isolated)           │
└─────────────────────────────────────────┘
```

### 4.2 核心集成测试场景

#### 4.2.1 视觉到决策集成测试

**测试目标**：验证视觉模块的输出能正确驱动决策逻辑。

**测试方法**：
* 使用真实截图 + Mock 的 YOLO 模型（或真实模型）
* 验证 `GameContext` 能正确构建
* 验证 `BotFSM` 状态转换符合预期

**示例代码**：

```python
# tests/integration/test_vision_to_logic_pipeline.py
import pytest
from vision.detector import YoloDetector
from logic.bot_fsm import BotFSM
from core.models import GameContext

class TestVisionToLogicPipeline:
    @pytest.fixture
    def pipeline(self, mock_vision_output):
        detector = YoloDetector(model_path="test_model.pt")
        fsm = BotFSM()
        return detector, fsm

    def test_monster_detected_triggers_combat(self, pipeline):
        """验证检测到怪物后状态机进入 COMBAT"""
        detector, fsm = pipeline

        # 加载测试图片
        img = cv2.imread("tests/fixtures/images/monster_single.png")

        # 执行流水线
        detection_result = detector.detect(img)
        ctx = GameContext.from_detection(detection_result)
        state = fsm.update(ctx)

        # 断言
        assert state == fsm.State.COMBAT
        assert len(ctx.monsters) == 1

    def test_cleared_room_triggers_navigation(self, pipeline):
        """验证房间清空后状态机进入 NAVIGATE"""
        # ... 类似逻辑 ...
```

#### 4.2.2 决策到输入集成测试

**测试目标**：验证决策指令能正确转换为输入信号。

**测试方法**：
* 使用 Mock 的 `InputAdapter`
* 记录所有发送的指令
* 验证指令序列的正确性

**示例代码**：

```python
# tests/integration/test_logic_to_input_pipeline.py
import pytest
from logic.bot_fsm import BotFSM
from input.adapter import InputAdapter

class TestLogicToInputPipeline:
    def test_combat_sequence_generates_correct_inputs(self):
        """验证战斗流程生成正确的输入序列"""
        # 设置初始状态
        fsm = BotFSM()
        mock_input = MockInput()  # 记录所有指令

        # 模拟 3 帧战斗
        for _ in range(3):
            ctx = self._create_combat_context()
            cmd = fsm.update(ctx)
            mock_input.execute(cmd)

        # 验证指令序列
        commands = mock_input.commands
        assert commands[0].action_type == "MOVE"  # 先对齐
        assert commands[1].action_type == "MOVE"
        assert commands[2].action_type == "ATTACK_COMBO"  # 再攻击
```

### 4.3 集成测试覆盖率要求

| 集成场景 | 覆盖率要求 |
|---------|-----------|
| Vision → Logic | ≥ 90% (主要状态转换路径) |
| Logic → Input | ≥ 85% (主要指令类型) |
| 完整流水线 | ≥ 80% (核心场景) |

---

## 5. 端到端测试 (End-to-End Tests)

### 5.1 测试环境要求

* **游戏客户端**：DNF 私服/单机版，分辨率 800x600
* **测试账号**：拥有修炼场和"洛兰"副本权限的角色
* **硬件**：NVIDIA GTX 1060 或以上显卡
* **系统**：Windows 10/11 64-bit

### 5.2 E2E 测试场景

#### 场景 1：修炼场基础移动

**测试目标**：验证输入模拟模块的基本功能。

**步骤**：
1. 进入修炼场
2. 启动 AradVision
3. 发送指令：按住右键 2 秒
4. 发送指令：按 X 键攻击 5 次
5. 发送指令：双击方向键冲刺

**验收标准**：
* 角色向右移动约 2 秒
* 释放 5 次普通攻击
* 执行冲刺动作

#### 场景 2：洛兰房间自动战斗

**测试目标**：验证完整的战斗循环。

**步骤**：
1. 进入洛兰副本第 1 房
2. 启动 AradVision
3. 系统自动识别并攻击怪物
4. 房间清空后自动寻找门

**验收标准**：
* 成功检测到所有怪物（≥ 90% 检测率）
* 正确执行 Y 轴对齐（误差 < 15 像素）
* 在攻击范围内释放攻击
* 房间清空后识别门并移动

#### 场景 3：洛兰完整通关

**测试目标**：验证全流程自动化。

**步骤**：
1. 从洛兰入口开始
2. 依次通过 3 个房间
3. 击败房间内怪物
4. 通关后自动停止

**验收标准**：
* 完整通关时间 < 3 分钟
* 角色血量 > 50%（无严重失误）
* 不出现卡死超过 5 秒的情况

### 5.3 性能验收指标

| 指标 | 目标值 | 测试方法 |
|------|--------|---------|
| **FPS** | ≥ 30 FPS | 统计 1 分钟内的平均帧率 |
| **推理延迟** | < 30ms | 记录 YOLO 单次推理耗时 |
| **端到端延迟** | < 150ms | 从画面变化到按键发出 |
| **CPU 占用** | < 40% | 任务管理器监控 |
| **显存占用** | < 2GB | nvidia-smi 监控 |

### 5.4 稳定性测试

**测试场景**：连续运行 10 局洛兰副本。

**验收标准**：
* 成功率 ≥ 80%（8/10 局通关）
* 无程序崩溃或未捕获异常
* 无内存泄漏（内存占用不持续增长）

---

## 6. 验收标准与里程碑 (Acceptance Criteria)

### 6.1 Milestone 1: Mock 测试完成 (Week 1-2)

**验收标准**：

* [ ] 单元测试框架搭建完成（pytest + cov）
* [ ] 视觉模块单元测试覆盖率 ≥ 70%
* [ ] 逻辑模块单元测试覆盖率 ≥ 80%
* [ ] 输入模块单元测试覆盖率 ≥ 75%
* [ ] 所有测试用例通过（`pytest` 无报错）
* [ ] 采集测试图像集 ≥ 50 张

**交付物**：
* `tests/unit/` 目录及所有测试文件
* `tests/fixtures/images/` 测试图像集
* 测试覆盖率报告（HTML）

### 6.2 Milestone 2: 集成测试完成 (Week 3)

**验收标准**：

* [ ] 视觉到决策集成测试通过
* [ ] 决策到输入集成测试通过
* [ ] 完整流水线集成测试通过
* [ ] Mock 测试能在无游戏环境下运行
* [ ] 集成测试覆盖率 ≥ 80%

**交付物**：
* `tests/integration/` 目录及测试文件
* 集成测试报告

### 6.3 Milestone 3: E2E 测试完成 (Week 4)

**验收标准**：

* [ ] 修炼场基础移动测试通过
* [ ] 洛兰单房间自动战斗测试通过
* [ ] 洛兰完整通关测试通过
* [ ] 性能指标达标（FPS ≥ 30, 延迟 < 150ms）
* [ ] 稳定性测试通过（10 局成功率 ≥ 80%）
* [ ] F12 熔断机制测试通过

**交付物**：
* `tests/e2e/` 目录及测试脚本
* E2E 测试报告（含性能数据）
* 演示视频（可选）

### 6.4 最终验收 (Final Acceptance)

**综合指标**：

* [ ] 整体代码覆盖率 ≥ 75%
* [ ] 所有单元测试通过（≥ 200 个测试用例）
* [ ] 所有集成测试通过（≥ 20 个测试用例）
* [ ] E2E 测试通过（≥ 5 个核心场景）
* [ ] 性能达标：FPS ≥ 30, 延迟 < 150ms
* [ ] 稳定性达标：连续运行 10 局无崩溃
* [ ] 文档完整：测试策略、测试报告、覆盖率报告

---

## 7. 测试自动化与 CI/CD (Test Automation)

### 7.1 自动化测试流程

**本地开发流程**：

```bash
# 1. 开发新功能
git checkout -b feature/combat-logic

# 2. 编写单元测试（TDD）
vim tests/unit/test_logic/test_combat_logic.py

# 3. 运行测试
pytest tests/unit/test_logic/test_combat_logic.py -v

# 4. 检查覆盖率
pytest tests/unit/ --cov=logic --cov-report=html

# 5. 提交代码
git add .
git commit -m "feat: 实现战斗对齐逻辑"
```

### 7.2 CI/CD 集成（可选）

**GitHub Actions 配置示例** (`.github/workflows/test.yml`)：

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=. --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

### 7.3 测试报告生成

**使用 pytest-html 生成可视化报告**：

```bash
pytest tests/ --html=report.html --self-contained-html
```

**报告应包含**：
* 测试用例总数及通过率
* 失败用例的详细错误日志
* 代码覆盖率统计
* 执行时间统计

---

## 8. 测试最佳实践 (Best Practices)

### 8.1 测试命名规范

**函数命名**：`test_<被测函数>_<场景>_<预期结果>`

**示例**：
```python
def test_detect_monster_with_low_light_returns_low_confidence():
    pass

def test_y_axis_alignment_when_misaligned_returns_move_command():
    pass
```

### 8.2 测试独立性原则

* **禁止**：测试用例之间有依赖关系
* **禁止**：测试用例修改共享状态
* **正确**：每个用例独立运行，使用 fixture 隔离数据

### 8.3 测试数据隔离

* 使用 `tmp_path` fixture 创建临时文件
* 测试数据库使用内存数据库或 `rollback`
* 测试完成后清理资源（使用 `yield` fixture）

### 8.4 Mock 的使用原则

* **何时 Mock**：
  * 外部依赖（游戏窗口、网络请求）
  * 慢速操作（YOLO 推理、文件 I/O）
  * 随机性操作（随机延迟）
* **何时不 Mock**：
  * 核心业务逻辑（如坐标计算）
  * 简单的数据结构操作

### 8.5 测试性能优化

* 使用 `@pytest.mark.skip("reason")` 跳过暂时不运行的测试
* 使用 `@pytest.mark.slow` 标记慢速测试，分开运行
* 并行运行测试：`pytest -n auto` (需安装 pytest-xdist)

---

## 9. 常见问题与解决方案 (FAQ)

### Q1: YOLO 模型推理太慢，测试耗时过长？

**解决方案**：
* 使用轻量级模型（YOLOv8n）用于测试
* Mock 掉 YOLO 推理，直接返回预设结果
* 使用 `@pytest.fixture(scope="session")` 缓存模型加载

### Q2: 游戏窗口必须在测试时启动吗？

**解决方案**：
* 单元测试和集成测试不需要真实游戏
* 只有 E2E 测试需要游戏环境
* 使用 Mock 的 `CaptureEngine` 返回预设截图

### Q3: 如何测试随机延迟逻辑？

**解决方案**：
* 使用 `@patch('random.uniform', return_value=0.1)` 固定随机值
* 使用 `pytest.mark.parametrize` 测试不同的延迟值

### Q4: 测试覆盖率未达标怎么办？

**解决方案**：
* 使用 `pytest-cov --cov-report=term-missing` 查看未覆盖的行
* 优先补充核心逻辑（`logic/` 模块）的测试
* 边界条件和异常处理的测试用例

---

## 10. 附录 (Appendix)

### 附录 A：测试工具安装

```bash
# 安装测试框架
pip install pytest pytest-cov pytest-html pytest-xdist

# 安装 Mock 工具
pip install unittest-mock

# 安装覆盖率工具
pip install coverage
```

### 附录 B：常用 pytest 命令

```bash
# 运行所有测试
pytest

# 运行指定目录的测试
pytest tests/unit/

# 显示详细输出
pytest -v

# 生成覆盖率报告
pytest --cov=. --cov-report=html

# 并行运行测试（加速）
pytest -n auto

# 运行标记的测试
pytest -m "not slow"

# 只运行失败的测试
pytest --lf
```

### 附录 C：测试检查清单

**代码提交前检查**：

- [ ] 新增代码有对应的单元测试
- [ ] 所有测试用例通过（`pytest` 无报错）
- [ ] 测试覆盖率没有下降（`--cov` 检查）
- [ ] 没有跳过的测试（`@pytest.mark.skip`）
- [ ] Mock 测试能在无游戏环境下运行

---

 **批准人** : haneball17

 **日期** : 2026-02-10
