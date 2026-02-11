# AradVision 快速启动指南

## 📋 开发前准备

### 环境检查清单

```bash
# 1. 确认Python版本 (需要3.10+)
python --version

# 2. 创建虚拟环境
conda create -n aradvision python=3.10
conda activate aradvision

# 3. 安装依赖
pip install -r requirements.txt
```

### 第一次项目设置

```bash
# 1. 初始化Git仓库
git init
git branch -M main

# 2. 创建dev分支并切换
git checkout -b dev

# 3. 运行项目初始化脚本
python scripts/init_project.py

# 4. 确认目录结构创建成功
ls -la core/ logic/ vision/ input/ tests/

# 5. 运行初始测试
pytest tests/ -v

# 6. 初始提交
git add .
git commit -m "chore: 项目初始化，添加模板代码"

# 7. 推送到远程（如果有的话）
git remote add origin <你的仓库地址>
git push -u origin dev
git push -u origin main
```

---

## 🎯 简化的Git协作策略

### 核心原则

对于 **2人 + 3天** 的小型项目，我们采用**极简Git策略**：

```
✅ 策略：单一dev分支协作
❌ 避免：复杂的feature分支
✅ 关键：频繁同步 + 良好沟通
```

### 分支结构

```
main  ──── 稳定版本（每日晚上合并）
  │
dev   ──── 开发分支（两人都在这工作）
```

### 为什么不需要feature分支？

| 复杂方案 | ❌ 每人多个feature分支 | 简化方案 | ✅ 单一dev分支 |
|---------|---------------------|---------|--------------|
| 创建分支 | feature/haneball17-xxx | 无需创建分支 | 两人都在dev |
| 合并代码 | 频繁merge到dev | 自动同步 | git pull |
| 代码审查 | PR流程 | 直接沟通 | 对话/屏幕共享 |
| 时间开销 | 每天30分钟在Git上 | 每天5分钟在Git上 | 更多时间写代码 |

---

## 👥 开发者分工

### haneball17 - 任务清单

**Day 1 上午 (3h)**
```bash
# 必须完成的任务 (P0):
1. core/config_loader.py       [2h] - 配置加载器
2. core/capture.py              [1h] - 截图引擎框架
```

**Day 1 下午 (4h)**
```bash
# 必须完成的任务 (P0):
1. vision/base_detector.py     [1h] - 检测器抽象类 ✓ (已提供)
2. vision/mock_detector.py     [1h] - Mock检测器 ✓ (已提供)
3. core/log_system.py          [1h] - 日志系统
4. 编写单元测试                [1h] - 测试上述模块
```

**Day 1 验收标准**
- [ ] ConfigLoader可加载YAML配置
- [ ] CaptureEngine可截取屏幕
- [ ] MockYoloDetector通过单元测试
- [ ] 所有测试通过: `pytest tests/test_mock_detector.py -v`

---

### yangmq17 - 任务清单

**Day 1 上午 (3h)**
```bash
# 必须完成的任务 (P0):
1. core/types.py               [2h] - 核心数据模型 ✓ (已提供)
2. core/exceptions.py          [0.5h] - 异常类定义 ✓ (已提供)
3. input/base_driver.py        [0.5h] - 输入驱动抽象类 ✓ (已提供)
```

**Day 1 下午 (4h)**
```bash
# 必须完成的任务 (P0):
1. input/mock_driver.py        [1h] - Mock输入驱动 ✓ (已提供)
2. input/input_driver.py       [2h] - 真实输入驱动
3. input/kill_switch.py        [1h] - F12紧急停止
4. 编写单元测试                [1h] - 测试上述模块
```

**Day 1 验收标准**
- [ ] 核心数据类型定义完整
- [ ] MockInputDriver通过单元测试
- [ ] InputDriver可发送键盘输入
- [ ] KillSwitch可监听F12
- [ ] 所有测试通过: `pytest tests/test_mock_driver.py tests/test_types.py -v`

---

## 🔄 每日协作流程（简化版）

### 早上 9:00 - 开始工作

```bash
# haneball17 和 yangmq17 都执行

# 1. 确保在dev分支
git checkout dev

# 2. 拉取最新代码
git pull origin dev

# 3. 开始工作...
# 各自开发自己的模块
```

### 上午工作中 - 频繁提交（每1-2小时）

```bash
# haneball17: 完成ConfigLoader后

# 1. 运行测试
pytest tests/test_config_loader.py -v

# 2. 提交代码
git add core/config_loader.py tests/test_config_loader.py
git commit -m "feat(haneball17): 实现ConfigLoader及其测试"

# 3. 立即推送（让对方能获取）
git push origin dev

# 4. 继续工作...
```

```bash
# yangmq17: 完成types.py后

# 1. 运行测试
pytest tests/test_types.py -v

# 2. 提交代码
git add core/types.py tests/test_types.py
git commit -m "feat(yangmq17): 完成核心数据模型定义"

# 3. 立即推送
git push origin dev

# 4. 继续工作...
```

### 中午 12:00 - 午餐前最后一次同步

```bash
# 两人都执行
git pull origin dev
# 获取对方的最新代码
```

### 下午 14:00 - 继续开发

**开始下一个模块前，先拉取：**
```bash
git pull origin dev
```

**遇到接口问题？**
```bash
# 立即沟通！不要擅自修改接口！
# 两人确认后，更新接口文档
```

### 下午 - 继续频繁提交

```bash
# 每1-2小时提交一次
# 完成 → 测试 → 提交 → 推送 → 继续
```

### 晚上 18:00 - 工作结束前

```bash
# 两人都执行

# 1. 最后一次拉取
git pull origin dev

# 2. 运行所有测试
pytest tests/ -v

# 3. 推送今天的所有工作
git push origin dev
```

### 晚上 20:00 - 同步会议后

```bash
# 代码审查完成后，合并到main

# 1. 切换到main
git checkout main

# 2. 合并dev
git merge dev

# 3. 推送到远程
git push origin main

# 4. 切回dev，准备明天工作
git checkout dev
```

---

## 🚨 避免冲突的黄金法则

### 1. 接口先行（最重要！）

```python
# Day 1 早上，两人一起花30分钟定义好所有接口

# core/types.py - yangmq17
class GameObject:
    ...

# vision/base_detector.py - haneball17
class BaseDetector:
    ...

# 后续各自实现，不会冲突！
```

### 2. 按文件分工

```
✅ 好的分工（不会冲突）:
├── core/
│   ├── config_loader.py    ← haneball17负责
│   ├── capture.py          ← haneball17负责
│   └── types.py            ← yangmq17负责
└── input/
    ├── input_driver.py     ← yangmq17负责
    └── kill_switch.py      ← yangmq17负责

❌ 不好的分工（会冲突）:
├── logic/
│   └── bot_fsm.py          ← 两人同时改这个文件！
```

### 3. 提交规范

```bash
# 提交信息格式
<类型>(开发者): 简短描述

# 示例：
feat(haneball17): 实现ConfigLoader
test(haneball17): 添加ConfigLoader单元测试
feat(yangmq17): 实现InputDriver
fix(yangmq17): 修复KillSwitch的线程问题
docs: 更新QUICKSTART文档
chore: 更新requirements.txt
```

### 4. 同步节奏

```
推荐节奏：
┌─────────────────────────────────────────────────────────┐
│  09:00  ───→  git pull                                  │
│  10:00  ───→  完成小功能 → test → commit → push         │
│  11:00  ───→  git pull → 继续开发                        │
│  12:00  ───→  git pull → 午餐                            │
│  14:00  ───→  继续开发                                   │
│  15:30  ───→  完成 → test → commit → push                │
│  18:00  ───→  最后一次 pull → test → push               │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ 代码审查清单

### haneball17 审查 yangmq17 的代码

```markdown
## core/types.py
- [ ] 所有数据类使用@dataclass
- [ ] GameObject.foot_point计算逻辑正确 (y2*0.95 + y1*0.05)
- [ ] 类型提示完整
- [ ] Google风格docstring

## input/input_driver.py
- [ ] 使用DirectInput扫描码
- [ ] tap()和hold()有随机延迟
- [ ] hold()有最小持续时间限制(50ms)
- [ ] 异常处理完善

## input/kill_switch.py
- [ ] F12监听在独立线程
- [ ] 能立即停止所有输入
- [ ] 使用os._exit(0)强制退出
```

### yangmq17 审查 haneball17 的代码

```markdown
## core/config_loader.py
- [ ] 支持YAML格式
- [ ] get()方法支持默认值
- [ ] 单例模式实现正确
- [ ] 异常处理(ConfigurationError)

## core/capture.py
- [ ] 使用MSS截图
- [ ] 能自动查找游戏窗口
- [ ] 截图性能<5ms
- [ ] 窗口最小化时抛出CaptureError

## vision/mock_detector.py
- [ ] 继承BaseDetector
- [ ] detect()返回GameObject列表
- [ ] load_model()总是返回True
- [ ] 测试数据覆盖所有对象类型
```

---

## 🆘 冲突解决（简化版）

### 如果真的遇到冲突了

```bash
# 1. git pull时发现冲突
git pull origin dev
# CONFLICT (content): Merge conflict in xxx.py

# 2. 不要慌！立即找对方

# 3. 两人一起打开冲突文件
# 查找冲突标记：
<<<<<<< HEAD
# yangmq17的代码
=======
# haneball17的代码
>>>>>>> origin/dev

# 4. 讨论后手动编辑，保留正确版本

# 5. 保存文件，标记冲突已解决
git add xxx.py

# 6. 完成合并
git commit

# 7. 立即推送
git push origin dev
```

### 冲突预防（比解决更重要）

| 预防措施 | 效果 |
|---------|------|
| ✅ 接口先定义好 | 🎯 消除90%的冲突 |
| ✅ 按文件分工 | 🎯 消除80%的冲突 |
| ✅ 频繁pull/push（1-2小时） | 🎯 快速发现冲突 |
| ✅ 提交前沟通 | 🎯 避免重复工作 |
| ✅ 小步快跑 | 🎯 冲突范围小 |

---

## 🧪 测试命令速查

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定文件测试
pytest tests/test_types.py -v

# 运行特定类测试
pytest tests/test_types.py::TestGameObject -v

# 运行特定方法测试
pytest tests/test_types.py::TestGameObject::test_foot_point_calculation -v

# 查看测试覆盖率
pytest tests/ --cov=core --cov=vision --cov=input --cov-report=html

# 只运行标记为unit的测试
pytest -m unit -v

# 并行运行测试(更快的!)
pytest -n auto tests/

# 查看详细输出
pytest tests/ -v -s

# 进入调试模式
pytest tests/ --pdb
```

---

## 🚨 常见问题

### Q1: 测试失败了怎么办?

```bash
# 1. 查看详细错误信息
pytest tests/ -v -s

# 2. 进入调试模式
pytest tests/ --pdb

# 3. 如果是自己代码的bug，修复后重测
# 如果是对方接口的问题，立即沟通!
```

### Q2: 如何快速验证数据流?

```bash
# 创建一个快速测试脚本 test_flow.py
# 使用全Mock环境测试数据流

python test_flow.py
# 应该能看到:
# ✅ MockYoloDetector: 检测到5个对象
# ✅ MockInputDriver: 记录了10条指令
# ✅ 数据流正常!
```

### Q3: 对方修改了接口怎么办?

```bash
# 1. 先pull最新代码
git pull origin dev

# 2. 可能会有冲突或编译错误

# 3. 立即沟通确认接口变更

# 4. 根据新接口调整自己的代码

# 5. 重新测试、提交
```

### Q4: Git命令记不住怎么办?

```bash
# 日常只需要记住4个命令：
git pull origin dev    # 获取最新代码
git add .              # 添加修改
git commit -m "..."    # 提交
git push origin dev    # 推送

# 其他命令查看Git文档或问对方
```

---

## 📁 目录结构参考

```
AradVision/
├── core/                   # (yangmq17 Day 1上午完成)
│   ├── __init__.py
│   ├── types.py            ✓ 核心数据模型
│   ├── exceptions.py       ✓ 异常类
│   ├── config_loader.py    (haneball17 Day 1上午)
│   ├── capture.py          (haneball17 Day 1上午)
│   └── log_system.py       (haneball17 Day 1下午)
│
├── vision/                 # (haneball17 Day 1下午)
│   ├── __init__.py
│   ├── base_detector.py    ✓ 检测器抽象类
│   └── mock_detector.py    ✓ Mock检测器
│
├── input/                  # (yangmq17 Day 1下午)
│   ├── __init__.py
│   ├── base_driver.py      ✓ 输入驱动抽象类
│   ├── mock_driver.py      ✓ Mock输入驱动
│   ├── input_driver.py     (yangmq17 Day 1下午)
│   └── kill_switch.py      (yangmq17 Day 1下午)
│
├── logic/                  # (Day 2)
│   └── __init__.py
│
├── tests/                  # 单元测试
│   ├── conftest.py         ✓ pytest配置
│   ├── test_types.py       ✓ types测试
│   ├── test_mock_detector.py ✓ Mock检测器测试
│   └── test_mock_driver.py ✓ Mock驱动测试
│
├── configs/
│   └── config.yaml         ✓ 配置模板
│
├── scripts/
│   ├── init_project.py     ✓ 项目初始化脚本
│   └── daily_checklist.md  每日检查清单
│
└── main.py                 (Day 3)
```

---

## 🎯 Day 1 完成标志

两人都需要完成的验收:

```bash
# 1. 所有单元测试通过
pytest tests/ -v

# 2. 查看今天的提交历史
git log --oneline --since="today"

# 3. 两人都能运行以下命令
python -c "from core.types import GameObject; print('✅ types导入成功')"
python -c "from vision.mock_detector import MockYoloDetector; print('✅ Mock检测器导入成功')"
python -c "from input.mock_driver import MockInputDriver; print('✅ Mock驱动导入成功')"

# 4. 确认代码已推送到远程
git log --oneline origin/dev | head

# 5. 每日检查清单已勾选
# 查看 scripts/daily_checklist.md
```

---

## 📞 紧急联系

| 开发者 | 职责范围 | 问题类型 |
|--------|----------|----------|
| haneball17 | ConfigLoader, CaptureEngine, MockYoloDetector | 配置、截图、检测 |
| yangmq17 | types, InputDriver, KillSwitch | 数据模型、输入、安全 |

**遇到阻塞问题立即沟通! 不要自己憋着!**

---

## 📚 参考文档

- [模块接口契约规范](docs/AradVision模块接口契约规范.md)
- [开发计划与里程碑](docs/AradVision开发计划与里程碑.md)
- [模块分配与协作方案](docs/AradVision模块分配与协作方案.md)
- [YOLO训练专项指南](docs/AradVision_YOLO训练专项指南.md)

---

## 💡 最重要的提醒

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  对于 2人 + 3天 的小型项目：                            │
│                                                         │
│  ✅ 简单的Git策略  >  复杂的Git流程                     │
│  ✅ 频繁沟通         >  完美的文档                      │
│  ✅ 小步快跑         >  大爆炸提交                      │
│  ✅ 接口先行         >  后期重构                        │
│                                                         │
│  核心：写代码 > Git管理                                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

**祝开发顺利! 🚀**
