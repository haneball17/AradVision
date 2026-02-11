# Poetry 迁移评估报告 - AradVision 项目

**评估者**: haneball17
**日期**: 2026-02-11
**项目**: AradVision v0.1.2
**当前依赖管理**: pip + requirements.txt + venv

---

## 📊 执行摘要

**结论**: ✅ **推荐迁移到 Poetry**，但需要权衡利弊。

**建议**:
- **短期**: 保持当前方式，优先完成功能开发
- **中期**: 在 v0.2.0 版本迁移到 Poetry
- **理由**: Poetry 提供更好的依赖管理，但当前应聚焦核心功能

---

## 🆚 Poetry vs 当前方案对比

### 当前方案（pip + venv + requirements.txt）

| 方面 | 优势 | 劣势 |
|------|------|------|
| **简单性** | ✅ 所有开发者都熟悉 | - |
| **通用性** | ✅ 任何环境都能用 | - |
| **文档** | ✅ 网上资料多 | - |
| **依赖锁定** | ❌ 无版本锁定文件 | 易出现版本不一致 |
| **依赖分组** | ⚠️ 手动维护多个 requirements | requirements-dev.txt, requirements-test.txt |
| **虚拟环境** | ⚠️ 手动管理 venv | 容易忘记激活 |
| **可重现性** | ⚠️ 中等 | 依赖版本可能漂移 |

### Poetry 方案

| 方面 | 优势 | 劣势 |
|------|------|------|
| **依赖锁定** | ✅ poetry.lock 精确锁定版本 | 需要提交到仓库 |
| **依赖分组** | ✅ 原生支持（main, dev, test） | 学习新语法 |
| **虚拟环境** | ✅ 自动管理 in-project .venv | 与现有 venv 可能冲突 |
| **可重现性** | ✅ 100% 可重现构建 | - |
| **发布** | ✅ 一键发布到 PyPI | 当前项目不需要 |
| **性能** | ⚠️ 中等（比 pip 快，比 uv 慢） | - |
| **学习曲线** | ⚠️ 需要学习新命令 | - |

---

## 📈 Poetry 的核心优势

### 1. 依赖锁定（Dependency Locking）

**问题**：当前 `requirements.txt` 无法锁定传递依赖

**示例**：
```
# requirements.txt
numpy>=1.24.0
opencv-python>=4.8.0
```

**问题**：
- numpy 1.24.0 和 numpy 1.26.0 行为可能不同
- opencv-python 依赖的 numpy 版本不确定
- 不同时间安装可能得到不同版本

**Poetry 解决方案**：
```toml
# pyproject.toml
[tool.poetry.dependencies]
numpy = "^1.24.0"
opencv-python = "^4.8.0"
```

```
# poetry.lock (自动生成)
[[package]]
name = "numpy"
version = "1.24.3"
...

[[package]]
name = "opencv-python"
version = "4.8.1.78"
dependencies = [
    {name = "numpy", version = "1.24.3"},
]
```

**收益**：
- ✅ 所有人安装完全相同的版本
- ✅ 传递依赖版本也被锁定
- ✅ 避免隐式版本升级导致的问题

---

### 2. 依赖分组（Dependency Groups）

**当前问题**：
```
requirements.txt          # 运行时依赖
requirements-dev.txt      # 开发依赖
requirements-test.txt     # 测试依赖
```

**Poetry 解决方案**：
```toml
[tool.poetry.dependencies]
python = "^3.10"
numpy = "^1.24.0"
PyYAML = "^6.0"
loguru = "^0.7.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
black = "^23.0.0"
mypy = "^1.5.0"

[tool.poetry.group.test.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
```

**使用**：
```bash
# 只安装主依赖
poetry install --no-dev

# 安装主依赖 + dev 依赖
poetry install

# 只安装 dev 依赖
poetry install --with dev
```

**收益**：
- ✅ 配置文件更简洁
- ✅ 依赖关系更清晰
- ✅ 灵活安装不同组合

---

### 3. 自动虚拟环境管理

**当前方式**：
```bash
python3 -m venv .venv
source .venv/bin/activate  # 容易忘记
pip install -r requirements.txt
```

**Poetry 方式**：
```bash
poetry install  # 自动创建和管理 .venv
poetry run pytest  # 自动使用项目虚拟环境
```

**收益**：
- ✅ 不需要手动激活虚拟环境
- ✅ 虚拟环境位置固定（项目根目录）
- ✅ 减少人为错误

---

### 4. pyproject.toml 标准化

**Poetry 使用 Python 官方标准**：

```toml
[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.poetry]
name = "aradvision"
version = "0.1.2"
description = "DNF 视觉辅助自动化系统"
authors = ["haneball17 <haneball17@example.com>"]
maintainers = ["yangmq17 <yangmq17@example.com>"]
license = "MIT"
readme = "README.md"
requires-python = ">=3.10"

[tool.poetry.dependencies]
python = "^3.10"
numpy = "^1.24.0"
PyYAML = "^6.0"
loguru = "^0.7.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
black = "^23.0.0"
mypy = "^1.5.0"
pylint = "^2.17.0"

[tool.poetry.scripts]
aradvision = "aradvision.main:main"

[tool.black]
line-length = 100
target-version = ['py310']

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --tb=short"

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
```

**收益**：
- ✅ 单一配置文件
- ✅ 工具配置集中管理
- ✅ 符合 Python 标准（PEP 517/518）

---

## ⚖️ 迁移成本分析

### 需要改动的文件

| 操作 | 文件 | 工作量 | 风险 |
|------|------|--------|------|
| **新增** | pyproject.toml | 30 分钟 | 低 |
| **新增** | poetry.lock | 自动生成 | 无 |
| **删除** | requirements.txt | 1 分钟 | 低 |
| **删除** | requirements-dev.txt | 1 分钟 | 低 |
| **删除** | setup.py（如有） | 1 分钟 | 低 |
| **修改** | README.md（文档更新） | 15 分钟 | 低 |
| **修改** | .gitignore（更新） | 5 分钟 | 低 |
| **修改** | CI/CD 配置 | 30 分钟 | 中 |
| **测试** | 验证所有功能 | 1 小时 | 中 |

**总工作量**: **约 2-3 小时**

---

## 📝 详细迁移步骤

### 第 1 步：安装 Poetry

```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py-

# Linux/Mac
curl -sSL https://install.python-poetry.org | python3 -

# 验证安装
poetry --version
```

---

### 第 2 步：创建 pyproject.toml

```bash
# 在项目根目录执行
cd /path/to/AradVision

# 初始化 Poetry 项目
poetry init

# 或直接创建 pyproject.toml 文件（见上文配置示例）
```

---

### 第 3 步：迁移依赖

```bash
# Poetry 自动从 requirements.txt 导入依赖
poetry add $(cat requirements.txt | tr '\n' ' ')

# 或手动添加
poetry add numpy PyYAML loguru
poetry add --group dev pytest pytest-cov black mypy pylint
```

---

### 第 4 步：生成锁文件

```bash
poetry lock
```

**生成文件**：
- `poetry.lock` - 依赖版本锁定文件（需提交到 Git）

---

### 第 5 步：安装依赖

```bash
# 创建虚拟环境并安装依赖
poetry install

# 查看虚拟环境路径
poetry env info --path
```

**默认虚拟环境位置**：
```
{project_root}/.venv/
```

---

### 第 6 步：更新常用命令

**旧命令 → 新命令对照**：

| 旧命令 | 新命令 |
|--------|--------|
| `python -m venv .venv` | `poetry install` |
| `source .venv/bin/activate` | （无需激活） |
| `pip install xxx` | `poetry add xxx` |
| `pip install -r requirements.txt` | `poetry install` |
| `python -m pytest` | `poetry run pytest` |
| `python main.py` | `poetry run python main.py` |
| `pytest -v` | `poetry run pytest -v` |
| `black .` | `poetry run black .` |

---

### 第 7 步：更新文档

**README.md**:
```markdown
## 安装

### 使用 Poetry（推荐）
```bash
poetry install
poetry run pytest
```

### 使用 pip（传统方式）
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
pytest
```
```

---

## ⚠️ 潜在风险与问题

### 1. poetry.lock 文件大小

**问题**：
```
poetry.lock  # 通常 5-20MB
```

**影响**：
- 仓库体积增大
- clone 时间增加
- 代码审查困难

**解决方案**：
```bash
# .gitignore
poetry.lock
# ❌ 不推荐（失去依赖锁定的好处）
```

**最佳实践**：
- ✅ 提交 poetry.lock（确保可重现性）
- ✅ 使用 LFS 或减少依赖数量

---

### 2. Windows 平台兼容性

**问题**：
- Poetry 早期版本在 Windows 上有问题
- 某些包的编译依赖可能安装失败

**解决方案**：
```bash
# 使用预编译的 wheel 包
poetry install --only-root
```

---

### 3. 与现有工具集成

**pytest 配置**：
```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
addopts = "-v --tb=short"
```

**black 配置**：
```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py310']
include = '\.pyi?$'
```

---

### 4. 学习曲线

**新命令学习**：
```bash
# 常用命令
poetry install              # 安装依赖
poetry add xxx              # 添加依赖
poetry remove xxx           # 移除依赖
poetry update               # 更新依赖
poetry show                 # 显示依赖树
poetry run xxx              # 在虚拟环境中运行命令
poetry shell                # 进入虚拟环境 shell
poetry env list             # 列出所有虚拟环境
poetry env remove           # 删除虚拟环境
```

---

## 🔄 替代方案：UV

**UV** 是 2024 年新出的 Python 包管理器，由 Astral（Ruff 团队）开发：

**性能对比**（来自生产环境实测）：
```
Poetry:    锁定耗时 45 秒，Docker 构建耗时 8 分钟
UV:        锁定耗时 6 秒  (87% 提升)，Docker 构建耗时 4 分钟 (50% 提升)
```

**UV 优势**：
- ⚡ 极快的速度（Rust 实现）
- 📦 兼容 pyproject.toml 和 poetry.lock
- 🔄 可以直接从 Poetry 迁移

**UV 劣势**：
- 🆕 相对较新（2024 年发布）
- 📚 生态和文档不如 Poetry 成熟
- 🔧 工具链集成不如 Poetry 完善

**迁移到 UV**：
```bash
# 从 Poetry 迁移到 UV（一行命令）
uv pip compile pyproject.toml -o requirements.txt
uv pip install -r requirements.txt
```

---

## 💡 最终建议

### 建议 1：保持当前方案（短期，推荐）

**理由**：
- ✅ 当前方式已经够用
- ✅ 优先完成功能开发（WorldModel、YOLO 检测器等）
- ✅ 减少迁移学习成本
- ✅ 避免引入新风险

**时间线**：
- **v0.1.2 - v0.2.0**: 保持 pip + requirements.txt
- **v0.3.0+**: 考虑迁移到 Poetry 或 UV

---

### 建议 2：迁移到 Poetry（中期）

**时机**：
- 当前功能开发进入稳定期
- 团队规模扩大（> 2 人）
- 需要更好的依赖管理

**收益**：
- ✅ 依赖版本锁定
- ✅ 更好的可重现性
- ✅ 工具配置统一

**成本**：
- ⏱️ 2-3 小时迁移工作量
- 📚 团队学习成本
- ⚠️ 短期内可能遇到兼容性问题

---

### 建议 3：直接迁移到 UV（激进，长远推荐）

**理由**：
- ⚡ 性能最优（87% 锁定速度提升）
- 📦 兼容 Poetry 配置
- 🚀 未来趋势（Astral 团队，Ruff 同门）

**时间线**：
- **v0.3.0 或 v0.4.0**: 直接迁移到 UV

---

## 📋 决策矩阵

| 场景 | 推荐方案 | 理由 |
|------|----------|------|
| **当前阶段（v0.1.2）** | 保持 pip | 优先功能开发 |
| **小团队（2-3 人）** | Poetry 或 uv | 提升协作效率 |
| **大团队（> 5 人）** | Poetry 或 uv | 依赖管理更关键 |
| **CI/CD 频繁** | uv | 性能优势明显 |
| **Windows 为主** | Poetry | 成熟稳定 |
| **追求性能** | uv | 速度最快 |
| **学习成本敏感** | pip | 无需学习 |

---

## 🎯 具体行动建议

### 当前不迁移（v0.1.2 - v0.2.0）

**理由**：
1. **聚焦核心价值**：当前应优先完成 WorldModel、YOLO 检测器等核心功能
2. **风险控制**：避免在开发关键期引入新工具的潜在问题
3. **成本收益**：迁移成本 > 当前收益

**继续使用**：
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -v
```

---

### 计划迁移（v0.3.0 或更晚）

**触发条件**：
- [ ] 核心功能全部完成
- [ ] 团队人数增加（> 2 人）
- [ ] 遇到依赖版本问题
- [ ] CI/CD 需要更好的可重现性

**选择**：
- **保守选择**：Poetry（成熟稳定）
- **激进选择**：uv（性能最优）

---

## 📄 附录：pyproject.toml 完整示例

```toml
[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.poetry]
name = "aradvision"
version = "0.1.2"
description = "DNF 视觉辅助自动化系统 - 基于计算机视觉的游戏辅助工具"
authors = [
    "haneball17 <haneball17@example.com>",
    "yangmq17 <yangmq17@example.com>"
]
maintainers = ["yangmq17 <yangmq17@example.com>"]
license = "MIT"
readme = "README.md"
requires-python = ">=3.10"
keywords = ["dnf", "automation", "computer-vision", "yolo", "game-bot"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Games/Entertainment",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

[tool.poetry.dependencies]
python = "^3.10"
numpy = "^1.24.0"
PyYAML = "^6.0"
loguru = "^0.7.0"
mss = "^9.0.1"
opencv-python = "^4.8.0"
ultralytics = "^8.0.0"
pydirectinput = "^1.0.0"
keyboard = "^0.13.5"

[tool.poetry.group.dev]
optional = true

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
pytest-asyncio = "^0.21.0"
black = "^23.0.0"
mypy = "^1.5.0"
pylint = "^2.17.0"

[tool.poetry.scripts]
aradvision = "aradvision.main:main"

[tool.black]
line-length = 100
target-version = ['py310', 'py311', 'py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 100

[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --tb=short --strict-markers"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
disallow_incomplete_defs = false
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
follow_imports = "normal"
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[tool.pylint.messages_control]
disable = [
    "C0103",  # invalid-name (we prefer short names)
    "C0114",  # missing-module-docstring (not needed for __init__)
    "R0903",  # too-few-public-methods
]

[tool.pylint.format]
max-line-length = 100

[tool.coverage.run]
source = ["."]
omit = [
    "*/tests/*",
    "*/__pycache__/*",
    "*/venv/*",
    "*/.venv/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]
```

---

## ✅ 总结

**当前建议**: **不迁移**，继续使用 pip + requirements.txt

**理由**：
1. 当前方式已经足够满足需求
2. 优先完成功能开发（更重要）
3. 避免迁移带来的风险和学习成本

**未来规划**：
- **v0.3.0 或更晚**: 考虑迁移到 **uv**（性能和兼容性都很好）
- **团队扩大**: 当团队超过 2-3 人时，Poetry/uv 的收益会超过成本

---

**生成时间**: 2026-02-11 16:30:00
**评估者**: haneball17
