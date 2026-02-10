# 每日开发检查清单

## Day 1 (2024-XX-XX) - 基础设施与数据收集

### 🌅 早上 (9:00 - 12:00)

#### Dev A 任务清单
- [ ] 启动游戏，确认窗口标题
- [ ] 运行 `python scripts/init_project.py` 创建项目结构
- [ ] 运行 `python scripts/capture_training_data.py` 开始收集数据
  - 目标: 收集 200+ 张图片
  - 场景: 战斗场景、过图场景、拾取场景
- [ ] 收集过程中整理图片分类

#### Dev B 任务清单
- [ ] 运行 `python scripts/init_project.py` 创建项目结构
- [ ] 实现 `core/config_loader.py`
  - [ ] ConfigLoader 类
  - [ ] load_yaml() 方法
  - [ ] get() 方法
- [ ] 实现 `core/types.py` 数据模型
  - [ ] GameObject 类
  - [ ] BBox 类型
  - [ ] GameContext 类
  - [ ] Command 类
- [ ] 编写单元测试 `tests/test_config_loader.py`

### 🌞 下午 (14:00 - 18:00)

#### Dev A 任务清单
- [ ] 继续收集数据 (目标: 500+ 张)
- [ ] 开始准备标注环境
  - [ ] 安装 labelImg: `pip install labelImg`
  - [ ] 创建 classes.txt 文件
- [ ] 开始标注前 100 张图片

#### Dev B 任务清单
- [ ] 实现 `core/capture.py` - CaptureEngine 类
  - [ ] MSS 截图实现
  - [ ] 窗口查找功能
  - [ ] 性能优化 (< 5ms)
- [ ] 实现 `vision/mock_detector.py` - MockYoloDetector
  - [ ] 返回预设测试数据
  - [ ] 支持从 JSON 加载 mock 结果
- [ ] 实现 `input/mock_driver.py` - MockInputDriver
  - [ ] 记录指令历史
  - [ ] 不实际发送输入
- [ ] 编写对应单元测试

### 🌙 晚上 (19:00 - 21:00)

#### 两人共同任务
- [ ] **每日同步会议** (15分钟)
  - [ ] Dev A 汇报数据收集进度
  - [ ] Dev B 演示 Mock 框架
  - [ ] 确认接口契约无误
- [ ] **代码合并** - Dev B 提交代码到 Git
- [ ] **Day 1 验收**
  - [ ] 项目结构完整 ✓
  - [ ] ConfigLoader 可用 ✓
  - [ ] Mock 框架可用 ✓
  - [ ] 数据收集 ≥ 300 张 ✓

---

## Day 2 (2024-XX-XX) - 标注与模型训练准备

### 🌅 早上 (9:00 - 12:00)

#### Dev A 任务清单
- [ ] 继续标注数据 (目标: 完成核心 100 张)
- [ ] 验证标注质量
- [ ] 准备 YOLO 训练配置
  - [ ] 创建 `data.yaml` 数据集配置
  - [ ] 配置训练超参数

#### Dev B 任务清单
- [ ] 实现 `input/input_driver.py` - InputDriver 类
  - [ ] DirectInput 扫描码映射
  - [ ] tap() 方法
  - [ ] hold() 方法
  - [ ] 随机延迟实现
- [ ] 实现 `input/kill_switch.py` - KillSwitch 监听
  - [ ] F12 键监听
  - [ ] 紧急停止机制
- [ ] 编写单元测试

### 🌞 下午 (14:00 - 18:00)

#### Dev A 任务清单
- [ ] **启动 YOLO 训练** (关键路径!)
  - [ ] 确认数据集格式正确
  - [ ] 启动训练: `python vision/train_yolo.py`
  - [ ] 预计训练时间: 8-12 小时
- [ ] 同时继续标注剩余数据

#### Dev B 任务清单
- [ ] 实现 `vision/detector.py` - YoloDetector 接口
  - [ ] 定义 detect() 方法签名
  - [ ] 使用 MockYoloDetector 暂时实现
- [ ] 实现 `logic/bot_fsm.py` - BotFSM 状态机
  - [ ] 定义状态枚举
  - [ ] 实现 update() 方法
  - [ ] 状态转换逻辑
- [ ] 实现 `logic/combat.py` - CombatLogic 类
  - [ ] Y 轴对齐算法
  - [ ] 目标选择逻辑
  - [ ] 攻击距离判断

### 🌙 晚上 (19:00 - 21:00)

#### 两人共同任务
- [ ] **每日同步会议**
  - [ ] Dev A 检查训练进度
  - [ ] Dev B 演示 FSM 状态机
- [ ] **准备训练监控**
  - [ ] Dev A 设置训练完成通知
- [ ] **代码合并**
- [ ] **Day 2 验收**
  - [ ] YOLO 训练已启动 ✓
  - [ ] InputDriver 可用 ✓
  - [ ] FSM 核心逻辑完成 ✓

---

## Day 3 (2024-XX-XX) - MVP 集成与验收

### 🌅 早上 (9:00 - 12:00)

#### Dev A 任务清单
- [ ] 检查 YOLO 训练结果
  - [ ] 如果完成: 提取最佳权重
  - [ ] 如果未完成/失败: 启动 COCO 备用方案
- [ ] 实现真实的 `vision/detector.py`
- [ ] 模型性能测试

#### Dev B 任务清单
- [ ] 实现 `main.py` - 主循环
  - [ ] MainLoop 类
  - [ ] 帧率控制 (30 FPS)
  - [ ] 异常处理
- [ ] 集成所有模块
  - [ ] 替换 Mock 为真实实现
  - [ ] 数据流测试

### 🌞 下午 (14:00 - 18:00)

#### 两人共同任务
- [ ] **首次真实环境联调** 🔥
  - [ ] Dev B 启动游戏
  - [ ] Dev A 准备测试场景 (洛兰深处)
  - [ ] 运行 `python main.py`
  - [ ] 调试识别问题
- [ ] **MVP 验收测试**
  - [ ] 能识别怪物 ✓
  - [ ] 能 Y 轴对齐 ✓
  - [ ] 能执行攻击 ✓
  - [ ] F12 紧急停止 ✓

### 🌙 晚上 (19:00 - 21:00)

#### 两人共同任务
- [ ] **MVP 庆祝** 🎉
- [ ] **Day 3 回顾**
  - [ ] 记录遇到的问题
  - [ ] 记录解决方案
  - [ ] 更新文档
- [ ] **Day 4-7 规划调整**
  - [ ] 评估当前进度
  - [ ] 调整后续计划

---

## 紧急联系人

| 开发者 | 职责 | 联系方式 |
|--------|------|----------|
| Dev A  | AI/模型 | @xxx |
| Dev B  | 架构/逻辑 | @xxx |

## 关键决策记录

| 日期 | 决策内容 | 原因 |
|------|----------|------|
| Day X | XXXXX | XXXXX |

---

**使用说明**: 每天开始前复制此清单，勾选完成的项目。晚上复盘时更新。
