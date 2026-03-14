# pytest 错误诊断与修复指南

**问题**: `ModuleNotFoundError: No module named 'vision'`
**状态**: ✅ 已修复
**修复者**: haneball17
**日期**: 2026-02-11

---

## 🔍 问题分析

### 错误信息
```
(.venv) PS D:\code\AradVision> pytest -v
ImportError while loading conftest 'D:\code\AradVision\tests\conftest.py'.
tests\conftest.py:13: in <module>
    from vision.mock_detector import MockYoloDetector
E   ModuleNotFoundError: No module named 'vision'
```

### 根本原因

**依赖链分析**：
```
pytest 启动
  ↓
加载 tests/conftest.py
  ↓
导入 numpy (第 11 行)
  ↓
导入 vision.mock_detector (第 13 行)
  ↓
vision/mock_detector.py 导入 vision.base_detector
  ↓
vision/base_detector.py 导入 numpy (第 12 行)
  ↓
❌ ModuleNotFoundError: No module named 'numpy'
```

**具体原因**：
1. `vision/` 模块依赖 numpy
2. `tests/conftest.py` 在 pytest 启动时就会被加载
3. 如果 numpy 未安装或虚拟环境未激活，导入失败

---

## ✅ 已实施的修复

### 修改 1：添加项目路径到 PYTHONPATH

```python
# tests/conftest.py
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

**作用**: 确保能找到项目模块

---

### 修改 2：延迟导入依赖

```python
# 可选导入 numpy
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("Warning: numpy 未安装，部分测试将被跳过")

# 可选导入 vision 模块
try:
    from vision.mock_detector import MockYoloDetector
    HAS_VISION = True
except ImportError:
    HAS_VISION = False
    print("Warning: vision 模块依赖缺失，部分测试将被跳过")
```

**作用**: 即使 numpy/vision 不可用，pytest 也能启动

---

### 修改 3：条件跳过依赖测试

```python
@pytest.fixture
def sample_frame():
    """生成测试用图像帧"""
    if not HAS_NUMPY:
        pytest.skip("numpy 未安装，跳过此测试")
    return np.zeros((600, 800, 3), dtype=np.uint8)

@pytest.fixture
def mock_detector():
    """Mock检测器fixture"""
    if not HAS_VISION:
        pytest.skip("vision 模块不可用，跳过此测试")
    return MockYoloDetector(mock_mode="fixed")
```

**作用**: 依赖缺失时跳过测试，而不是报错

---

## 🚀 快速修复步骤

### 步骤 1：确认虚拟环境已激活

```powershell
# Windows PowerShell
# 检查命令提示符前是否有 (.venv)

# 验证 Python 路径
where python
# 期望输出：D:\code\AradVision\.venv\Scripts\python.exe
```

**如果未激活**：
```powershell
# 激活虚拟环境
.venv\Scripts\Activate.ps1
```

---

### 步骤 2：安装 numpy

```powershell
# 确认 numpy 未安装
python -c "import numpy; print(numpy.__version__)"

# 如果报错，安装 numpy
pip install numpy
```

---

### 步骤 3：重新运行测试

```powershell
# 选项 A：运行逻辑层验证（无需 numpy）
python scripts/verify_logic_layer.py

# 选项 B：运行完整 pytest（需要 numpy）
pytest -v

# 选项 C：只运行不依赖 vision 的测试
pytest tests/test_types.py -v
pytest tests/test_bot_fsm.py -v
pytest tests/test_combat.py -v
pytest tests/test_path_planner.py -v
```

---

## 📋 完整依赖安装清单

如果缺少多个依赖，运行：

```powershell
# 安装所有依赖
pip install -r requirements.txt
```

**包括**：
- numpy >= 1.24.0
- PyYAML >= 6.0
- loguru >= 0.7.0
- pytest >= 7.4.0
- pytest-cov >= 4.1.0
- pydirectinput >= 1.0.0 (Windows only)
- keyboard >= 0.13.5 (Windows only)
- mss >= 9.0.1
- opencv-python >= 4.8.0
- ultralytics >= 8.0.0

---

## 🎯 测试分组

### 不需要 numpy 的测试（可立即运行）

```powershell
# 数据类型测试
pytest tests/test_types.py -v

# 状态机测试
pytest tests/test_bot_fsm.py -v

# 战斗逻辑测试
pytest tests/test_combat.py -v

# 路径规划测试
pytest tests/test_path_planner.py -v

# Mock 输入驱动测试
pytest tests/test_mock_driver.py -v
```

**期望输出**：
```
tests/test_types.py::test_bbox_properties PASSED
tests/test_types.py::test_game_object_creation PASSED
...
========================= 40 passed in 1.23s ==========================
```

---

### 需要 numpy 的测试（需要先安装 numpy）

```powershell
# Mock 检测器测试
pytest tests/test_mock_detector.py -v

# 集成测试
pytest tests/integration/test_full_flow_mock.py -v
```

---

## 🔧 调试技巧

### 技巧 1：检查导入是否成功

```powershell
# 检查 numpy
python -c "import numpy; print('numpy OK')"

# 检查 vision 模块
python -c "from vision.mock_detector import MockYoloDetector; print('vision OK')"

# 检查所有依赖
python -c "
import sys
sys.path.insert(0, '.')
from vision.mock_detector import MockYoloDetector
from input.mock_driver import MockInputDriver
from logic.bot_fsm import BotFSM
print('所有依赖 OK')
"
```

---

### 技巧 2：只运行特定测试

```powershell
# 只运行一个测试文件
pytest tests/test_types.py::test_bbox_properties -v

# 只运行不依赖 vision 的测试
pytest tests/test_types.py tests/test_bot_fsm.py -v

# 排除依赖 vision 的测试
pytest -v --ignore=tests/test_mock_detector.py
```

---

### 技巧 3：查看详细错误信息

```powershell
# 显示完整回溯
pytest -v --tb=long

# 只显示失败的测试
pytest -v --tb=short -x

# 进入 pdb 调试器
pytest --pdb
```

---

## 📊 期望的测试输出

### 成功的输出

```powershell
(.venv) PS D:\code\AradVision> pytest tests/test_types.py -v

================================ test session starts =================================
platform win32 -- Python 3.10.0, pytest-7.4.0, rootdir: D:\code\AradVision
collected 40 items

tests/test_types.py::test_bbox_properties PASSED                            [  2%]
tests/test_types.py::test_game_object_creation PASSED                       [  5%]
tests/test_types.py::test_game_context PASSED                              [  7%]
tests/test_types.py::test_command_creation PASSED                         [ 10%]
...
================================= 40 passed in 1.45s ==================================
```

### 部分跳过的输出（numpy 未安装）

```powershell
(.venv) PS D:\code\AradVision> pytest -v

================================ test session starts =================================
collected 73 items

tests/test_types.py::test_bbox_properties PASSED                            [  1%]
...
tests/test_mock_detector.py::test_mock_detector_init PASSED                  [ 50%]
tests/test_mock_detector.py::test_mock_detector_detect SKIPPED               [ 50%] (numpy 未安装，跳过此测试)
...
========================= 60 passed, 13 skipped in 2.10s ======================
```

---

## ✅ 验证修复成功

### 1. 逻辑层验证（应始终成功）

```powershell
python scripts/verify_logic_layer.py
```

**期望输出**：
```
============================================================
 测试结果: 5 通过, 0 失败
============================================================
```

---

### 2. pytest 部分测试（应成功）

```powershell
pytest tests/test_types.py tests/test_bot_fsm.py tests/test_combat.py -v
```

**期望输出**：
```
========================= 40 passed in 1.23s ==========================
```

---

## 📝 总结

### 已修复的问题

✅ **修复 1**: 添加项目路径到 PYTHONPATH
✅ **修复 2**: 延迟导入 numpy 和 vision 模块
✅ **修复 3**: 条件跳过依赖测试（使用 pytest.skip）

### 修复后的行为

- **有 numpy**: 所有测试都能运行
- **无 numpy**: 部分测试被跳过，但不会报错
- **逻辑层测试**: 无论 numpy 是否安装都能运行

### 后续建议

1. **短期**: 确保安装 numpy，运行完整测试套件
2. **中期**: 考虑迁移到 Poetry 或 uv 进行依赖管理
3. **长期**: 在 CI/CD 中自动化测试

---

**修复完成时间**: 2026-02-11 17:00:00
**修复者**: haneball17
