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
# 1. 克隆/初始化项目
git init
python scripts/init_project.py

# 2. 确认目录结构创建成功
ls -la core/ logic/ vision/ input/ tests/

# 3. 运行初始测试
pytest tests/ -v
```

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

## 🔄 每日协作流程

### 早上 9:00 - 各自开始工作

```bash
# haneball17
git checkout -b feature/haneball17-day1
# 开始实现...

# yangmq17
git checkout -b feature/yangmq17-day1
# 开始实现...
```

### 中午 12:00 - 午餐休息

### 下午 14:00 - 继续开发

**遇到接口问题?**
```bash
# 立即沟通! 不要擅自修改接口
# 两人确认后, 在群组/文档中记录接口变更
```

### 晚上 18:00 - 提交代码

```bash
# 1. 运行测试
pytest tests/ -v

# 2. 提交代码
git add .
git commit -m "feat: 实现<模块名>"

# 3. 推送到远程
git push origin feature/<name>-day1
```

### 晚上 20:00 - 每日同步会议 (15-30分钟)

**会议内容:**
1. **演示成果** (各5分钟)
   - haneball17演示ConfigLoader、CaptureEngine
   - yangmq17演示InputDriver、KillSwitch

2. **代码审查** (10分钟)
   - 互相审查对方代码
   - 使用下面的审查清单

3. **确认明日计划** (5分钟)

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
```

---

## 🚨 常见问题

### Q1: Git冲突怎么办?

```bash
# 1. 拉取最新代码
git fetch origin dev

# 2. 合并到自己的分支
git merge origin/dev

# 3. 解决冲突
# 打开冲突文件，查找 <<<<<<< 标记
# 与对方协商后手动编辑

# 4. 标记冲突已解决
git add <冲突文件>
git commit

# 5. 如果不知道如何解决，找对方一起看
```

### Q2: 测试失败了怎么办?

```bash
# 1. 查看详细错误信息
pytest tests/ -v -s

# 2. 进入调试模式
pytest tests/ --pdb

# 3. 如果是自己代码的bug, 修复后重测
# 如果是对方接口的问题, 立即沟通!
```

### Q3: 如何快速运行项目验证?

```bash
# 创建一个测试脚本 test_integration.py
# 使用全Mock环境测试数据流

python test_integration.py
# 应该能看到:
# ✅ MockYoloDetector: 检测到5个对象
# ✅ MockInputDriver: 记录了10条指令
# ✅ 数据流正常!
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

# 2. 代码已合并到dev分支
git log --oneline dev

# 3. 两人都能运行以下命令
python -c "from core.types import GameObject; print('✅ types导入成功')"
python -c "from vision.mock_detector import MockYoloDetector; print('✅ Mock检测器导入成功')"
python -c "from input.mock_driver import MockInputDriver; print('✅ Mock驱动导入成功')"

# 4. 每日检查清单已勾选
# 查看 scripts/daily_checklist.md
```

---

## 📞 紧急联系

| 开发者 | 职责范围 | 问题类型 |
|--------|----------|----------|
| haneball17 | ConfigLoader, CaptureEngine, MockYoloDetector | 配置、截图、检测 |
| yangmq17 | types, InputDriver, KillSwitch | 数据模型、输入、安全 |

**遇到阻塞问题立即在群里沟通! 不要自己憋着!**

---

## 📚 参考文档

- [模块接口契约规范](docs/AradVision模块接口契约规范.md)
- [分模块开发指南](docs/AradVision分模块开发指南.md)
- [开发计划与里程碑](docs/AradVision开发计划与里程碑.md)
- [模块分配与协作方案](docs/AradVision模块分配与协作方案.md)

---

**祝开发顺利! 🚀**
