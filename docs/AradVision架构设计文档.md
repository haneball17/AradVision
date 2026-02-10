
# 架构设计文档 (Architecture Design Document)

**项目名称**：AradVision - DNF 视觉辅助自动化系统
**版本**：V1.0
**状态**：正式版
**最后更新日期**：2026-02-10

---

## 1. 引言 (Introduction)

### 1.1 设计目标

本设计旨在构建一个**高内聚、低耦合**的自动化系统架构。

* **高内聚**：视觉模块只负责看，逻辑模块只负责想，驱动模块只负责做。
* **低耦合**：更换识别模型（如从 YOLOv8 换到 YOLOv11）不应影响逻辑代码；更换游戏窗口分辨率不应影响核心寻路算法。

### 1.2 架构风格

采用 **分层架构 (Layered Architecture)** 与 **事件驱动 (Event-Driven)** 相结合的模式。

* **分层**：自下而上分别为 驱动层 -> 感知层 -> 决策层 -> 应用层。
* **事件**：系统通过“帧更新”事件驱动主循环，每一帧的图像数据流动触发后续的逻辑计算。

---

## 2. 技术选型与技术栈 (Technology Stack)

| 层次               | 核心技术组件                               | 选型理由                                                             |
| ------------------ | ------------------------------------------ | -------------------------------------------------------------------- |
| **开发语言** | **Python 3.10+**                     | 拥有最丰富的 AI 生态（PyTorch, OpenCV）和自动化库。                  |
| **视觉感知** | **Ultralytics YOLOv8**               | 目前工业界最成熟的实时目标检测模型，兼顾速度与精度。                 |
| **图像处理** | **OpenCV (cv2)**                     | 用于色彩过滤（血条）、模板匹配（技能CD）及图像预处理。               |
| **屏幕捕获** | **MSS (Multiple Screen Shots)**      | 相比 PIL 或 PyAutoGUI，MSS 在 Windows 下的截图速度快 5-10 倍。       |
| **输入驱动** | **PyDirectInput** / **Ctypes** | DNF屏蔽了高层虚拟按键，必须使用底层的 DirectX 扫描码（Scan Codes）。 |
| **配置管理** | **PyYAML**                           | 配置文件可读性强，方便非程序员调整阈值。                             |
| **加速推理** | **CUDA 11.x + TensorRT**             | 利用 NVIDIA 显卡加速，确保推理延迟 < 30ms。                          |

---

## 3. 系统组件架构 (Component Architecture)

系统划分为四个主要子系统，数据流向为单向流动。

### 3.1 模块划分

#### A. 基础设施层 (Infrastructure Layer)

负责与操作系统和硬件交互，屏蔽底层细节。

* **CaptureEngine**: 负责维护游戏窗口句柄，处理分辨率适配，提供 Raw Image。
* **InputDriver**: 封装 Win32 API 和 SendInput，提供 `press`, `release`, `move_mouse` 等原子操作。
* **ConfigLoader**: 读取 `config.yaml`，提供全局参数单例。

#### B. 感知层 (Perception Layer)

负责将非结构化的图像数据转换为结构化的语义数据。

* **ObjectDetector**: 封装 YOLO 模型，输出 `List[GameObject]`（包含类别、坐标、置信度）。
* **StateReader**: 封装 OpenCV 算法，输出 `PlayerState`（HP/MP、技能CD状态、当前房间位置）。
* **CoordinateMapper**: 将屏幕坐标  转换为游戏世界坐标 ，特别是处理 **Y轴深度** 修正。

#### C. 决策层 (Decision Layer)

负责“大脑”的思考，维护游戏状态机。

* **WorldModel**: 维护当前环境的上下文（例如：房间内还有多少怪？门开了吗？）。
* **BotFSM (Finite State Machine)**: 核心状态机，管理 `Idle`, `Combat`, `Loot`, `Maps` 状态的流转。
* **PathPlanner**: 局部路径规划，计算从当前位置到目标的移动向量，包含简单的避障逻辑。

#### D. 应用层 (Application Layer)

负责程序的生命周期管理。

* **MainLoop**: 控制帧率（FPS），调度各层模块。
* **OverlaySystem**: (Debug用) 在游戏窗口之上绘制透明蒙版，显示识别框和状态信息。
* **WatchDog**: 监控程序健康状态，负责异常熔断（F12 紧急停止）。

---

## 4. 模块关系与数据流 (Data Flow)

整个系统运行在一个主 `While` 循环中，单次循环的数据流如下：

1. **输入阶段 (Input)**

* `CaptureEngine` 截取当前帧 。
* 数据包：`RawFrame (1920x1080 BGR)`

2. **感知阶段 (Perception)**

* `ObjectDetector` 推理 。
* `StateReader` 分析 UI 区域。
* 数据包：`ContextData { monsters: [...], hero_pos: (x,y), hp: 80% }`

3. **决策阶段 (Decision)**

* `BotFSM` 根据 `ContextData` 更新当前状态（如：发现怪物 -> 进入战斗）。
* `PathPlanner` 计算移动指令。
* 数据包：`ActionCommand { type: 'ATTACK', target: (x,y), skill: 'A' }`

4. **执行阶段 (Action)**

* `InputDriver` 解析 `ActionCommand`。
* 加入 **随机延迟 (Random Delay)**。
* 发送硬件信号 -> 操作系统 -> 游戏客户端。

---

## 5. 接口定义 (API Definition)

虽然是本地单体应用，但为了模块解耦，我们需要定义内部 Python 类的接口。

### 5.1 视觉接口 (IVision)

```python
class IVision:
    def detect(self, image: np.ndarray) -> DetectionResult:
        """
        输入: OpenCV图像矩阵
        输出: 包含所有识别对象的列表
        """
        pass

@dataclass
class DetectionResult:
    timestamp: float
    player: Box | None
    monsters: List[Box]
    items: List[Box]
    doors: List[Box]

```

### 5.2 控制接口 (IController)

```python
class IController:
    def execute(self, command: Command):
        """
        执行具体的游戏操作
        """
        pass

@dataclass
class Command:
    action_type: str  # 'MOVE', 'ATTACK', 'SKILL', 'PICKUP'
    direction: Tuple[int, int] = None # (dx, dy)
    key_code: str = None
    duration: float = 0.0

```

---

## 6. 系统非功能属性 (Non-Functional Requirements)

### 6.1 性能与伸缩性 (Performance)

* **推理优化**：必须使用 `.pt` 模型的 FP16（半精度）模式推理，以减少显存占用并提高速度。
* **多线程策略**：
* **主线程**：负责 UI 更新和逻辑判断。
* **视觉线程**：独立运行 YOLO 推理，通过 `Queue` 传递结果（避免推理阻塞输入模拟）。
* *注意*：初期版本为降低复杂度，可先采用单线程模型，若 FPS < 15 再重构为多线程。

### 6.2 安全性与合规性 (Safety)

* **Kill Switch (熔断器)**：
* 独立的一个 `Listener` 线程监听键盘。
* 一旦检测到 `F12`，直接调用 `os._exit(0)` 强行终止进程，防止逻辑死循环导致角色失控。
* **反检测 (Anti-Cheat Evasion)**：
* **不注入**：严禁使用 `WriteProcessMemory` 或 `ReadProcessMemory`。
* **非线性移动**：鼠标移动轨迹（如有）需使用贝塞尔曲线算法，避免直线跳转。
* **输入抖动**：按键时长 (Press Duration) 需符合高斯分布（均值 100ms，方差 20ms）。

### 6.3 健壮性 (Robustness)

* **目标丢失处理**：若连续 5 帧识别不到怪物，不应立即停止，而应保持上一帧的运动趋势（惯性预测）。
* **分辨率自适应**：系统启动时自动读取游戏窗口大小，并重新计算坐标映射比例，无需硬编码坐标值。

---

**批准人**：haneball17
**日期**：2026-02-10
